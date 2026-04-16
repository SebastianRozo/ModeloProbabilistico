import bcrypt
from db.connection.main import Connection
from schemas.auth.main import RegisterStudent,RoleCreate,StudentLogin

class authServices:
    def __init__(self):
        self.db = Connection()
    def hash_password(self,password):
        return bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

    def verify_password(self,password,hashed_password):
        return bcrypt.checkpw(password.encode('utf-8'),hashed_password)
    def create_role(self,data:RoleCreate):
        with self.db.conn.cursor() as cursor:
            cursor.execute("INSERT INTO Role (nombre,description) values (%s , %s)",(data.name,data.description))
            self.db.conn.commit()

    def create_student(self,data:RegisterStudent):
        hashed_password = self.hash_password(data.password).decode("utf-8")
        with self.db.conn.cursor() as cursor:
            #Verificar si el correo ya existe
            cursor.execute("SELECT id_usuario FROM User WHERE email = %s",(data.email))
            exist_user= cursor.fetchone()

            if exist_user:
                raise ValueError("El correo ya esta registrado")
            
            #Verificar si el codigo institucional ya existe 
            cursor.execute("SELECT id_estudiante FROM Student WHERE codigo_institucional = %s",(data.student_code))
            exist_user = cursor.fetchone()

            if exist_user:
                raise ValueError("Ya hay un estudiante con ese codigo")
            
            #Crear usuario 
            cursor.execute("INSERT INTO User (name , last_name , email, password)", (data.name, data.last_name, data.email, hashed_password))
            
            cursor.execute("INSERT INTO Student (fk_id_usuario,codigo_institucional,facultad,programa,semestre,fecha_nacimiento,genero)", (data.student_code, data.faculty, data.program, data.semester, data.birth_date, data.gender))
            self.db.conn.commit()  

            return {"message":"Estudiante creado exitosamente"}
    def login_user(self, data:StudentLogin):
        with self.db.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM User WHERE email = %s",(data.email))
            user = cursor.fetchone()
            if not user:
                raise ValueError("Usuario no encontrado")
            if not self.verify_password(data.password,user[4]):
                raise ValueError("Contraseña incorrecta")
            return {"message":"Usuario logueado exitosamente"}

    def getAllUsers(self):
        with self.db.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM User")
            return cursor.fetchall()