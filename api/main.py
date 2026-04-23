from fastapi import FastAPI, Depends
from schemas.auth.main import (
    RegisterStudent, StudentLogin, RoleCreate,
    FacultyCreate, ProgramCreate, RegisterUser,
    VerifyEmailCode, ResendVerificationCode, UpdateUser, ChangePassword
)
from services.auth.main import authServices

app = FastAPI()

@app.get("/", tags=["Root"])
def root():
    return "HOLA"

@app.post("/create_role", tags=["Roles"])
def create_role(data: RoleCreate, current_user=Depends(authServices().get_current_user)):
    return authServices().create_role(data)

@app.get("/roles", tags=["Roles"])
def get_all_roles(current_user=Depends(authServices().get_current_user)):
    return authServices().get_all_roles()

@app.post("/register", tags=["Auth"])
def register_student(data: RegisterStudent):
    return authServices().create_student(data)

@app.post("/register_user", tags=["Auth"])
def register_user(data: RegisterUser):
    return authServices().create_user(data)

@app.post("/verify-email",tags=["Auth"])
def verify_email(data: VerifyEmailCode):
    return authServices().verify_email(data)

@app.post("/resend-code", tags=["Auth"])
def resend_code(data: ResendVerificationCode):
    return authServices().resend_verification_code(data)

@app.post("/login", tags=["Auth"])
def login_user(data: StudentLogin):
    return authServices().login_user(data)

@app.post("/change-password", tags=["Auth"])
def change_password(data: ChangePassword):
    return authServices().change_password(data)

@app.get("/users", tags=["Users"])
def get_all_users():
    return authServices().getAllUsers()
@app.get("/delete-user/{id_usuario}", tags=["Users"])
def delete_user(id_usuario:int):
    return authServices().deleteUser(id_usuario)

@app.put("/users/{id_usuario}", tags=["Users"])
def update_user(id_usuario:int, data: UpdateUser):
    return authServices().update_user(id_usuario, data)

@app.post("/create_faculty", tags=["Faculties"])
def create_faculty(data: FacultyCreate, current_user=Depends(authServices().get_current_user)):
    return authServices().create_faculty(data)

@app.post("/create_program", tags=["Programs"])
def create_program(data: ProgramCreate, current_user=Depends(authServices().get_current_user)):
    return authServices().create_program(data)

@app.get("/faculties", tags=["Faculties"])
def get_all_faculties(current_user=Depends(authServices().get_current_user)):
    return authServices().get_all_faculties()

@app.get("/programs", tags=["Programs"])
def get_all_programs(current_user=Depends(authServices().get_current_user)):
    return authServices().get_all_programs()
