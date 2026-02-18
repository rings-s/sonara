import uuid
from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import String, Float, Integer, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class LessonType(str, PyEnum):
    home = "home"
    online = "online"
    studio = "studio"


class BookingStatus(str, PyEnum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    instrument_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False)
    address_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id"))
    lesson_type: Mapped[LessonType] = mapped_column(Enum(LessonType), nullable=False)
    lesson_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.pending)

    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    teacher: Mapped["User"] = relationship(foreign_keys=[teacher_id])
    instrument: Mapped["Instrument"] = relationship()
    address: Mapped["Address | None"] = relationship()
    payment: Mapped["BookingPayment | None"] = relationship(back_populates="booking", uselist=False)
