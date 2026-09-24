# Plataforma de Gestión de Citas Médicas

Backend educativo construido con Python, FastAPI, Pydantic, SQLite, SQLModel, Alembic, JWT, CORS y middleware HTTP. Permite registrar pacientes y médicos, publicar disponibilidad, crear citas y controlar quién puede consultar o modificar cada recurso.

## 1. Estructura

```text
app/
  main.py                 # Crea FastAPI, registra routers y Swagger.
  database.py             # Conexión SQLite y sesiones.
  models.py               # Tablas SQLModel.
  schemas.py              # Validación de entrada y salida con Pydantic.
  auth.py                 # Hash de contraseñas y JWT.
  dependencies.py         # Usuario autenticado y permisos.
  middleware.py           # Request ID, tiempos, logging y headers de seguridad.
  routers/
    auth.py               # Registro, login y perfil.
    patients.py           # Perfil y citas del paciente.
    doctors.py            # Disponibilidad y agenda del médico.
    appointments.py       # Crear, consultar, confirmar y cancelar citas.
tests/                    # Pruebas automáticas con TestClient.
docs/                     # Material para explicar y sustentar.
alembic/                  # Entorno y versiones de migración.
alembic.ini               # Configuración de Alembic.
```

## 2. Instalación desde cero

En macOS o Linux:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

En Windows, la activación suele ser:

```powershell
.venv\Scripts\activate
```

Edita `.env` y cambia `SECRET_KEY` por una clave larga. Nunca publiques la clave real en Git.

`CORS_ORIGINS` define los frontends autorizados, separados por comas. Por defecto se permiten los frontends locales en los puertos `5173` y `3000`.

## 3. Ejecutar la API

```bash
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000`.

- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Alembic crea y actualiza el esquema de `citas.db`. La aplicación ya no ejecuta `SQLModel.metadata.create_all()` al iniciar.

## 4. Migraciones con Alembic

Desde la raíz del proyecto:

```bash
alembic history
alembic current
alembic upgrade head
```

Cuando cambien los modelos, genera una revisión y revísala antes de aplicarla:

```bash
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
```

La migración inicial `20260921_01_initial_schema` crea `user`, `availability` y `appointment`. Si ya tienes un `citas.db` creado por la versión anterior y esas tablas ya existen, registra la línea base una sola vez sin borrar datos:

```bash
alembic stamp 20260921_01
```

Después, las migraciones nuevas se aplican normalmente con `alembic upgrade head`.

## 5. CORS, middleware y autenticación

La aplicación configura `CORSMiddleware` usando `CORS_ORIGINS`. Las peticiones desde esos orígenes pueden usar credenciales y los métodos HTTP de la API.

El middleware HTTP agrega:

- `X-Request-ID` para rastrear una petición.
- `X-Process-Time` con el tiempo de respuesta.
- `X-Content-Type-Options`, `X-Frame-Options` y `Referrer-Policy`.
- Logging del método, ruta, estado y duración sin registrar tokens ni contraseñas.

La autenticación existente usa JWT. `POST /auth/register` registra usuarios, `POST /auth/login` entrega el token y los endpoints protegidos usan `Authorization: Bearer TOKEN`. `require_role("patient")` y `require_role("doctor")` aplican autorización por rol.

## 6. Ejemplos de solicitudes

### Registrar paciente

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Ana Pérez","email":"ana@example.com","phone":"+573001112233","password":"secreto123","role":"patient","document":"CC12345"}'
```

### Registrar médico

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Dr. López","email":"doctor@example.com","phone":"+573009998877","password":"secreto123","role":"doctor","specialty":"Medicina general","professional_license":"MED-12345"}'
```

### Login

El login usa formulario OAuth2: el campo `username` contiene el correo.

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=ana@example.com&password=secreto123"
```

Copia `access_token` y envíalo así:

```text
Authorization: Bearer TU_TOKEN
```

### Crear disponibilidad

Un médico usa el día de la semana de Python: lunes es `0` y domingo es `6`.

```bash
curl -X POST http://127.0.0.1:8000/doctors/me/availability \
  -H "Authorization: Bearer TOKEN_MEDICO" \
  -H "Content-Type: application/json" \
  -d '{"day_of_week":1,"start_time":"09:00:00","end_time":"17:00:00"}'
```

### Crear cita

La fecha debe coincidir con el día configurado y estar en el futuro.

```bash
curl -X POST http://127.0.0.1:8000/appointments \
  -H "Authorization: Bearer TOKEN_PACIENTE" \
  -H "Content-Type: application/json" \
  -d '{"doctor_id":2,"appointment_date":"2026-09-21","start_time":"10:00:00","end_time":"11:00:00","reason":"Consulta general"}'
