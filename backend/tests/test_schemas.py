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
