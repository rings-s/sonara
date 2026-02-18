import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=ReviewOut)
async def submit_review(
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    review = Review(reviewer_id=current_user.id, **payload.model_dump())
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.get("/{target_type}/{target_id}", response_model=list[ReviewOut])
async def get_reviews(target_type: str, target_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review).where(Review.target_type == target_type, Review.target_id == target_id)
    )
    return result.scalars().all()
