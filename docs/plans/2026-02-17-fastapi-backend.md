# Sonara FastAPI Backend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a production-ready FastAPI backend for Sonara — a music education marketplace supporting Google OAuth, teachers, students, bookings, courses, halls, events, singers, wallets, and reviews.

**Architecture:** Layered FastAPI app using SQLAlchemy 2.0 ORM with async support, Alembic for migrations, and PostgreSQL. Auth is Google OAuth only — no passwords. A single `users` table holds all roles; separate profile tables extend per role.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL, Pydantic v2, python-jose (JWT), httpx (Google token verification), pytest + httpx (async tests), uv (package manager)

---

## Setup Checklist (Do Once Before Starting)

```bash
# In /home/ahmed/2026/sonara
uv init --no-workspace
uv add fastapi "uvicorn[standard]" sqlalchemy alembic asyncpg \
       pydantic pydantic-settings "python-jose[cryptography]" \
       httpx python-multipart pillow
uv add --dev pytest pytest-asyncio httpx coverage

# Create project layout
mkdir -p backend/{app/{api/v1/routes,core,models,schemas,services,utils},tests/{api,services,models}}
touch backend/app/__init__.py
touch backend/app/main.py
touch backend/app/core/{__init__.py,config.py,database.py,security.py,deps.py}
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/api/__init__.py backend/app/api/v1/__init__.py backend/app/api/v1/routes/__init__.py
touch backend/app/services/__init__.py
touch backend/app/utils/__init__.py
touch backend/tests/__init__.py backend/tests/api/__init__.py backend/tests/services/__init__.py
touch backend/tests/conftest.py
touch backend/.env.example
touch backend/alembic.ini
```

---

## Task 1: Project Config & Settings

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/.env.example`

**Step 1: Write `.env.example`**

```bash
# backend/.env.example
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/sonara
SECRET_KEY=change-me-in-production-min-32-chars
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
FRONTEND_URL=http://localhost:5173
ACCESS_TOKEN_EXPIRE_MINUTES=60
COMMISSION_RATE=0.15
```

Copy to `.env`: `cp backend/.env.example backend/.env`

**Step 2: Write `config.py`**

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="backend/.env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    FRONTEND_URL: str = "http://localhost:5173"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    COMMISSION_RATE: float = 0.15


settings = Settings()
```

**Step 3: Write the failing test**

```python
# backend/tests/test_config.py
from app.core.config import settings

def test_settings_load():
    assert settings.DATABASE_URL.startswith("postgresql")
    assert len(settings.SECRET_KEY) >= 32
    assert settings.COMMISSION_RATE == 0.15
```

**Step 4: Run test**

```bash
cd backend && uv run pytest tests/test_config.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/core/config.py backend/.env.example backend/tests/test_config.py
git commit -m "feat: project settings with pydantic-settings"
```

---

## Task 2: Database Engine & Base Model

**Files:**
- Create: `backend/app/core/database.py`
- Create: `backend/app/models/base.py`

**Step 1: Write `database.py`**

```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:  # FastAPI dependency
    async with AsyncSessionLocal() as session:
        yield session
```

**Step 2: Write `models/base.py`**

```python
# backend/app/models/base.py
import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

**Step 3: Write test**

```python
# backend/tests/models/test_base.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base

@pytest.mark.asyncio
async def test_engine_connects():
    from app.core.database import engine
    async with engine.begin() as conn:
        result = await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        assert result.scalar() == 1
```

**Step 4: Run test**

```bash
cd backend && uv run pytest tests/models/test_base.py -v
```

**Step 5: Commit**

```bash
git add backend/app/core/database.py backend/app/models/base.py backend/tests/models/test_base.py
git commit -m "feat: async sqlalchemy engine and declarative base"
```

---

## Task 3: User & Address Models

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/address.py`

**Step 1: Write `models/user.py`**

```python
# backend/app/models/user.py
import uuid
from enum import Enum as PyEnum
from sqlalchemy import String, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class UserRole(str, PyEnum):
    student = "student"
    teacher = "teacher"
    singer = "singer"
    hall_owner = "hall_owner"
    admin = "admin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    google_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.student, nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    addresses: Mapped[list["Address"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    teacher_profile: Mapped["TeacherProfile | None"] = relationship(back_populates="user", uselist=False)
    singer_profile: Mapped["SingerProfile | None"] = relationship(back_populates="user", uselist=False)
    wallet: Mapped["Wallet | None"] = relationship(back_populates="user", uselist=False)
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")
```

