# Checklist Implementacion JWT + PostgreSQL

## Estado Actual

- `api/main.py` esta vacio.
- No hay integracion de base de datos.
- No hay auth ni JWT implementado.
- `schemas/auth/auth.py` esta incompleto.
- Ya existe `schemas/phq9.py`, que despues podremos proteger con JWT.

## Nota Previa

- [ ] Ver un video corto de referencia sobre creacion de API con FastAPI antes de empezar la implementacion
- [x] Dejar primero la conexion a la base de datos funcionando antes de avanzar con JWT

## Checklist General

- [x] Definir la conexion a PostgreSQL
- [ ] Crear la capa de base de datos
- [ ] Crear el modelo `User`
- [ ] Crear los schemas de autenticacion
- [ ] Implementar hash de contrasena
- [ ] Implementar generacion y validacion de JWT
- [ ] Crear endpoints de auth
- [ ] Proteger endpoints privados con Bearer token
- [ ] Probar el flujo completo `register/login/me`
- [ ] Conectar luego el endpoint `/predict` con autenticacion

## Orden Recomendado

### 1. Configuracion de PostgreSQL

- [x] Definir `DATABASE_URL`
- [ ] Probar que la conexion a PostgreSQL funciona antes de crear auth

Ejemplo:

```text
postgresql://usuario:password@localhost:5432/modelo_probabilistico
```

### 2. Dependencias

- [ ] `fastapi`
- [ ] `uvicorn`
- [ ] `sqlalchemy`
- [ ] `psycopg` o `psycopg2-binary`
- [ ] `python-jose[cryptography]`
- [ ] `passlib[bcrypt]`
- [ ] `email-validator`

### 3. Capa de Base de Datos

- [ ] Crear `engine`
- [ ] Crear `SessionLocal`
- [ ] Crear `Base`
- [ ] Crear dependencia `get_db()`

### 4. Modelo de Usuario

- [ ] Crear tabla `users`
- [ ] Campos minimos:
- [ ] `id`
- [ ] `username` o `email`
- [ ] `hashed_password`
- [ ] `is_active`
- [ ] `created_at`
- [ ] Decidir si `email` sera el login principal
- [ ] Poner `unique` en `email`

### 5. Schemas de Auth

- [ ] `UserCreate`
- [ ] `UserLogin`
- [ ] `TokenResponse`
- [ ] `UserResponse`
- [ ] `MessageResponse`

### 6. Seguridad

- [ ] Funcion para hashear password
- [ ] Funcion para verificar password
- [ ] Funcion `create_access_token`
- [ ] Funcion `decode_access_token`

### 7. Endpoints Minimos

- [ ] `POST /auth/register`
- [ ] `POST /auth/login`
- [ ] `GET /auth/me`

### 8. Dependencia JWT

- [ ] Leer token desde `Authorization: Bearer ...`
- [ ] Decodificar JWT
- [ ] Obtener usuario actual desde BD
- [ ] Devolver `401` si el token no sirve

### 9. Pruebas Minimas

- [ ] Registrar usuario
- [ ] Hacer login
- [ ] Recibir `access_token`
- [ ] Consumir `/auth/me` con el token
- [ ] Confirmar que sin token falle

### 10. Integracion con la API Actual

- [ ] Crear `POST /predict`
- [ ] Recibir `PHQ9Request`
- [ ] Protegerlo con `get_current_user`
- [ ] Dejar el modelo accesible solo con login

## Decisiones Tecnicas Fijadas

- Login por `email`
- JWT con `HS256`
- Token de acceso simple, sin refresh token por ahora
- PostgreSQL + SQLAlchemy
- Password hash con `bcrypt`

## Estructura Sugerida

- `api/main.py`
- `db/session.py`
- `db/models.py`
- `schemas/auth.py`
- `services/security.py`

## MVP Real

- [ ] Conectar PostgreSQL
- [ ] Crear tabla `users`
- [ ] Implementar `register`
- [ ] Implementar `login`
- [ ] Implementar `me`
- [ ] Proteger `/predict`

## No Haria Todavia

- [ ] Roles
- [ ] Refresh tokens
- [ ] Recuperacion de contrasena
- [ ] Verificacion por correo
- [ ] Migraciones con Alembic

## Siguiente Paso Exacto

1. Definir `DATABASE_URL`
2. Crear la conexion SQLAlchemy a PostgreSQL
3. Crear el modelo `User`
4. Recien despues montar JWT
