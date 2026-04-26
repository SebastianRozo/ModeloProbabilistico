from fastapi import FastAPI, Depends, Query, Response
from services.auth.main import authServices
from services.model.main import modelServices
from schemas.auth.main import (
    RegisterStudent, StudentLogin, RoleCreate,
    FacultyCreate, ProgramCreate, RegisterUser,
    VerifyEmailCode, ResendVerificationCode, UpdateUser, ChangePassword
)
from schemas.phq9 import PHQ9Request

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

@app.get("/students", tags=["Students"])
def get_all_students(
    page:int = Query(1, ge=1),
    limit:int = Query(10, ge=1, le=100),
):
    return authServices().get_all_students(page, limit)

@app.get("/delete-student/{id_estudiante}", tags=["Students"])
def delete_student(id_estudiante:int):
    return authServices().delete_student(id_estudiante)

@app.get("/students/{id_estudiante}/evaluations", tags=["Students"])
def get_student_evaluations(
    id_estudiante:int,
    page:int = Query(1, ge=1),
    limit:int = Query(10, ge=1, le=100),
):
    return modelServices().get_student_evaluations(id_estudiante, page, limit)

@app.get("/dashboard/stats", tags=["Dashboard"])
def get_dashboard_stats(
    page:int = Query(1, ge=1),
    limit:int = Query(12, ge=1, le=60),
):
    return modelServices().get_dashboard_stats(page, limit)

@app.get("/evaluations", tags=["Reports"])
def get_evaluations(
    risk:str | None = Query(None),
    page:int = Query(1, ge=1),
    limit:int = Query(10, ge=1, le=100),
):
    return modelServices().get_evaluations_report(risk, page, limit)

@app.get("/reports/export", tags=["Reports"])
def export_report(
    risk:str | None = Query(None),
    page:int = Query(1, ge=1),
    limit:int = Query(100, ge=1, le=1000),
):
    pdf_content = modelServices().get_evaluations_report_pdf(risk, page, limit)
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_evaluaciones.pdf"},
    )

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


@app.post("/predict", tags=["Model"])
def predict(data: PHQ9Request, current_user=Depends(authServices().get_current_user)):
    return modelServices().predict_depression(data, current_user)
