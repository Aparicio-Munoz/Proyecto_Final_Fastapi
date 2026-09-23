from datetime import date, timedelta

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


def register_and_login(client, data):
    client.post("/auth/register", json=data)
    response = client.post(
        "/auth/login",
        data={"username": data["email"], "password": data["password"]},
    )
    return response.json()["access_token"]


def setup_users(client):
    patient = {
        "name": "Ana Pérez", "email": "ana@example.com", "phone": "+573001112233",
        "password": "secreto123", "role": "patient", "document": "CC12345",
    }
    doctor = {
        "name": "Dr. López", "email": "doctor@example.com", "phone": "+573009998877",
        "password": "secreto123", "role": "doctor", "specialty": "Medicina general",
        "professional_license": "MED-12345",
    }
    patient_token = register_and_login(client, patient)
    doctor_token = register_and_login(client, doctor)
    doctor_id = client.get("/auth/me", headers={"Authorization": f"Bearer {doctor_token}"}).json()["id"]
    return patient_token, doctor_token, doctor_id


def future_date_with_weekday(weekday):
    current = date.today()
    days_ahead = (weekday - current.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return current + timedelta(days=days_ahead)


def create_availability(client, doctor_token, weekday=0):
    return client.post(
        "/doctors/me/availability",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={"day_of_week": weekday, "start_time": "09:00:00", "end_time": "17:00:00"},
    )


def appointment_data(doctor_id, weekday=0):
    return {
        "doctor_id": doctor_id,
        "appointment_date": future_date_with_weekday(weekday).isoformat(),
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "reason": "Consulta general",
    }


def test_creacion_de_disponibilidad_medica(client):
    patient_token, doctor_token, doctor_id = setup_users(client)
    response = create_availability(client, doctor_token)
    assert response.status_code == 201


def test_creacion_correcta_de_cita(client):
    patient_token, doctor_token, doctor_id = setup_users(client)
    create_availability(client, doctor_token)
    response = client.post(
        "/appointments", headers={"Authorization": f"Bearer {patient_token}"},
        json=appointment_data(doctor_id),
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_rechaza_cita_en_el_pasado(client):
    patient_token, doctor_token, doctor_id = setup_users(client)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    data = appointment_data(doctor_id)
    data["appointment_date"] = yesterday
    response = client.post(
        "/appointments", headers={"Authorization": f"Bearer {patient_token}"}, json=data,
    )
    assert response.status_code == 422


def test_rechaza_cita_duplicada(client):
    patient_token, doctor_token, doctor_id = setup_users(client)
    create_availability(client, doctor_token)
    data = appointment_data(doctor_id)
    headers = {"Authorization": f"Bearer {patient_token}"}
    assert client.post("/appointments", headers=headers, json=data).status_code == 201
    response = client.post("/appointments", headers=headers, json=data)
    assert response.status_code == 409
    assert response.json()["detail"] == "Horario no disponible"


def test_paciente_solo_cancela_sus_propias_citas(client):
    patient_token, doctor_token, doctor_id = setup_users(client)
    create_availability(client, doctor_token)
    appointment = client.post(
        "/appointments", headers={"Authorization": f"Bearer {patient_token}"},
        json=appointment_data(doctor_id),
    ).json()
    other_patient = {
        "name": "Luis Gómez", "email": "luis@example.com", "phone": "+573004445566",
        "password": "secreto123", "role": "patient", "document": "CC67890",
    }
    other_token = register_and_login(client, other_patient)
    response = client.patch(
        f"/patients/me/appointments/{appointment['id']}/cancel",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403


def test_medico_puede_confirmar_una_cita(client):
    patient_token, doctor_token, doctor_id = setup_users(client)
    create_availability(client, doctor_token)
    appointment = client.post(
        "/appointments", headers={"Authorization": f"Bearer {patient_token}"},
        json=appointment_data(doctor_id),
    ).json()
    response = client.patch(
        f"/appointments/{appointment['id']}/status",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={"status": "confirmed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_usuario_sin_permisos_recibe_403(client):
    patient_token, doctor_token, doctor_id = setup_users(client)
    response = client.post(
        "/doctors/me/availability",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"},
    )
    assert response.status_code == 403


def test_cita_inexistente_responde_404(client):
    patient_token, doctor_token, doctor_id = setup_users(client)
    response = client.delete(
        "/appointments/9999",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Cita no encontrada"