```

## 7. Usuarios y roles

- `patient`: puede ver su perfil, sus citas y cancelar solamente sus citas.
- `doctor`: puede crear y editar su disponibilidad, ver su agenda y confirmar o cancelar sus citas.
- El endpoint `GET /appointments/me` devuelve las citas propias según el rol.

La contraseña nunca se guarda directamente. `pwdlib` crea un hash Argon2 y durante el login compara la contraseña recibida con ese hash.

## 8. Validaciones

Pydantic valida el formato de los datos antes de entrar al endpoint: correo con `EmailStr`, teléfono, longitud de contraseña, rol permitido, documento, fechas y horas. También valida que la fecha no sea pasada y que la hora inicial sea menor que la final.

La disponibilidad del médico y las citas repetidas no se pueden decidir mirando solamente el JSON. Esas reglas se validan consultando SQLite: se busca una disponibilidad que cubra el horario y una cita activa con el mismo médico, fecha y horas.

## 9. Códigos HTTP

- `201`: registro, disponibilidad o cita creados.
- `200`: consulta o modificación correcta.
- `400`: datos inválidos generales.
- `401`: token faltante, inválido o credenciales incorrectas.
- `403`: el usuario está autenticado, pero su rol o propiedad no permiten la acción.
- `404`: usuario, médico, disponibilidad o cita no encontrados.
- `409`: correo repetido o horario no disponible.
- `422`: Pydantic rechazó el formato o un campo requerido.

La eliminación de `DELETE /appointments/{appointment_id}` es lógica: no borra la fila, cambia `status` a `cancelled` para conservar el historial.

## 10. Pruebas

### Windows PowerShell

Desde la raíz del proyecto, si aún no existe `venv`, créalo una sola vez y actívalo:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python --version
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, permite scripts solo durante esa sesión y vuelve a activarlo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Ejecuta las pruebas y, al terminar, sal del entorno:

```powershell
python -m pytest -v
deactivate
```

Si `py` no se reconoce, abre una nueva ventana de PowerShell e inténtalo de nuevo. También puedes crear el entorno con `python -m venv venv`.

```bash
source .venv/bin/activate
python -m pytest -v
```

Resultado verificado en este proyecto: `14 passed`.

## 11. Archivos para la sustentación

- [docs/guion-sustentacion.md](docs/guion-sustentacion.md): explicación oral sugerida.
- [docs/casos-prueba.md](docs/casos-prueba.md): demostraciones positivas y negativas.

## 12. Cómo leer el código

1. `main.py` arma la aplicación y conecta routers.
2. Un router recibe la petición y usa una dependencia para obtener sesión y usuario.
3. `schemas.py` valida la forma del JSON.
4. El router consulta o modifica los modelos de `models.py` mediante SQLModel.
5. FastAPI convierte el resultado al esquema de salida y genera Swagger.

Esta secuencia es la idea central para explicar el proyecto: **petición -> validación -> permisos -> consulta a base de datos -> respuesta**.

# Proyecto Final FastAPI - Plataforma de Gestión de Citas Médicas

# Proyecto Final FastAPI - Plataforma de Gestión de Citas Médicas
## 1. Abrir el proyecto en otra pc
## 1. Preparar el proyecto

### Entrar a la carpeta

Abre PowerShell y entra a la carpeta del proyecto:

```powershell
cd "C:\Users\Administrator\Proyecto_Final_Fastapi"
```

Comprueba que estás en la ubicación correcta:

```powershell
Get-Location
```

Y verifica que existen los archivos principales:

```powershell
Test-Path .\requirements.txt
Test-Path .\alembic.ini
Test-Path .\app\main.py
```

Los tres deben mostrar:

```text
True
```

---

## 2. Activar el entorno virtual

Ejecuta:

```powershell
.\venv\Scripts\Activate.ps1
```

Si aparece:

```text
(venv)
```

el entorno está activo.

Comprueba Python:

```powershell
python --version
```

Si PowerShell no permite activar el entorno:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## 3. Instalar dependencias

Con `(venv)` activo:

```powershell
python -m pip install -r requirements.txt
```

Si es la primera vez que configuro el proyecto:

```powershell
python -m pip install --upgrade pip
```

---

# 4. Trabajar con Alembic

Antes de modificar la base de datos:

```powershell
python -m alembic current
```

Ver migraciones:

```powershell
python -m alembic history
```

Aplicar las migraciones existentes:

```powershell
python -m alembic upgrade head
```

Comprobar nuevamente:

```powershell
python -m alembic current
```

Debe aparecer la migración actual como:

```text
(head)
```

---

# 5. Cuando agregue un campo nuevo

Ejemplo: agregar `city` al usuario.

### Paso 1 — Modelo

En:

```text
app/models.py
```

agregar dentro de `User`:

```python
city: str | None = None
```

### Paso 2 — Schema

En:

```text
app/schemas.py
```

agregar `city` en `UserRegister` si quiero recibirlo:

```python
city: str | None = None
```

Y en `UserPublic` si quiero devolverlo:

```python
city: str | None = None
```

### Paso 3 — Crear migración

```powershell
python -m alembic revision --autogenerate -m "add city to users"
```

Después abrir:

```text
alembic/versions/
```

y revisar que la migración solamente agregue `city`.

### Paso 4 — Aplicar

```powershell
python -m alembic upgrade head
```

Comprobar:

```powershell
python -m alembic current
```

---

# 6. Guardar el nuevo dato

Si `city` se recibe durante el registro, abrir:

```text
app/routers/auth.py
```

Buscar:

```python
user = User(
```

y agregar:

```python
city = (data.city,)
```

No necesito crear otra migración por este cambio, porque la columna ya existe en la base de datos.

---

# 7. Ejecutar FastAPI

Desde la raíz del proyecto:

```powershell
python -m uvicorn app.main:app --reload
```

Debe aparecer algo parecido a:

```text
Uvicorn running on http://127.0.0.1:8000
```

Abrir Swagger:

```text
http://127.0.0.1:8000/docs
```

Para detener el servidor:

```text
Ctrl + C
```

---

# 8. Probar el registro en Swagger

Buscar:

```text
POST /auth/register
```

Ejemplo:

```json
{
  "name": "Carlos Demo",
  "email": "carlos2@example.com",
  "phone": "+573001234567",
  "password": "jose123",
  "role": "patient",
  "document": "CC765432",
  "specialty": null,
  "professional_license": null,
  "city": "Medellín"
}
```

Debe devolver:

```text
201 Created
```

Si el correo ya existe:

```text
409
```

Si la contraseña tiene menos de 6 caracteres:

```text
422
```

---

# 9. Autenticación

Para iniciar sesión:

```text
POST /auth/login
```

Aunque Swagger muestre:

```text
username
```

en este proyecto se debe colocar el **correo electrónico**.

El flujo es:

```text
correo + contraseña
        ↓
/auth/login
        ↓
JWT
        ↓
Authorize
        ↓
endpoints protegidos
```

---

# 10. Si Swagger muestra `500 Internal Server Error`

Primero mirar la terminal donde está corriendo Uvicorn.

No modificar código inmediatamente.

Si aparece:

```text
no such table: user
```

ejecutar:

```powershell
python -m alembic upgrade head
```

Después:

```powershell
python -m alembic current
```

No borrar `citas.db` sin revisar primero el problema.

---

# 11. Error que encontramos con la migración

Si aparece:

```text
NameError: name 'sqlmodel' is not defined
```

abrir la migración en:

```text
alembic/versions/
```

y comprobar que tenga:

```python
import sqlmodel
```

Después ejecutar nuevamente:

```powershell
python -m alembic upgrade head
```

---

# 12. Ejecutar pruebas

```powershell
python -m pytest -v
```

---

# 13. Comandos principales

```powershell
# Entrar al proyecto
cd "C:\Users\Administrator\Proyecto_Final_Fastapi"

# Activar entorno
.\venv\Scripts\Activate.ps1

# Estado de Alembic
python -m alembic current

# Historial
python -m alembic history

# Crear migración
python -m alembic revision --autogenerate -m "descripcion"

# Aplicar migración
python -m alembic upgrade head

# Comprobar migraciones pendientes
python -m alembic check

# Ejecutar pruebas
python -m pytest -v

# Iniciar FastAPI
python -m uvicorn app.main:app --reload
```

---

# 14. Regla para solucionar errores

Cuando aparezca un error:

```text
1. Leer el error completo.
2. Revisar la terminal.
3. Identificar el archivo donde ocurre.
4. Hacer un solo cambio.
5. Volver a ejecutar.
6. Comprobar el resultado.
```

No borrar la base de datos ni modificar varios archivos al mismo tiempo sin saber cuál es el problema.

---

# 15. Flujo general del proyecto

```text
Swagger
   ↓
Schemas
   ↓
Routers
   ↓
Models
   ↓
Alembic
   ↓
SQLite
```

**Schemas:** validan los datos.

**Routers:** reciben las solicitudes.

**Models:** representan las tablas.

**Alembic:** controla los cambios de la base de datos.

**SQLite:** almacena los datos.

**Swagger:** permite probar la API.

# 16. Flujo general del proyecto 
este comando es para  verificar que la columna existe en SQLite

@'
import sqlite3

with sqlite3.connect("file:citas.db?mode=ro", uri=True) as con:
    rows = con.execute("PRAGMA table_info(appointment)").fetchall()
    for row in rows:
        print(row)
'@ | python -