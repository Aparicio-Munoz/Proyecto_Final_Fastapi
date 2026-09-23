from datetime import date, time
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserRegister(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=6)
    role: Literal["patient", "doctor"]
    document: Optional[str] = Field(default=None, min_length=5)
    specialty: Optional[str] = None
    professional_license: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validar_telefono(cls, value: str) -> str:
        digits = value.replace("+", "").replace(" ", "").replace("-", "")
        if not digits.isdigit() or len(digits) < 7:
            raise ValueError("El teléfono no tiene un formato válido")
        return value

    @model_validator(mode="after")
    def validar_datos_segun_rol(self):
        if self.role == "patient" and not self.document:
            raise ValueError("El documento es obligatorio para pacientes")
        if self.role == "doctor" and (not self.specialty or not self.professional_license):
            raise ValueError("La especialidad y la licencia son obligatorias para médicos")
        return self


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: str
    role: str
    document: Optional[str] = None
    specialty: Optional[str] = None
    professional_license: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AvailabilityCreate(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validar_horario(self):
        if self.start_time >= self.end_time:
            raise ValueError("La hora inicial debe ser menor que la hora final")
        return self


class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: date
    start_time: time
    end_time: time
    reason: str = Field(min_length=3)

    @model_validator(mode="after")
    def validar_horario(self):
        if self.start_time >= self.end_time:
            raise ValueError("La hora inicial debe ser menor que la hora final")
        if self.appointment_date < date.today():
            raise ValueError("La fecha no puede estar en el pasado")
        return self


class AppointmentStatusUpdate(BaseModel):
    status: Literal["confirmed", "cancelled"]


class AppointmentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    doctor_id: int
    appointment_date: date
    start_time: time
    end_time: time
    reason: str
    status: str