**Step 2: Write `models/address.py`**

```python
# backend/app/models/address.py
import uuid
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Address(Base, TimestampMixin):
    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    place_id: Mapped[str | None] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="addresses")
```

**Step 3: Write test**

```python
# backend/tests/models/test_user.py
def test_user_role_values():
    from app.models.user import UserRole
    assert UserRole.student == "student"
    assert UserRole.teacher == "teacher"
    assert UserRole.admin == "admin"

def test_user_tablename():
    from app.models.user import User
    assert User.__tablename__ == "users"
```

**Step 4: Run test**

```bash
cd backend && uv run pytest tests/models/test_user.py -v
```

**Step 5: Commit**

```bash
git add backend/app/models/user.py backend/app/models/address.py backend/tests/models/test_user.py
git commit -m "feat: User and Address models"
```

---

## Task 4: Teacher, Singer, Hall, Instrument Models

**Files:**
- Create: `backend/app/models/teacher.py`
- Create: `backend/app/models/singer.py`
- Create: `backend/app/models/instrument.py`
- Create: `backend/app/models/hall.py`

**Step 1: Write `models/instrument.py`**

```python
# backend/app/models/instrument.py
import uuid
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    teacher_instruments: Mapped[list["TeacherInstrument"]] = relationship(back_populates="instrument")
```

**Step 2: Write `models/teacher.py`**

```python
# backend/app/models/teacher.py
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
```

**Step 3: Write `models/singer.py`**

```python
# backend/app/models/singer.py
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
```

**Step 4: Write `models/hall.py`**

```python
# backend/app/models/hall.py
import uuid
from sqlalchemy import String, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Hall(Base, TimestampMixin):
    __tablename__ = "halls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_hour: Mapped[float] = mapped_column(Float, nullable=False)

    owner: Mapped["User"] = relationship()
    events: Mapped[list["Event"]] = relationship(back_populates="hall")
```

**Step 5: Write test**

```python
# backend/tests/models/test_teacher.py
def test_teacher_tablenames():
    from app.models.teacher import TeacherProfile, TeacherInstrument
    assert TeacherProfile.__tablename__ == "teacher_profiles"
    assert TeacherInstrument.__tablename__ == "teacher_instruments"

def test_instrument_tablename():
    from app.models.instrument import Instrument
    assert Instrument.__tablename__ == "instruments"
```

**Step 6: Run test**

```bash
cd backend && uv run pytest tests/models/test_teacher.py -v
```

**Step 7: Commit**

```bash
git add backend/app/models/teacher.py backend/app/models/singer.py \
        backend/app/models/instrument.py backend/app/models/hall.py \
        backend/tests/models/test_teacher.py
git commit -m "feat: Teacher, Singer, Hall, Instrument models"
```

---

## Task 5: Booking, Course, Enrollment, Event Models

**Files:**
- Create: `backend/app/models/booking.py`
- Create: `backend/app/models/course.py`
- Create: `backend/app/models/event.py`

**Step 1: Write `models/booking.py`**

```python
# backend/app/models/booking.py
import uuid
from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import String, Float, Integer, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class LessonType(str, PyEnum):
    home = "home"
    online = "online"
    studio = "studio"


class BookingStatus(str, PyEnum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    instrument_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False)
    address_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id"))
    lesson_type: Mapped[LessonType] = mapped_column(Enum(LessonType), nullable=False)
    lesson_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.pending)

    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    teacher: Mapped["User"] = relationship(foreign_keys=[teacher_id])
    instrument: Mapped["Instrument"] = relationship()
    address: Mapped["Address | None"] = relationship()
    payment: Mapped["BookingPayment | None"] = relationship(back_populates="booking", uselist=False)
```

**Step 2: Write `models/course.py`**

```python
# backend/app/models/course.py
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
```

**Step 3: Write `models/event.py`**

```python
# backend/app/models/event.py
import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    hall_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("halls.id"))
    singer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("singer_profiles.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0)

    organizer: Mapped["User"] = relationship(foreign_keys=[organizer_id])
    hall: Mapped["Hall | None"] = relationship(back_populates="events")
    singer: Mapped["SingerProfile | None"] = relationship(back_populates="events")
```

**Step 4: Write test**

