# Casos de prueba

Cada caso se puede ejecutar desde Swagger o con las pruebas de `tests/`.

| # | Caso | Tipo | Resultado esperado |
|---|---|---|---|
| 1 | Registrar paciente con todos sus datos | Positivo | `201`, usuario con rol `patient` |
| 2 | Registrar médico con especialidad y licencia | Positivo | `201`, usuario con rol `doctor` |
| 3 | Registrar un correo repetido | Negativo | `409`, correo ya registrado |
| 4 | Registrar un correo con formato incorrecto | Negativo | `422`, error de `EmailStr` |
| 5 | Registrar paciente sin documento | Negativo | `422`, documento obligatorio |
| 6 | Registrar médico sin licencia | Negativo | `422`, licencia obligatoria |
| 7 | Login con contraseña correcta | Positivo | `200`, token JWT |
| 8 | Login con contraseña incorrecta | Negativo | `401`, credenciales incorrectas |
| 9 | Médico crea disponibilidad válida | Positivo | `201`, disponibilidad guardada |
| 10 | Paciente intenta crear disponibilidad | Negativo | `403`, permisos insuficientes |
| 11 | Crear cita dentro de la disponibilidad | Positivo | `201`, estado inicial `pending` |
| 12 | Crear cita con fecha pasada | Negativo | `422`, fecha no permitida |
| 13 | Crear una cita duplicada | Negativo | `409`, `Horario no disponible` |
| 14 | Paciente cancela cita propia | Positivo | `200`, estado `cancelled` |
| 15 | Paciente cancela cita ajena | Negativo | `403`, permisos insuficientes |
| 16 | Médico confirma una cita | Positivo | `200`, estado `confirmed` |
| 17 | Consultar una cita inexistente | Negativo | `404`, `Cita no encontrada` |
| 18 | Consultar endpoint protegido sin token | Negativo | `401`, token ausente |

## Orden recomendado para una demostración

1. Registrar médico y paciente.
2. Hacer login con cada usuario y conservar los tokens.
3. Crear disponibilidad con el token del médico.
4. Crear una cita futura con el token del paciente.
5. Confirmarla con el token del médico.
6. Intentar repetirla para mostrar el `409`.
7. Consultarla o cancelarla para mostrar los permisos.
