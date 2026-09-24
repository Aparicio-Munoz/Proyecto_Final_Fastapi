from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import require_role
from app.models import Appointment, User
from app.schemas import AppointmentPublic, UserPublic

router = APIRouter(prefix="/patients/me", tags=["Pacientes"])


@router.get("", response_model=UserPublic)
def get_patient_profile(current_user: User = Depends(require_role("patient"))):
    return current_user


@router.get("/appointments", response_model=list[AppointmentPublic])
def get_patient_appointments(
    current_user: User = Depends(require_role("patient")),
    session: Session = Depends(get_session),
):
    return session.exec(
        select(Appointment).where(Appointment.patient_id == current_user.id)
    ).all()


@router.patch("/appointments/{appointment_id}/cancel", response_model=AppointmentPublic)
def cancel_patient_appointment(
    appointment_id: int,
    current_user: User = Depends(require_role("patient")),
    session: Session = Depends(get_session),
):
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    appointment.status = "cancelled"
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return appointment
