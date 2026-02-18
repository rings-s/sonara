import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.course import Course, Enrollment
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/courses", tags=["courses"])


class CourseCreate(BaseModel):
    title: str
    description: str | None = None
    price: float
    level: str = "beginner"
    start_date: datetime | None = None
    end_date: datetime | None = None


class CourseOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    title: str
    price: float
    level: str


@router.get("/", response_model=list[CourseOut])
async def list_courses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course))
    return result.scalars().all()


@router.post("/", response_model=CourseOut)
async def create_course(
    payload: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    course = Course(teacher_id=current_user.id, **payload.model_dump())
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.post("/{course_id}/enroll", response_model=dict)
async def enroll(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enrollment = Enrollment(course_id=course_id, student_id=current_user.id)
    db.add(enrollment)
    await db.commit()
    return {"status": "enrolled"}
