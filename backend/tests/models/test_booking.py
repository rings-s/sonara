def test_booking_status_values():
    from app.models.booking import BookingStatus, LessonType
    assert BookingStatus.pending == "pending"
    assert BookingStatus.confirmed == "confirmed"
    assert LessonType.home == "home"
    assert LessonType.online == "online"
