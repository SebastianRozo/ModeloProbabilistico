import bcrypt
from db.connection.main import Connection
from schemas.auth.main import RegisterStudent,RoleCreate,StudentLogin,FacultyCreate,ProgramCreate

class authServices:
    def __init__(self):
        self.db = Connection()
    def hash_password(self,password):
        return bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

    def verify_password(self,password,hashed_password):
        return bcrypt.checkpw(password.encode('utf-8'),hashed_password)
    def create_role(self,data:RoleCreate):
        with self.db.conn.cursor() as cursor:
            cursor.execute("INSERT INTO roles (nombre_rol,descripcion) values (%s , %s)",(data.name,data.description))
            self.db.conn.commit()
        return {"message":"Rol creado exitosamente"}

    def get_role_id(self,rol_name:str):
        with self.db.conn.cursor() as cursor:
            cursor.execute("SELECT id_rol FROM roles WHERE nombre_rol = %s",(rol_name,))
            return cursor.fetchone()[0]

    def create_student(self,data:RegisterStudent):
        hashed_password = self.hash_password(data.password).decode("utf-8")
        with self.db.conn.cursor() as cursor:
            #Verificar si el correo ya existe
            cursor.execute("SELECT id_usuario FROM users WHERE email = %s",(data.email,))
            exist_user= cursor.fetchone()

            if exist_user:
                raise ValueError("El correo ya esta registrado")
            
            #Verificar si el codigo institucional ya existe 
            cursor.execute("SELECT id_estudiante FROM students WHERE codigo_institucional = %s",(data.student_code,))
            exist_user = cursor.fetchone()

            if exist_user:
                raise ValueError("Ya hay un estudiante con ese codigo")
            
            #Crear usuario 
            id_rol = self.get_role_id("estudiante")
            cursor.execute("INSERT INTO users (name, last_name, email, password, fk_id_rol) VALUES (%s, %s, %s, %s, %s) RETURNING id_usuario", (data.name, data.last_name, data.email, hashed_password, id_rol))
            id_usuario = cursor.fetchone()[0]
            cursor.execute("INSERT INTO students (fk_id_usuario,codigo_institucional,facultad,programa,semestre,fecha_nacimiento,genero) VALUES (%s, %s, %s, %s, %s, %s, %s)", (id_usuario,data.student_code, data.faculty, data.program, data.semester, data.birth_date, data.gender))
            self.db.conn.commit()  
            return {"message":"Estudiante creado exitosamente"}
            
    def login_user(self, data:StudentLogin):
        with self.db.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s",(data.email,))
            user = cursor.fetchone()
            if not user:
                raise ValueError("Usuario no encontrado")
            if not self.verify_password(data.password,user[4]):
                raise ValueError("Contraseña incorrecta")
            return {"message":"Usuario logueado exitosamente"}

    def getAllUsers(self):
        with self.db.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            return cursor.fetchall()

    def create_faculty(self,data:FacultyCreate):
        with self.db.conn.cursor() as cursor:
            cursor.execute("INSERT INTO facultades (nombre_facultad) VALUES (%s)",(data.name,))
            self.db.conn.commit()
        return {"message":"Facultad creada exitosamente"}
    
    def create_program(self,data:ProgramCreate):
        with self.db.conn.cursor() as cursor:
            cursor.execute("INSERT INTO programs (nombre_programa,fk_id_facultad) VALUES (%s,%s)",(data.name,data.faculty_id))
            self.db.conn.commit()
        return {"message":"Programa creado exitosamente"}