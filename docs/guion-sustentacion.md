# Guion sencillo para la sustentación

## 1. Problema que resuelve

Una clínica necesita organizar pacientes, médicos, horarios y citas sin permitir cruces de horarios ni acceso a información de otra persona. Esta API centraliza esas operaciones y aplica reglas según el rol del usuario.

Frase útil: **el sistema convierte la gestión manual de citas en un flujo controlado, con autenticación y validaciones**.

## 2. Entidades

- **User**: representa a un paciente o médico. Tiene datos personales, rol y los datos especiales de su rol.
- **Availability**: representa un bloque de tiempo en el que un médico atiende. Guarda el día de la semana y las horas.
- **Appointment**: representa una cita. Relaciona un paciente con un médico, fecha, horario, motivo y estado.

Los campos `patient_id` y `doctor_id` de `Appointment` apuntan al `id` de `User`. No se crea otra tabla para pacientes o médicos porque ambos son usuarios con diferente rol.

## 3. Registro

El cliente envía JSON a `POST /auth/register`. Pydantic revisa el formato: correo, teléfono, contraseña y rol. Después aplica una regla condicional:

- Paciente: necesita `document`.
- Médico: necesita `specialty` y `professional_license`.

El endpoint consulta si el correo ya existe. Si existe, responde `409`. Si no, convierte la contraseña en un hash y guarda el usuario. La respuesta no devuelve `password_hash`.

## 4. Login y JWT

El usuario envía correo y contraseña a `POST /auth/login`. El sistema busca el correo y verifica la contraseña contra el hash. Si coincide, crea un JWT con el id del usuario y una fecha de vencimiento.

En los siguientes endpoints, el cliente envía `Authorization: Bearer TOKEN`. `get_current_user` decodifica el JWT, obtiene el id y busca al usuario en SQLite. Así cada endpoint conoce quién está haciendo la petición.

El JWT no reemplaza la base de datos: identifica al usuario, pero el sistema todavía consulta si ese usuario existe y cuál es su rol.

## 5. Roles y permisos

`require_role("patient")` permite solamente pacientes y `require_role("doctor")` permite solamente médicos. Si hay token pero el rol no corresponde, la respuesta es `403`.

Además del rol, se revisa la propiedad. Por ejemplo, un paciente autenticado no puede cancelar una cita cuyo `patient_id` pertenece a otra persona.

## 6. Validación de una cita

El flujo de `POST /appointments` es:

1. El paciente se identifica con el token.
2. Pydantic valida fecha, horas y motivo.
3. Se busca que el médico exista y tenga rol `doctor`.
4. Se calcula el día de la semana de la fecha.
5. Se consulta una disponibilidad del médico que cubra todo el horario.
6. Se consulta que no exista una cita activa para el mismo médico, fecha y horario.
7. Se guarda la cita con estado inicial `pending`.

Pydantic valida la forma y valores básicos del dato. La disponibilidad y las citas repetidas requieren consultar la base de datos, porque dependen de información que ya está guardada.

## 7. Diferencia entre errores

- **401 Unauthorized**: falta el token o el token no es válido. El sistema no puede identificar al usuario.
- **403 Forbidden**: el usuario sí está identificado, pero no tiene el rol o la propiedad necesaria.
- **404 Not Found**: el recurso solicitado no existe.
- **409 Conflict**: el recurso chocaría con el estado actual, por ejemplo un horario ocupado o un correo repetido.
- **422 Unprocessable Entity**: Pydantic rechazó el cuerpo por formato o campos inválidos.

## 8. Demostración con Swagger

1. Ejecutar `uvicorn app.main:app --reload`.
2. Abrir `http://127.0.0.1:8000/docs`.
3. Ejecutar `POST /auth/register` para crear un paciente y un médico.
4. Ejecutar los dos `POST /auth/login`. En login se usa el correo en `username`.
5. Pulsar **Authorize** y escribir `Bearer TOKEN_MEDICO` para probar disponibilidad.
6. Crear una disponibilidad para un día futuro.
7. Autorizarse con el token del paciente y crear una cita en ese día y horario.
8. Volver a autorizarse con el token médico y confirmar la cita.
9. Repetir la creación para mostrar `409 Horario no disponible`.
10. Probar una cita inexistente y observar `404 Cita no encontrada`.

## 9. Cómo explicar los archivos

- `main.py`: punto de entrada y unión de routers.
- `database.py`: motor SQLite, creación de tablas y sesiones.
- `models.py`: estructura que SQLModel convierte en tablas.
- `schemas.py`: contratos de entrada y salida; aquí vive Pydantic.
- `auth.py`: funciones pequeñas para hash y JWT.
- `dependencies.py`: lógica reutilizable para token, usuario y rol.
- `routers/auth.py`: registro y login.
- `routers/patients.py`: operaciones exclusivas del paciente.
- `routers/doctors.py`: disponibilidad y agenda médica.
- `routers/appointments.py`: reglas de creación y estados de las citas.
- `tests/`: pruebas que envían solicitudes como lo haría un cliente real.

## 10. Bloques importantes en palabras sencillas

`Depends(get_session)` le dice a FastAPI que entregue una sesión de base de datos al endpoint y la cierre al terminar.

`Field(..., primary_key=True)` identifica la columna que distingue cada fila.

`select(User).where(User.email == data.email)` construye una consulta para buscar un usuario por correo.

`session.add`, `session.commit` y `session.refresh` significan guardar el objeto, confirmar los cambios y recuperar los valores generados por la base de datos, como el id.

`HTTPException` detiene el endpoint y produce una respuesta HTTP controlada.

`model_validator` permite comparar varios campos al mismo tiempo, por ejemplo comprobar que la hora inicial sea menor que la final o que ciertos campos existan según el rol.

`status = "cancelled"` en vez de borrar la fila es una cancelación lógica: conserva el historial y permite auditar qué ocurrió.
