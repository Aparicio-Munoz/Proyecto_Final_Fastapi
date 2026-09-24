from datetime import date, time

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True)
    phone: str
    password_hash: str
    role: str
    city: str | None = None
    document: str | None = None
    specialty: str | None = None
    professional_license: str | None = None


class Availability(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="user.id", index=True)
    day_of_week: int
    start_time: time
    end_time: time



class Appointment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="user.id", index=True)
    doctor_id: int = Field(foreign_key="user.id", index=True)
    appointment_date: date
    start_time: time
    end_time: time
    reason: str
    status: str = "pending"
    notes: str | None = None
