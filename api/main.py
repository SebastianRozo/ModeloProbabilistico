from fastapi import FastAPI
from schemas.auth.main import RegisterStudent,StudentLogin
from services.auth.main import authServices
app= FastAPI()

@app.get("/")
def root():
    return "HOLA PUTO"


@app.post("/register")
def register_student(data:RegisterStudent):
    return authServices().create_student(data)

@app.post("/login")
def login_user(data:StudentLogin):
    return authServices().login_user(data)

@app.get("/users")
def get_all_users():
    return authServices().getAllUsers()