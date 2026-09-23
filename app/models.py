from datetime import date, time
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True)
    phone: str
    password_hash: str
    role: str
    document: Optional[str] = None
    specialty: Optional[str] = None
    professional_license: Optional[str] = None


class Availability(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="user.id", index=True)
    day_of_week: int
    start_time: time
    end_time: time


class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="user.id", index=True)
    doctor_id: int = Field(foreign_key="user.id", index=True)
    appointment_date: date
    start_time: time
    end_time: time
    reason: str
    status: str = "pending"
