from fastapi import FastAPI
from schemas.auth.main import RegisterStudent,StudentLogin,RoleCreate,FacultyCreate,ProgramCreate
from services.auth.main import authServices
app= FastAPI()

@app.get("/")
def root():
    return "HOLA PUTO"

@app.post("/create_role")
def create_role(data:RoleCreate):
    return authServices().create_role(data)

@app.post("/register")
def register_student(data:RegisterStudent):
    return authServices().create_student(data)

@app.post("/login")
def login_user(data:StudentLogin):
    return authServices().login_user(data)

@app.get("/users")
def get_all_users():
    return authServices().getAllUsers()

@app.post("/create_faculty")
def create_faculty(data:FacultyCreate):
    return authServices().create_faculty(data)

@app.post("/create_program")
def create_program(data:ProgramCreate):
    return authServices().create_program(data)