import uuid
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class SingerProfile(Base, TimestampMixin):
    __tablename__ = "singer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    genres: Mapped[str | None] = mapped_column(String(500))   # comma-separated or JSON string
    languages: Mapped[str | None] = mapped_column(String(500))
    price_range: Mapped[float | None] = mapped_column(Float)
    bio: Mapped[str | None] = mapped_column(String(2000))

    user: Mapped["User"] = relationship(back_populates="singer_profile")
    events: Mapped[list["Event"]] = relationship(back_populates="singer")
