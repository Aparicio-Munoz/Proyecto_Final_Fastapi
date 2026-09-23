from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
import pytest

from app.database import get_session
from app.main import app


@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def patient_data(email="ana@example.com"):
    return {
        "name": "Ana Pérez",
        "email": email,
        "phone": "+573001112233",
        "password": "secreto123",
        "role": "patient",
        "document": "CC12345",
    }


def doctor_data(email="doctor@example.com"):
    return {
        "name": "Dr. López",
        "email": email,
        "phone": "+573009998877",
        "password": "secreto123",
        "role": "doctor",
        "specialty": "Medicina general",
        "professional_license": "MED-12345",
    }


def test_registro_correcto_de_paciente(client):
    response = client.post("/auth/register", json=patient_data())
    assert response.status_code == 201
    assert response.json()["role"] == "patient"
    assert "password_hash" not in response.json()


def test_registro_correcto_de_medico(client):
    response = client.post("/auth/register", json=doctor_data())
    assert response.status_code == 201
    assert response.json()["specialty"] == "Medicina general"


def test_rechaza_correo_invalido(client):
    response = client.post("/auth/register", json=patient_data("correo-no-valido"))
    assert response.status_code == 422


def test_rechaza_datos_faltantes_segun_rol(client):
    data = patient_data()
    data.pop("document")
    assert client.post("/auth/register", json=data).status_code == 422

    data = doctor_data()
    data.pop("professional_license")
    assert client.post("/auth/register", json=data).status_code == 422


def test_login_correcto_y_jwt(client):
    client.post("/auth/register", json=patient_data())
    response = client.post(
        "/auth/login",
        data={"username": "ana@example.com", "password": "secreto123"},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_rechaza_credenciales_incorrectas(client):
    client.post("/auth/register", json=patient_data())
    response = client.post(
        "/auth/login",
        data={"username": "ana@example.com", "password": "incorrecta"},
    )
    assert response.status_code == 401
