import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    hall_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("halls.id"))
    singer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("singer_profiles.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0)

    organizer: Mapped["User"] = relationship(foreign_keys=[organizer_id])
    hall: Mapped["Hall | None"] = relationship(back_populates="events")
    singer: Mapped["SingerProfile | None"] = relationship(back_populates="events")
