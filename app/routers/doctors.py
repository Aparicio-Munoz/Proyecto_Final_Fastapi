from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import require_role
from app.models import Appointment, Availability, User
from app.schemas import AppointmentPublic, AvailabilityCreate

router = APIRouter(prefix="/doctors/me", tags=["Médicos", "Disponibilidad"])


@router.post("/availability", response_model=Availability, status_code=status.HTTP_201_CREATED)
def create_availability(
    data: AvailabilityCreate,
    current_user: User = Depends(require_role("doctor")),
    session: Session = Depends(get_session),
):
    availability = Availability(doctor_id=current_user.id, **data.model_dump())
    session.add(availability)
    session.commit()
    session.refresh(availability)
    return availability


@router.put("/availability/{availability_id}", response_model=Availability)
def update_availability(
    availability_id: int,
    data: AvailabilityCreate,
    current_user: User = Depends(require_role("doctor")),
    session: Session = Depends(get_session),
):
    availability = session.get(Availability, availability_id)
    if not availability or availability.doctor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
    for key, value in data.model_dump().items():
        setattr(availability, key, value)
    session.add(availability)
    session.commit()
    session.refresh(availability)
    return availability


@router.get("/availability", response_model=list[Availability])
def list_availability(
    current_user: User = Depends(require_role("doctor")),
    session: Session = Depends(get_session),
):
    return session.exec(select(Availability).where(Availability.doctor_id == current_user.id)).all()


@router.get("/appointments", response_model=list[AppointmentPublic])
def list_doctor_appointments(
    current_user: User = Depends(require_role("doctor")),
    session: Session = Depends(get_session),
):
    return session.exec(select(Appointment).where(Appointment.doctor_id == current_user.id)).all()
