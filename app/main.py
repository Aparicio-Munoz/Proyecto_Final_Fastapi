import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.middleware import RequestMiddleware
from app.routers import appointments, auth, doctors, patients

load_dotenv()


def _cors_origins() -> list[str]:
    configured_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    )
    return [
        origin.strip() for origin in configured_origins.split(",") if origin.strip()
    ]


app = FastAPI(
    title="Plataforma de Gestión de Citas Médicas",
    description="API sencilla para registrar usuarios, disponibilidad y citas médicas.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestMiddleware)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(appointments.router)


@app.get("/", tags=["General"])
def root():
    return {"message": "API de citas médicas funcionando"}


# Agrega respuestas frecuentes para que Swagger documente los errores principales.
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    for path in schema["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict) and "responses" in operation:
                operation["responses"].setdefault(
                    "400", {"description": "Datos inválidos"}
                )
                operation["responses"].setdefault(
                    "401", {"description": "Token inválido o ausente"}
                )
                operation["responses"].setdefault(
                    "403", {"description": "Permisos insuficientes"}
                )
                operation["responses"].setdefault(
                    "404", {"description": "Recurso no encontrado"}
                )
                operation["responses"].setdefault(
                    "409", {"description": "Horario no disponible o correo repetido"}
                )
                operation["responses"].setdefault(
                    "422", {"description": "Error de validación de Pydantic"}
                )
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
