from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AppointmentBase(BaseModel):
    appointment_date: datetime
    reason: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    status: Optional[str] = None
    reason: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: int
    student_id: int
    psychologist_id: Optional[int]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
