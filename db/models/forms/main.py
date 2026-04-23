from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
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


    