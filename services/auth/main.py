import os
from datetime import datetime, timedelta, timezone
import bcrypt
from db.connection.main import Connection
from schemas.auth.main import RegisterStudent,RoleCreate,StudentLogin,FacultyCreate,ProgramCreate
from fastapi import HTTPException
from fastapi import Depends
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from psycopg.errors import UniqueViolation
import jwt

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 60))
security = HTTPBearer()


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

    def get_role_id(self,rol_name:str):
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

                id_rol = self.get_role_id("estudiante")
                cursor.execute("INSERT INTO users (name, last_name, email, password, fk_id_rol) VALUES (%s, %s, %s, %s, %s) RETURNING id_usuario", (data.name, data.last_name, data.email, hashed_password, id_rol))
                id_usuario = cursor.fetchone()[0]
                cursor.execute("INSERT INTO students (fk_id_usuario,codigo_institucional,facultad,programa,semestre,fecha_nacimiento,genero) VALUES (%s, %s, %s, %s, %s, %s, %s)", (id_usuario,data.student_code, data.faculty, data.program, data.semester, data.birth_date, data.gender))
                cursor.execute("INSERT INTO user_consents (fk_id_usuario,tipo_consentimiento,version_consentimiento,aceptado) VALUES (%s, %s, %s, %s)", (id_usuario, "informed_consent", data.consent_version, data.accepted_informed_consent))
                self.db.conn.commit()
                return {"message":"Estudiante creado exitosamente"}
        except HTTPException:
            self.db.conn.rollback()
            raise
        except UniqueViolation:
            self.db.conn.rollback()
            raise HTTPException(status_code=400, detail="El estudiante ya existe")
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error creando estudiante: {str(e)}")

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
                cursor.execute("SELECT * FROM users WHERE email = %s",(data.email,))
                user = cursor.fetchone()
                if not user:
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")
                if not self.verify_password(data.password, user[4].encode("utf-8")):
                    raise HTTPException(status_code=400, detail="Contraseña incorrecta")
                
                payload ={
                    "sub": str(user[0]),
                    "email": user[3],
                    "role": "estudiante",
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
