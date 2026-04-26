import os
from datetime import datetime, timedelta, timezone
import bcrypt
from db.connection.main import Connection
from schemas.auth.main import RegisterStudent,RoleCreate,StudentLogin,FacultyCreate,ProgramCreate,RegisterUser,VerifyEmailCode,ResendVerificationCode,UpdateUser,ChangePassword
from fastapi import HTTPException
from fastapi import Depends
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from psycopg.errors import UniqueViolation
from services.auth.mail.main import send_verification_code
import jwt

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 60))
security = HTTPBearer()
DEFAULT_USER_ROLE = "usuario"


class authServices:
    def __init__(self):
        self.db = Connection()

    def _require_jwt_config(self):
        if not JWT_SECRET:
            raise HTTPException(status_code=500, detail="JWT_SECRET no esta configurado")

    def hash_password(self,password):
        return bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

    def verify_password(self,password,hashed_password):
        return bcrypt.checkpw(password.encode('utf-8'),hashed_password)

    def _create_verification_code(self, cursor, user_id: int, email: str):
        now = datetime.now(timezone.utc)
        cursor.execute(
            "UPDATE email_verification_codes SET usado_en = %s WHERE fk_id_usuario = %s AND usado_en IS NULL",
            (now, user_id),
        )
        verification_code = send_verification_code(email)
        verification_code_hash = self.hash_password(verification_code).decode("utf-8")
        expires_at = now + timedelta(minutes=10)
        cursor.execute(
            """
            INSERT INTO email_verification_codes (fk_id_usuario, codigo_hash, expira_en)
            VALUES (%s, %s, %s)
            """,
            (user_id, verification_code_hash, expires_at),
        )

    def create_role(self, data: RoleCreate):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO roles (nombre_rol, descripcion) VALUES (%s, %s)",
                    (data.name, data.description),
                )
                self.db.conn.commit()
            return {"message": "Rol creado exitosamente"}
        except UniqueViolation:
            self.db.conn.rollback()
            raise HTTPException(status_code=400, detail="El rol ya existe")
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error creando rol: {str(e)}")
    def get_all_roles(self):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM roles")
                roles= cursor.fetchall()
                return roles
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error obteniendo roles: {str(e)}")

    def get_role_id(self,rol_id:int):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT id_rol FROM roles WHERE id_rol = %s",(rol_id,))
                role = cursor.fetchone()
                if not role:
                    raise HTTPException(status_code=404, detail=f"No existe el rol '{rol_id}'")
                return role[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error obteniendo rol: {str(e)}")

    def get_role_id_by_name(self,rol_name:str):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT id_rol FROM roles WHERE nombre_rol = %s",(rol_name,))
                role = cursor.fetchone()
                if not role:
                    raise HTTPException(status_code=404, detail=f"No existe el rol '{rol_name}'")
                return role[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error obteniendo rol: {str(e)}")

    def create_student(self,data:RegisterStudent):
        hashed_password = self.hash_password(data.password).decode("utf-8")
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT id_usuario FROM users WHERE email = %s",(data.email,))
                exist_user= cursor.fetchone()

                if exist_user:
                    raise HTTPException(status_code=400, detail="El correo ya esta registrado")
                
                cursor.execute("SELECT id_estudiante FROM students WHERE codigo_institucional = %s",(data.student_code,))
                exist_user = cursor.fetchone()

                if exist_user:
                    raise HTTPException(status_code=400, detail="Ya hay un estudiante con ese codigo")

                id_rol = self.get_role_id_by_name("estudiante")
                cursor.execute("INSERT INTO users (name, last_name, email, password, fk_id_rol) VALUES (%s, %s, %s, %s, %s) RETURNING id_usuario", (data.name, data.last_name, data.email, hashed_password, id_rol))
                id_usuario = cursor.fetchone()[0]
                self._create_verification_code(cursor, id_usuario, data.email)
                cursor.execute("INSERT INTO students (fk_id_usuario,codigo_institucional,facultad,programa,semestre,fecha_nacimiento,genero) VALUES (%s, %s, %s, %s, %s, %s, %s)", (id_usuario,data.student_code, data.faculty, data.program, data.semester, data.birth_date, data.gender))
                cursor.execute("INSERT INTO user_consents (fk_id_usuario,tipo_consentimiento,version_consentimiento,aceptado) VALUES (%s, %s, %s, %s)", (id_usuario, "informed_consent", data.consent_version, data.accepted_informed_consent))
                self.db.conn.commit()
                return {"message":"Estudiante creado exitosamente, se ha enviado un codigo de verificacion a tu correo",
                "email": data.email,
                }
                
        except HTTPException:
            self.db.conn.rollback()
            raise
        except UniqueViolation:
            self.db.conn.rollback()
            raise HTTPException(status_code=400, detail="El estudiante ya existe")
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error creando estudiante: {str(e)}")
    
    def create_user(self, data:RegisterUser):
        try:
            hashed_password = self.hash_password(data.password).decode("utf-8")
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT id_usuario FROM users WHERE email = %s",(data.email,))
                exist_user= cursor.fetchone()
                if exist_user:
                    raise HTTPException(status_code=400, detail="El usuario ya existe")
                id_rol = self.get_role_id(data.role_id)
                cursor.execute("INSERT INTO users (name, last_name, email, password, fk_id_rol) VALUES (%s, %s, %s, %s, %s) RETURNING id_usuario", (data.name, data.last_name, data.email, hashed_password, id_rol))
                id_usuario = cursor.fetchone()[0]
                self._create_verification_code(cursor, id_usuario, data.email)
                self.db.conn.commit()
                return {"message":"Usuario creado exitosamente, se ha enviado un codigo de verificacion a tu correo",
                "email": data.email,
                }
        except HTTPException:
            self.db.conn.rollback()
            raise
        except UniqueViolation:
            self.db.conn.rollback()
            raise HTTPException(status_code=400, detail="El usuario ya existe")
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error creando usuario: {str(e)}")

    def decode_token(self,token:str):
        try:
            self._require_jwt_config()
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if not payload.get("sub"):
                raise HTTPException(status_code=401, detail="Token invalido")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token invalido")
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        token= credentials.credentials
        payload = self.decode_token(token)
        user_id = payload["sub"]
        with self.db.conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE id_usuario = %s",
                (user_id,)
            )
            user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no autorizado")
        return user
    
    def login_user(self, data:StudentLogin):
        try:
            self._require_jwt_config()
            with self.db.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT users.id_usuario, users.email, users.password, roles.nombre_rol, users.email_verified
                    FROM users
                    JOIN roles ON roles.id_rol = users.fk_id_rol
                    WHERE users.email = %s
                    """,
                    (data.email,),
                )
                user = cursor.fetchone()
                if not user:
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")
                if not self.verify_password(data.password, user[2].encode("utf-8")):
                    raise HTTPException(status_code=400, detail="Contraseña incorrecta")
                if not user[4]:
                    raise HTTPException(status_code=403, detail="Debes verificar tu correo antes de iniciar sesion")
                
                payload ={
                    "sub": str(user[0]),
                    "email": user[1],
                    "role": user[3],
                    "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                }
                token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
                return {
                    "mensaje":"Usuario logueado exitosamente",
                    "access_token": token,
                    "token_type": "bearer"
                }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error iniciando sesion: {str(e)}")

    def getAllUsers(self):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                return cursor.fetchall()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error obteniendo usuarios: {str(e)}")
    def deleteUser(self,id_usuario:int):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT id_usuario FROM users WHERE id_usuario = %s", (id_usuario,))
                user = cursor.fetchone()
                if not user:
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")

                cursor.execute("SELECT id_estudiante FROM students WHERE fk_id_usuario = %s", (id_usuario,))
                student = cursor.fetchone()
                if student:
                    cursor.execute("DELETE FROM phq9_responses WHERE student_id = %s", (student[0],))
                    cursor.execute("DELETE FROM students WHERE id_estudiante = %s", (student[0],))

                cursor.execute("DELETE FROM email_verification_codes WHERE fk_id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM user_consents WHERE fk_id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM users WHERE id_usuario = %s",(id_usuario,))
                self.db.conn.commit()
            return {"message":"Usuario eliminado exitosamente"}
        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error eliminando usuario: {str(e)}")

    def update_user(self, id_usuario:int, data:UpdateUser):
        try:
            update_data = data.model_dump(exclude_none=True)
            if not update_data:
                raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT id_usuario FROM users WHERE id_usuario = %s", (id_usuario,))
                user = cursor.fetchone()
                if not user:
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")

                if "email" in update_data:
                    cursor.execute(
                        "SELECT id_usuario FROM users WHERE email = %s AND id_usuario <> %s",
                        (update_data["email"], id_usuario),
                    )
                    if cursor.fetchone():
                        raise HTTPException(status_code=400, detail="El correo ya esta registrado")

                if "role_id" in update_data:
                    update_data["role_id"] = self.get_role_id(update_data["role_id"])

                field_map = {
                    "name": "name",
                    "last_name": "last_name",
                    "email": "email",
                    "role_id": "fk_id_rol",
                }
                assignments = []
                values = []
                for field, value in update_data.items():
                    assignments.append(f"{field_map[field]} = %s")
                    values.append(value)

                values.append(id_usuario)
                cursor.execute(
                    f"UPDATE users SET {', '.join(assignments)} WHERE id_usuario = %s",
                    tuple(values),
                )
                self.db.conn.commit()
            return {"message":"Usuario actualizado exitosamente"}
        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error actualizando usuario: {str(e)}")

    def change_password(self, data:ChangePassword, current_user):
        try:
            if data.current_password == data.new_password:
                raise HTTPException(status_code=400, detail="La nueva contraseña debe ser diferente a la actual")

            if not self.verify_password(data.current_password, current_user[4].encode("utf-8")):
                raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

            new_password_hash = self.hash_password(data.new_password).decode("utf-8")
            with self.db.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password = %s WHERE id_usuario = %s",
                    (new_password_hash, current_user[0]),
                )
                self.db.conn.commit()
            return {"message":"Contraseña actualizada exitosamente"}
        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error cambiando contraseña: {str(e)}")

    def create_faculty(self,data:FacultyCreate):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute("INSERT INTO facultades (nombre_facultad) VALUES (%s)",(data.name,))
                self.db.conn.commit()
            return {"message":"Facultad creada exitosamente"}
        except UniqueViolation:
            self.db.conn.rollback()
            raise HTTPException(status_code=400, detail="La facultad ya existe")
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error creando facultad: {str(e)}")
    
    def create_program(self,data:ProgramCreate):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute("INSERT INTO programs (nombre_programa,fk_id_facultad) VALUES (%s,%s)",(data.name,data.faculty_id))
                self.db.conn.commit()
            return {"message":"Programa creado exitosamente"}
        except UniqueViolation:
            self.db.conn.rollback()
            raise HTTPException(status_code=400, detail="El programa ya existe")
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error creando programa: {str(e)}")

    def get_all_faculties(self):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM facultades")
                return cursor.fetchall()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error obteniendo facultades: {str(e)}")
    
    def get_all_programs(self):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM programs")
                return cursor.fetchall()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error obteniendo programas: {str(e)}")

    def verify_email(self,data:VerifyEmailCode):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id_usuario, email_verified FROM users WHERE email = %s",
                    (data.email,),
                )
                user = cursor.fetchone()
                if not user:
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")
                if user[1]:
                    return {"message":"El email ya fue verificado"}

                cursor.execute(
                    """
                    SELECT id_codigo_verificacion, codigo_hash, expira_en
                    FROM email_verification_codes
                    WHERE fk_id_usuario = %s AND usado_en IS NULL
                    ORDER BY fecha_creacion DESC
                    LIMIT 1
                    """,
                    (user[0],),
                )
                verification_code = cursor.fetchone()
                if not verification_code:
                    raise HTTPException(status_code=404, detail="Codigo de verificacion no encontrado")
                if verification_code[2] < datetime.now(timezone.utc):
                    raise HTTPException(status_code=400, detail="Codigo de verificacion expirado")
                if not self.verify_password(data.verification_code, verification_code[1].encode("utf-8")):
                    raise HTTPException(status_code=400, detail="Codigo de verificacion incorrecto")
                cursor.execute(
                    "UPDATE users SET email_verified = %s, estado = %s WHERE id_usuario = %s",
                    (True, "activo", user[0]),
                )
                cursor.execute(
                    "UPDATE email_verification_codes SET usado_en = %s WHERE id_codigo_verificacion = %s",
                    (datetime.now(timezone.utc), verification_code[0]),
                )
                self.db.conn.commit()
            return {"message":"Email verificado exitosamente"}
        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error verificando email: {str(e)}")

    def resend_verification_code(self, data:ResendVerificationCode):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id_usuario, email_verified FROM users WHERE email = %s",
                    (data.email,),
                )
                user = cursor.fetchone()
                if not user:
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")
                if user[1]:
                    raise HTTPException(status_code=400, detail="El email ya fue verificado")

                self._create_verification_code(cursor, user[0], data.email)
                self.db.conn.commit()
            return {"message":"Se envio un nuevo codigo de verificacion", "email": data.email}
        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error reenviando codigo: {str(e)}")

    def get_total_pages(self, total:int, limit:int):
        if total == 0:
            return 0
        return (total + limit - 1) // limit

    def get_all_students(self, page:int = 1, limit:int = 10):
        try:
            offset = (page - 1) * limit
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM students")
                total = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT * FROM students ORDER BY id_estudiante ASC LIMIT %s OFFSET %s",
                    (limit, offset),
                )
                students = cursor.fetchall()
                return {
                    "items": students,
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total,
                        "total_pages": self.get_total_pages(total, limit),
                    },
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error obteniendo estudiantes: {str(e)}")

    def delete_student(self, id_estudiante: int):
        try:
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT id_estudiante FROM students WHERE id_estudiante = %s", (id_estudiante,))
                student = cursor.fetchone()
                if not student:
                    raise HTTPException(status_code=404, detail="Estudiante no encontrado")

                cursor.execute("DELETE FROM phq9_responses WHERE student_id = %s", (id_estudiante,))
                cursor.execute("DELETE FROM students WHERE id_estudiante = %s", (id_estudiante,))
                self.db.conn.commit()
            return {"message":"Estudiante eliminado exitosamente"}
        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error eliminando estudiante: {str(e)}")
