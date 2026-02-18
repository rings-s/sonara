import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.hall import Hall
from pydantic import BaseModel

router = APIRouter(prefix="/halls", tags=["halls"])


class HallCreate(BaseModel):
    name: str
    capacity: int
    latitude: float
    longitude: float
    price_per_hour: float


class HallOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    name: str
    capacity: int
    price_per_hour: float


@router.get("/", response_model=list[HallOut])
async def list_halls(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hall))
    return result.scalars().all()


@router.post("/", response_model=HallOut)
async def create_hall(
    payload: HallCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    hall = Hall(owner_id=current_user.id, **payload.model_dump())
    db.add(hall)
    await db.commit()
    await db.refresh(hall)
    return hall
