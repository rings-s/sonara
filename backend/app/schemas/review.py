import uuid
from pydantic import BaseModel, Field
from app.models.review import ReviewTargetType


class ReviewCreate(BaseModel):
    target_type: ReviewTargetType
    target_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    target_type: ReviewTargetType
    target_id: uuid.UUID
    rating: int
    comment: str | None