```python
# backend/tests/models/test_booking.py
def test_booking_status_values():
    from app.models.booking import BookingStatus, LessonType
    assert BookingStatus.pending == "pending"
    assert BookingStatus.confirmed == "confirmed"
    assert LessonType.home == "home"
    assert LessonType.online == "online"
```

**Step 5: Run test**

```bash
cd backend && uv run pytest tests/models/test_booking.py -v
```

**Step 6: Commit**

```bash
git add backend/app/models/booking.py backend/app/models/course.py \
        backend/app/models/event.py backend/tests/models/test_booking.py
git commit -m "feat: Booking, Course, Enrollment, Event models"
```

---

## Task 6: Wallet, Transaction, Payment, Review Models

**Files:**
- Create: `backend/app/models/wallet.py`
- Create: `backend/app/models/review.py`

**Step 1: Write `models/wallet.py`**

```python
# backend/app/models/wallet.py
import uuid
from enum import Enum as PyEnum
from sqlalchemy import String, Float, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class TransactionType(str, PyEnum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    booking_payment = "booking_payment"
    booking_earning = "booking_earning"
    commission = "commission"
    refund = "refund"


class TransactionStatus(str, PyEnum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class PaymentMethod(str, PyEnum):
    wallet = "wallet"
    cash = "cash"
    bank_transfer = "bank_transfer"


class Wallet(Base, TimestampMixin):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    pending_balance: Mapped[float] = mapped_column(Float, default=0.0)

    user: Mapped["User"] = relationship(back_populates="wallet")


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus), default=TransactionStatus.pending)
    reference: Mapped[str | None] = mapped_column(String(255))
    proof_image: Mapped[str | None] = mapped_column(String(500))

    user: Mapped["User"] = relationship(back_populates="transactions")


class BookingPayment(Base, TimestampMixin):
    __tablename__ = "booking_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    commission_amount: Mapped[float] = mapped_column(Float, nullable=False)
    teacher_amount: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus), default=TransactionStatus.pending)

    booking: Mapped["Booking"] = relationship(back_populates="payment")
    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    teacher: Mapped["User"] = relationship(foreign_keys=[teacher_id])


class TeacherBalance(Base, TimestampMixin):
    __tablename__ = "teacher_balances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teacher_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_earnings: Mapped[float] = mapped_column(Float, default=0.0)
    commission_due: Mapped[float] = mapped_column(Float, default=0.0)
    commission_paid: Mapped[float] = mapped_column(Float, default=0.0)
    last_settlement: Mapped[str | None] = mapped_column(DateTime(timezone=True))

    teacher: Mapped["TeacherProfile"] = relationship(back_populates="teacher_balance")
```

**Step 2: Write `models/review.py`**

```python
# backend/app/models/review.py
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
```

**Step 3: Write test**

```python
# backend/tests/models/test_wallet.py
def test_wallet_defaults():
    from app.models.wallet import TransactionType, TransactionStatus
    assert TransactionType.deposit == "deposit"
    assert TransactionStatus.pending == "pending"

def test_review_target_types():
    from app.models.review import ReviewTargetType
    assert ReviewTargetType.teacher == "teacher"
    assert ReviewTargetType.hall == "hall"
```

**Step 4: Run test**

```bash
cd backend && uv run pytest tests/models/test_wallet.py -v
```

**Step 5: Update `models/__init__.py` to import all models**

```python
# backend/app/models/__init__.py
from app.models.base import Base
from app.models.user import User, UserRole
from app.models.address import Address
from app.models.instrument import Instrument
from app.models.teacher import TeacherProfile, TeacherInstrument
from app.models.singer import SingerProfile
from app.models.hall import Hall
from app.models.booking import Booking, LessonType, BookingStatus
from app.models.course import Course, Enrollment, CourseLevel
from app.models.event import Event
from app.models.wallet import Wallet, Transaction, BookingPayment, TeacherBalance
from app.models.review import Review, ReviewTargetType

__all__ = [
    "Base", "User", "UserRole", "Address", "Instrument",
    "TeacherProfile", "TeacherInstrument", "SingerProfile", "Hall",
    "Booking", "LessonType", "BookingStatus",
    "Course", "Enrollment", "CourseLevel",
    "Event", "Wallet", "Transaction", "BookingPayment", "TeacherBalance",
    "Review", "ReviewTargetType",
]
```

**Step 6: Commit**

