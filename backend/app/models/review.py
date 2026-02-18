import uuid
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class ReviewTargetType(str, PyEnum):
    teacher = "teacher"
    singer = "singer"
    hall = "hall"
    course = "course"


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type: Mapped[ReviewTargetType] = mapped_column(Enum(ReviewTargetType), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)   # 1-5
    comment: Mapped[str | None] = mapped_column(String(1000))

    reviewer: Mapped["User"] = relationship()
