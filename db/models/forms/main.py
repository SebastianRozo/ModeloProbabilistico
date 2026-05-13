from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from db.connection.main import Base

class PHQ9Response(Base):
    __tablename__ = "phq9_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id_estudiante"))

    q1: Mapped[int] = mapped_column(Integer, nullable=False)
    q2: Mapped[int] = mapped_column(Integer, nullable=False)
    q3: Mapped[int] = mapped_column(Integer, nullable=False)
    q4: Mapped[int] = mapped_column(Integer, nullable=False)
    q5: Mapped[int] = mapped_column(Integer, nullable=False)
    q6: Mapped[int] = mapped_column(Integer, nullable=False)
    q7: Mapped[int] = mapped_column(Integer, nullable=False)
    q8: Mapped[int] = mapped_column(Integer, nullable=False)
    q9: Mapped[int] = mapped_column(Integer, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class GAD7Response(Base):
    __tablename__ = "gad7_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id_estudiante"))

    q1: Mapped[int] = mapped_column(Integer, nullable=False)
    q2: Mapped[int] = mapped_column(Integer, nullable=False)
    q3: Mapped[int] = mapped_column(Integer, nullable=False)
    q4: Mapped[int] = mapped_column(Integer, nullable=False)
    q5: Mapped[int] = mapped_column(Integer, nullable=False)
    q6: Mapped[int] = mapped_column(Integer, nullable=False)
    q7: Mapped[int] = mapped_column(Integer, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id_estudiante"))
    psychologist_id: Mapped[int] = mapped_column(ForeignKey("users.id_usuario"), nullable=True)
    appointment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, default="pendiente", nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


    