```bash
git add backend/app/models/wallet.py backend/app/models/review.py \
        backend/app/models/__init__.py backend/tests/models/test_wallet.py
git commit -m "feat: Wallet, Transaction, BookingPayment, TeacherBalance, Review models"
```

---

## Task 7: Alembic Setup & Initial Migration

**Files:**
- Modify: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

**Step 1: Initialize Alembic**

```bash
cd backend && uv run alembic init alembic
```

**Step 2: Update `alembic/env.py`**

Replace the generated file with:

```python
# backend/alembic/env.py
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.core.config import settings
import app.models  # noqa: F401 — import all models so Alembic sees them

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.models.base import Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 3: Generate and apply migration**

```bash
cd backend && uv run alembic revision --autogenerate -m "initial schema"
uv run alembic upgrade head
```

Expected: all 16 tables created in PostgreSQL.

**Step 4: Verify**

```bash
psql -U postgres -d sonara -c "\dt"
```

Expected: list of 16 tables.

**Step 5: Commit**

```bash
git add backend/alembic/ backend/alembic.ini
git commit -m "feat: alembic setup and initial migration"
```

---

## Task 8: JWT Security & Google OAuth Verification

**Files:**
- Create: `backend/app/core/security.py`

**Step 1: Write `core/security.py`**

```python
# backend/app/core/security.py
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import httpx
from app.core.config import settings

ALGORITHM = "HS256"
GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Returns user_id string or None if invalid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


