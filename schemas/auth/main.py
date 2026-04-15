from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    student_code: str = Field(min_length=3, max_length=30)
    birth_date: date
    gender: str = Field(min_length=1, max_length=30)
    faculty: str = Field(min_length=2, max_length=100)
    program: str = Field(min_length=2, max_length=100)
    semester: int = Field(ge=1, le=20)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    accepted_informed_consent: Literal[True]
    consent_version: str = Field(min_length=1, max_length=30, default="v1")
    

class StudentVerifyCode(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    verification_code: str = Field(min_length=4, max_length=12)


class StudentLogin(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class ConsentAccept(BaseModel):
    accepted_informed_consent: Literal[True]
    consent_version: str = Field(min_length=1, max_length=30)
