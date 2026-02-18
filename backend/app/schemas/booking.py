import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.booking import LessonType, BookingStatus


class BookingCreate(BaseModel):
    teacher_id: uuid.UUID
    instrument_id: uuid.UUID
    address_id: uuid.UUID | None = None
    lesson_type: LessonType
    lesson_date: datetime
    duration_minutes: int = 60


class BookingOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    teacher_id: uuid.UUID
    instrument_id: uuid.UUID
    lesson_type: LessonType
    lesson_date: datetime
    duration_minutes: int
    price: float
    status: BookingStatus
    created_at: datetime
