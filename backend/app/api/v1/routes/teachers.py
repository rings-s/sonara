import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.teacher import TeacherProfile, TeacherInstrument
from app.schemas.teacher import TeacherProfileCreate, TeacherProfileOut, TeacherInstrumentAdd

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.post("/profile", response_model=TeacherProfileOut)
async def create_teacher_profile(
    payload: TeacherProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(TeacherProfile).where(TeacherProfile.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Profile already exists")
    profile = TeacherProfile(user_id=current_user.id, **payload.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/", response_model=list[TeacherProfileOut])
async def list_teachers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TeacherProfile).where(TeacherProfile.verified == True))
    return result.scalars().all()


@router.post("/profile/instruments", response_model=dict)
async def add_instrument(
    payload: TeacherInstrumentAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TeacherProfile).where(TeacherProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Teacher profile not found")
    ti = TeacherInstrument(teacher_id=profile.id, instrument_id=payload.instrument_id, level=payload.level)
    db.add(ti)
    await db.commit()
    return {"status": "added"}
