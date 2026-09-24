from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user, require_role
from app.models import Appointment, Availability, User
from app.schemas import AppointmentCreate, AppointmentPublic, AppointmentStatusUpdate

router = APIRouter(prefix="/appointments", tags=["Citas"])


def buscar_cita(session: Session, appointment_id: int) -> Appointment:
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return appointment


@router.post("", response_model=AppointmentPublic, status_code=status.HTTP_201_CREATED)
def create_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(require_role("patient")),
    session: Session = Depends(get_session),
):
    doctor = session.get(User, data.doctor_id)
    if not doctor or doctor.role != "doctor":
        raise HTTPException(status_code=404, detail="Médico no encontrado")

    weekday = data.appointment_date.weekday()
    availability = session.exec(
        select(Availability).where(
            Availability.doctor_id == data.doctor_id,
            Availability.day_of_week == weekday,
            Availability.start_time <= data.start_time,
            Availability.end_time >= data.end_time,
        )
    ).first()
    if not availability:
        raise HTTPException(status_code=409, detail="Horario no disponible")

    duplicate = session.exec(
        select(Appointment).where(
            Appointment.doctor_id == data.doctor_id,
            Appointment.appointment_date == data.appointment_date,
            Appointment.start_time == data.start_time,
            Appointment.end_time == data.end_time,
            Appointment.status != "cancelled",
        )
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Horario no disponible")

    appointment = Appointment(
        patient_id=current_user.id, status="pending", **data.model_dump()
    )
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return appointment


@router.get("/me", response_model=list[AppointmentPublic])
def get_my_appointments(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    query = select(Appointment)
    if current_user.role == "patient":
        query = query.where(Appointment.patient_id == current_user.id)
    else:
        query = query.where(Appointment.doctor_id == current_user.id)
    return session.exec(query).all()


@router.patch("/{appointment_id}/status", response_model=AppointmentPublic)
def update_appointment_status(
    appointment_id: int,
    data: AppointmentStatusUpdate,
    current_user: User = Depends(require_role("doctor")),
    session: Session = Depends(get_session),
):
    appointment = buscar_cita(session, appointment_id)
    if appointment.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    appointment.status = data.status
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return appointment


@router.delete("/{appointment_id}", response_model=AppointmentPublic)
def delete_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    appointment = buscar_cita(session, appointment_id)
    if current_user.id not in (appointment.patient_id, appointment.doctor_id):
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    appointment.status = "cancelled"
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return appointment
