from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.event import Event
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/events", tags=["events"])


class EventCreate(BaseModel):
    hall_id: uuid.UUID | None = None
    singer_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    event_date: datetime
    price: float = 0.0


class EventOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    title: str
    event_date: datetime
    price: float


@router.get("/", response_model=list[EventOut])
async def list_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event))
    return result.scalars().all()


@router.post("/", response_model=EventOut)
async def create_event(
    payload: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    event = Event(organizer_id=current_user.id, **payload.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
