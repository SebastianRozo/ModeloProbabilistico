from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.connection.main import Base


class Role(Base):
    __tablename__ = "roles"

    id_rol = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String, unique=True, nullable=False)
    descripcion = Column(String)

    usuarios = relationship("User", back_populates="rol")


class User(Base):
    __tablename__ = "users"

    id_usuario = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    estado = Column(String, nullable=False, default="pendiente_verificacion")
    email_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_access = Column(DateTime(timezone=True), nullable=True)

    fk_id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)

    rol = relationship("Role", back_populates="usuarios")
    estudiante = relationship("Student", back_populates="usuario", uselist=False)
    codigos_verificacion = relationship(
        "EmailVerificationCode",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    consentimientos = relationship(
        "UserConsent",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )


class Student(Base):
    __tablename__ = "students"

    id_estudiante = Column(Integer, primary_key=True, index=True)
    fk_id_usuario = Column(Integer, ForeignKey("users.id_usuario"), unique=True, nullable=False)
    codigo_institucional = Column(String, unique=True, nullable=False)
    facultad = Column(Integer, ForeignKey("facultades.id_facultad"), nullable=False)
    programa = Column(Integer, ForeignKey("programs.id_programa"), nullable=False)
    semestre = Column(Integer, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(String, nullable=False)

    usuario = relationship("User", back_populates="estudiante")
    facultad = relationship("facultad", back_populates="estudiantes")
    programa = relationship("program", back_populates="estudiantes")


class EmailVerificationCode(Base):
    __tablename__ = "email_verification_codes"

    id_codigo_verificacion = Column(Integer, primary_key=True, index=True)
    fk_id_usuario = Column(Integer, ForeignKey("users.id_usuario"), nullable=False, index=True)
    codigo_hash = Column(String, nullable=False)
    expira_en = Column(DateTime(timezone=True), nullable=False)
    usado_en = Column(DateTime(timezone=True), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("User", back_populates="codigos_verificacion")


class UserConsent(Base):
    __tablename__ = "user_consents"

    id_consentimiento = Column(Integer, primary_key=True, index=True)
    fk_id_usuario = Column(Integer, ForeignKey("users.id_usuario"), nullable=False, index=True)
    tipo_consentimiento = Column(String, nullable=False, default="informed_consent")
    version_consentimiento = Column(String, nullable=False)
    aceptado = Column(Boolean, nullable=False, default=True)
    aceptado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    texto_consentimiento = Column(Text, nullable=True)

    usuario = relationship("User", back_populates="consentimientos")

class program(Base):
    __tablename__ = "programs"
    id_programa = Column(Integer, primary_key=True, index=True)
    nombre_programa = Column(String, nullable=False)
    fk_id_facultad = Column(Integer, ForeignKey("facultades.id_facultad"), nullable=False)
    
class facultad(Base):
    __tablename__ = "facultades"
    id_facultad = Column(Integer, primary_key=True, index=True)
    nombre_facultad = Column(String, nullable=False)