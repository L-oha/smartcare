from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: str = "patient"

class Provider(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    specialty: str
    bio: str = ""

class Slot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="provider.id")
    # Keep the existing timezone-naive SQLite format for stored slots.
    start_time: datetime = Field(sa_column=Column(DateTime(), nullable=False))
    is_booked: bool = False

class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    slot_id: int = Field(foreign_key="slot.id")
    reason: str = "General appointment"
    status: str = "confirmed"
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(), nullable=False),
    )