async def verify_google_token(id_token: str) -> dict | None:
    """
    Verify Google ID token and return user info dict, or None if invalid.
    Returns: {"sub": google_id, "email": ..., "name": ..., "picture": ...}
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_TOKEN_INFO_URL, params={"id_token": id_token})
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("aud") != settings.GOOGLE_CLIENT_ID:
            return None
        return data
```

**Step 2: Write test**

```python
# backend/tests/test_security.py
from app.core.security import create_access_token, decode_access_token

def test_create_and_decode_token():
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    token = create_access_token(user_id)
    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded == user_id

def test_invalid_token_returns_none():
    result = decode_access_token("totally.invalid.token")
    assert result is None
```

**Step 3: Run test**

```bash
cd backend && uv run pytest tests/test_security.py -v
```

**Step 4: Commit**

```bash
git add backend/app/core/security.py backend/tests/test_security.py
git commit -m "feat: JWT token creation/decoding and Google OAuth verification"
```

---

## Task 9: FastAPI Dependencies (Auth & DB)

**Files:**
- Create: `backend/app/core/deps.py`

**Step 1: Write `core/deps.py`**

```python
# backend/app/core/deps.py
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(*roles: UserRole):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return checker
```

**Step 2: Write test**

```python
# backend/tests/test_deps.py
from app.core.deps import require_role
from app.models.user import UserRole

def test_require_role_creates_callable():
    checker = require_role(UserRole.admin)
    assert callable(checker)
```

**Step 3: Run test**

```bash
cd backend && uv run pytest tests/test_deps.py -v
```

**Step 4: Commit**

```bash
git add backend/app/core/deps.py backend/tests/test_deps.py
git commit -m "feat: FastAPI auth dependencies with role enforcement"
```

---

## Task 10: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/schemas/teacher.py`
- Create: `backend/app/schemas/booking.py`
- Create: `backend/app/schemas/course.py`
- Create: `backend/app/schemas/event.py`
- Create: `backend/app/schemas/wallet.py`
- Create: `backend/app/schemas/review.py`

**Step 1: Write `schemas/user.py`**

```python
# backend/app/schemas/user.py
import uuid
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class GoogleAuthRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    email: EmailStr
    role: UserRole
    avatar: str | None
    phone: str | None


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    role: UserRole | None = None


class AddressCreate(BaseModel):
    latitude: float
    longitude: float
    description: str | None = None
    place_id: str | None = None


class AddressOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    latitude: float
    longitude: float
    description: str | None
    place_id: str | None
```

**Step 2: Write `schemas/teacher.py`**

```python
# backend/app/schemas/teacher.py
import uuid
from pydantic import BaseModel


class TeacherProfileCreate(BaseModel):
    bio: str | None = None
    experience_years: int = 0
    hourly_rate: float
    travel_radius_km: float = 0.0


class TeacherProfileOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    bio: str | None
    experience_years: int
    hourly_rate: float
    travel_radius_km: float
    verified: bool


class TeacherInstrumentAdd(BaseModel):
    instrument_id: uuid.UUID
    level: str | None = None
```

**Step 3: Write `schemas/booking.py`**

```python
# backend/app/schemas/booking.py
import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.booking import LessonType, BookingStatus


class BookingCreate(BaseModel):
    teacher_id: uuid.UUID
    instrument_id: uuid.UUID
    address_id: uuid.UUID | None = None
    lesson_type: LessonType
    lesson_date: datetime
    duration_minutes: int = 60


class BookingOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    teacher_id: uuid.UUID
    instrument_id: uuid.UUID
    lesson_type: LessonType
    lesson_date: datetime
    duration_minutes: int
    price: float
    status: BookingStatus
    created_at: datetime
```

**Step 4: Write `schemas/wallet.py`**

```python
# backend/app/schemas/wallet.py
import uuid
from pydantic import BaseModel
from app.models.wallet import TransactionType, TransactionStatus, PaymentMethod


class WalletOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    balance: float
    pending_balance: float


class DepositRequest(BaseModel):
    amount: float
    method: PaymentMethod
    reference: str | None = None


class TransactionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    amount: float
    type: TransactionType
    method: PaymentMethod
    status: TransactionStatus
    created_at: str
```

**Step 5: Write `schemas/review.py`**

```python
# backend/app/schemas/review.py
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
```

**Step 6: Write test**

```python
# backend/tests/test_schemas.py
from app.schemas.user import GoogleAuthRequest, UserOut
from app.schemas.booking import BookingCreate
from app.models.booking import LessonType
import uuid
from datetime import datetime

def test_google_auth_schema():
    req = GoogleAuthRequest(id_token="some_token")
    assert req.id_token == "some_token"

def test_booking_create_schema():
    b = BookingCreate(
        teacher_id=uuid.uuid4(),
        instrument_id=uuid.uuid4(),
        lesson_type=LessonType.online,
        lesson_date=datetime.now(),
    )
    assert b.duration_minutes == 60
```

**Step 7: Run test**

```bash
cd backend && uv run pytest tests/test_schemas.py -v
```

**Step 8: Commit**

```bash
git add backend/app/schemas/ backend/tests/test_schemas.py
git commit -m "feat: Pydantic v2 schemas for all entities"
```

---

## Task 11: Auth Route (Google OAuth → JWT)

**Files:**
- Create: `backend/app/api/v1/routes/auth.py`

**Step 1: Write `routes/auth.py`**

```python
# backend/app/api/v1/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_google_token, create_access_token
from app.models.user import User
from app.schemas.user import GoogleAuthRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse)
async def google_login(payload: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    user_info = await verify_google_token(payload.id_token)
    if not user_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    google_id = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name", email)
    avatar = user_info.get("picture")

    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        # Auto-create account on first login
        user = User(google_id=google_id, email=email, name=name, avatar=avatar)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=None)
async def me():
    """Placeholder — use /users/me instead."""
    return {"status": "ok"}
```

**Step 2: Write integration test**

```python
# backend/tests/api/test_auth.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app

@pytest.mark.asyncio
async def test_google_login_invalid_token():
    with patch("app.api.v1.routes.auth.verify_google_token", new_callable=AsyncMock, return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/google", json={"id_token": "bad_token"})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_google_login_creates_user(monkeypatch):
    import uuid
    fake_user_info = {
        "sub": "google123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": None,
    }
    with patch("app.api.v1.routes.auth.verify_google_token", new_callable=AsyncMock, return_value=fake_user_info):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/google", json={"id_token": "valid"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
```

**Step 3: Write `app/main.py`** (needed before tests)

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.routes import auth

app = FastAPI(title="Sonara API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
```

**Step 4: Write `tests/conftest.py`**

```python
# backend/tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
```

**Step 5: Add `aiosqlite` for tests**

```bash
cd backend && uv add --dev aiosqlite
```

**Step 6: Run test**

```bash
cd backend && uv run pytest tests/api/test_auth.py -v
```

**Step 7: Commit**

```bash
git add backend/app/main.py backend/app/api/v1/routes/auth.py \
        backend/tests/api/test_auth.py backend/tests/conftest.py
git commit -m "feat: Google OAuth login endpoint"
```

---

## Task 12: Users Routes (Profile, Addresses)

**Files:**
- Create: `backend/app/api/v1/routes/users.py`

**Step 1: Write `routes/users.py`**

```python
# backend/app/api/v1/routes/users.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.address import Address
from app.schemas.user import UserOut, UserUpdate, AddressCreate, AddressOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/me/addresses", response_model=AddressOut)
async def add_address(
    payload: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    address = Address(user_id=current_user.id, **payload.model_dump())
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address


@router.get("/me/addresses", response_model=list[AddressOut])
async def list_addresses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Address).where(Address.user_id == current_user.id))
    return result.scalars().all()
```

**Step 2: Write test**

```python
# backend/tests/api/test_users.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.user import User, UserRole
import uuid

def make_fake_user():
    return User(
        id=uuid.uuid4(),
        name="Test",
        email="t@t.com",
        google_id="g1",
        role=UserRole.student,
        is_active=True,
    )

@pytest.mark.asyncio
async def test_get_me_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 403  # no bearer header

@pytest.mark.asyncio
async def test_get_me_with_fake_user():
    fake_user = make_fake_user()
    with patch("app.core.deps.get_current_user", return_value=fake_user):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/users/me", headers={"Authorization": "Bearer fake"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "t@t.com"
```

**Step 3: Register routes in `main.py`**

Add to `backend/app/main.py`:
```python
from app.api.v1.routes import auth, users
app.include_router(users.router, prefix="/api/v1")
```

**Step 4: Run test**

```bash
cd backend && uv run pytest tests/api/test_users.py -v
```

**Step 5: Commit**

```bash
git add backend/app/api/v1/routes/users.py backend/tests/api/test_users.py backend/app/main.py
git commit -m "feat: user profile and address routes"
```

---

## Task 13: Teachers Routes

**Files:**
- Create: `backend/app/api/v1/routes/teachers.py`

**Step 1: Write `routes/teachers.py`**

```python
# backend/app/api/v1/routes/teachers.py
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
```

**Step 2: Write test**

```python
# backend/tests/api/test_teachers.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_list_teachers_public():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/teachers/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

**Step 3: Register route in `main.py`**

```python
from app.api.v1.routes import auth, users, teachers
app.include_router(teachers.router, prefix="/api/v1")
```

**Step 4: Run test**

```bash
cd backend && uv run pytest tests/api/test_teachers.py -v
```

**Step 5: Commit**

```bash
git add backend/app/api/v1/routes/teachers.py backend/tests/api/test_teachers.py backend/app/main.py
git commit -m "feat: teacher profile and instruments routes"
```

---

## Task 14: Bookings Routes

**Files:**
- Create: `backend/app/api/v1/routes/bookings.py`
- Create: `backend/app/services/booking_service.py`

**Step 1: Write `services/booking_service.py`**

```python
# backend/app/services/booking_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.teacher import TeacherProfile
from app.models.booking import Booking
from app.schemas.booking import BookingCreate
from app.core.config import settings
import uuid


async def calculate_price(teacher_id: uuid.UUID, duration_minutes: int, db: AsyncSession) -> float:
    result = await db.execute(select(TeacherProfile).where(TeacherProfile.user_id == teacher_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        return 0.0
    return round(teacher.hourly_rate * (duration_minutes / 60), 2)


async def create_booking(student_id: uuid.UUID, payload: BookingCreate, db: AsyncSession) -> Booking:
    price = await calculate_price(payload.teacher_id, payload.duration_minutes, db)
    booking = Booking(
        student_id=student_id,
        price=price,
        **payload.model_dump(),
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking
```

**Step 2: Write `routes/bookings.py`**

```python
# backend/app/api/v1/routes/bookings.py
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingOut
from app.services.booking_service import create_booking

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingOut)
async def book_lesson(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_booking(current_user.id, payload, db)


@router.get("/my", response_model=list[BookingOut])
async def my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Booking).where(Booking.student_id == current_user.id))
    return result.scalars().all()
```

**Step 3: Write test**

```python
# backend/tests/services/test_booking_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.booking_service import calculate_price
import uuid


@pytest.mark.asyncio
async def test_calculate_price_no_teacher():
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    price = await calculate_price(uuid.uuid4(), 60, db)
    assert price == 0.0
```

**Step 4: Run test**

```bash
cd backend && uv run pytest tests/services/test_booking_service.py -v
```

**Step 5: Register in `main.py`**

```python
from app.api.v1.routes import auth, users, teachers, bookings
app.include_router(bookings.router, prefix="/api/v1")
```

**Step 6: Commit**

```bash
git add backend/app/api/v1/routes/bookings.py backend/app/services/booking_service.py \
        backend/tests/services/test_booking_service.py backend/app/main.py
git commit -m "feat: booking creation and listing routes with price calculation"
```

---

## Task 15: Wallet Routes

**Files:**
- Create: `backend/app/api/v1/routes/wallet.py`

**Step 1: Write `routes/wallet.py`**

```python
# backend/app/api/v1/routes/wallet.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.wallet import Wallet, Transaction, TransactionType, TransactionStatus
from app.schemas.wallet import WalletOut, DepositRequest, TransactionOut

router = APIRouter(prefix="/wallet", tags=["wallet"])


async def get_or_create_wallet(user: User, db: AsyncSession) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        wallet = Wallet(user_id=user.id)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    return wallet


@router.get("/", response_model=WalletOut)
async def get_wallet(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_or_create_wallet(current_user, db)


@router.post("/deposit", response_model=TransactionOut)
async def deposit(
    payload: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    wallet = await get_or_create_wallet(current_user, db)
    tx = Transaction(
        user_id=current_user.id,
        amount=payload.amount,
        type=TransactionType.deposit,
        method=payload.method,
        status=TransactionStatus.pending,
        reference=payload.reference,
    )
    db.add(tx)
    # Wallet balance updated after admin approval in production
    await db.commit()
    await db.refresh(tx)
    return tx
```

**Step 2: Write test**

```python
# backend/tests/api/test_wallet.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_wallet_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/wallet/")
    assert resp.status_code == 403
```

**Step 3: Register in `main.py`**

```python
from app.api.v1.routes import auth, users, teachers, bookings, wallet
app.include_router(wallet.router, prefix="/api/v1")
```

**Step 4: Run test**

```bash
cd backend && uv run pytest tests/api/test_wallet.py -v
```

**Step 5: Commit**

```bash
git add backend/app/api/v1/routes/wallet.py backend/tests/api/test_wallet.py backend/app/main.py
git commit -m "feat: wallet balance and deposit request routes"
```

---

## Task 16: Events, Reviews, Courses, Halls Routes

**Files:**
- Create: `backend/app/api/v1/routes/events.py`
- Create: `backend/app/api/v1/routes/reviews.py`
- Create: `backend/app/api/v1/routes/courses.py`
- Create: `backend/app/api/v1/routes/halls.py`

**Step 1: Write `routes/events.py`**

```python
# backend/app/api/v1/routes/events.py
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
```

**Step 2: Write `routes/reviews.py`**

```python
# backend/app/api/v1/routes/reviews.py
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
```

**Step 3: Write `routes/halls.py`**

```python
# backend/app/api/v1/routes/halls.py
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
```

**Step 4: Write `routes/courses.py`**

```python
# backend/app/api/v1/routes/courses.py
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
```

**Step 5: Register all in `main.py`**

```python
from app.api.v1.routes import auth, users, teachers, bookings, wallet, events, reviews, halls, courses
app.include_router(events.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(halls.router, prefix="/api/v1")
app.include_router(courses.router, prefix="/api/v1")
```

**Step 6: Write test**

```python
# backend/tests/api/test_events.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_list_events_public():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/events/")
    assert resp.status_code == 200
```

**Step 7: Run tests**

```bash
cd backend && uv run pytest tests/api/test_events.py -v
```

**Step 8: Commit**

```bash
git add backend/app/api/v1/routes/events.py backend/app/api/v1/routes/reviews.py \
        backend/app/api/v1/routes/halls.py backend/app/api/v1/routes/courses.py \
        backend/tests/api/test_events.py backend/app/main.py
git commit -m "feat: events, reviews, halls, courses routes"
```

---

## Task 17: Run Full Test Suite & Verify

**Step 1: Run all tests**

```bash
cd backend && uv run pytest tests/ -v --tb=short
```

Expected: All tests pass.

**Step 2: Start the server and check Swagger**

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

Open: `http://localhost:8000/docs`

Expected: 16+ endpoints listed across all route groups.

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete FastAPI backend - all models, routes, auth, wallet"
```

---

## Summary

| Layer | Count |
|-------|-------|
| Models | 16 tables |
| Routes | 9 router groups, 25+ endpoints |
| Schemas | 10+ Pydantic models |
| Services | booking price calculation |
| Tests | 15+ tests |

**Next:** SvelteKit frontend connecting to this API.
