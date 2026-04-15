import bcrypt
from db.connection.main import Connection
import bcrypt
from schemas.auth.main import UserCreate

class authServices:
    def __init__(self):
        self.db = Connection()
    def hash_password(self,password):
        return bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

    def verify_password(self,password,hashed_password):
        return bcrypt.checkpw(password.encode('utf-8'),hashed_password)

    def create_user(self,data:UserCreate):
        hashed_password = self.hash_password(data.password).decode("utf-8")
        with self.db.conn.cursor() as cursor:
            #Verificar si el correo ya existe
            cursor.execute("SELECT id_usuario FROM users WHERE correo = %s",(data.email))
            exist_user= cursor.fetchone()

            if exist_user:
                raise ValueError("El correo ya esta registrado")
            
            #Verificar si el codigo institucional ya existe 
            cursor.execute("SELECT id_usuario FROM users WHERE codigo_institucional = %s",(data.student_code))
            exist_user = cursor.fetchone()

            if exist_user:
                raise ValueError("Ya hay un estudiante con ese codigo")

        