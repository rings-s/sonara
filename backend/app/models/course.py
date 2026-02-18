import uuid
from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import String, Float, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class CourseLevel(str, PyEnum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class EnrollmentStatus(str, PyEnum):
    active = "active"
    completed = "completed"
    dropped = "dropped"


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))
    price: Mapped[float] = mapped_column(Float, nullable=False)
    level: Mapped[CourseLevel] = mapped_column(Enum(CourseLevel), default=CourseLevel.beginner)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    teacher: Mapped["User"] = relationship()
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course", cascade="all, delete-orphan")


class Enrollment(Base, TimestampMixin):
    __tablename__ = "enrollments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[EnrollmentStatus] = mapped_column(Enum(EnrollmentStatus), default=EnrollmentStatus.active)

    course: Mapped["Course"] = relationship(back_populates="enrollments")
    student: Mapped["User"] = relationship()
