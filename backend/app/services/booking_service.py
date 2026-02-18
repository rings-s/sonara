from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.teacher import TeacherProfile
from app.models.booking import Booking
from app.schemas.booking import BookingCreate
from app.core.config import settings
import uuid


async def calculate_price(teacher_id: uuid.UUID, duration_minutes: int, db: AsyncSession) -> float:
    result = await db.execute(select(TeacherProfile).where(TeacherProfile.user_id == teacher_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        return 0.0
    return round(teacher.hourly_rate * (duration_minutes / 60), 2)


async def create_booking(student_id: uuid.UUID, payload: BookingCreate, db: AsyncSession) -> Booking:
    price = await calculate_price(payload.teacher_id, payload.duration_minutes, db)
    booking = Booking(
        student_id=student_id,
        price=price,
        **payload.model_dump(),
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking
