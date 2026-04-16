from fastapi import FastAPI
from schemas.auth.main import RegisterStudent,StudentLogin,RoleCreate,FacultyCreate,ProgramCreate
from services.auth.main import authServices
from fastapi import Depends
app= FastAPI()

@app.get("/")
def root():
    return "HOLA PUTO"

@app.post("/create_role")
def create_role(data:RoleCreate,current_user = Depends(authServices().get_current_user)):
    return authServices().create_role(data)

@app.get("/roles")
def get_all_roles(current_user = Depends(authServices().get_current_user)):
    return authServices().get_all_roles()

@app.post("/register")
def register_student(data:RegisterStudent):
    return authServices().create_student(data)

@app.post("/login")
def login_user(data:StudentLogin):
    return authServices().login_user(data)

@app.get("/users")
def get_all_users(current_user = Depends(authServices().get_current_user)):
    return authServices().getAllUsers()

@app.post("/create_faculty")
def create_faculty(data:FacultyCreate,current_user = Depends(authServices().get_current_user)):
    return authServices().create_faculty(data)

@app.post("/create_program")
def create_program(data:ProgramCreate,current_user = Depends(authServices().get_current_user)):
    return authServices().create_program(data)
