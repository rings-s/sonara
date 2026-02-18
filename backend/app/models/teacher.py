import uuid
from sqlalchemy import String, Float, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class TeacherProfile(Base, TimestampMixin):
    __tablename__ = "teacher_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    bio: Mapped[str | None] = mapped_column(String(2000))
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    hourly_rate: Mapped[float] = mapped_column(Float, nullable=False)
    travel_radius_km: Mapped[float] = mapped_column(Float, default=0.0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="teacher_profile")
    teacher_instruments: Mapped[list["TeacherInstrument"]] = relationship(back_populates="teacher", cascade="all, delete-orphan")
    teacher_balance: Mapped["TeacherBalance | None"] = relationship(back_populates="teacher", uselist=False)


class TeacherInstrument(Base):
    __tablename__ = "teacher_instruments"
    __table_args__ = (UniqueConstraint("teacher_id", "instrument_id"),)

    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teacher_profiles.id", ondelete="CASCADE"), primary_key=True)
    instrument_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), primary_key=True)
    level: Mapped[str | None] = mapped_column(String(50))  # beginner | intermediate | advanced

    teacher: Mapped["TeacherProfile"] = relationship(back_populates="teacher_instruments")
    instrument: Mapped["Instrument"] = relationship(back_populates="teacher_instruments")
