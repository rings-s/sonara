def test_teacher_tablenames():
    from app.models.teacher import TeacherProfile, TeacherInstrument
    assert TeacherProfile.__tablename__ == "teacher_profiles"
    assert TeacherInstrument.__tablename__ == "teacher_instruments"


def test_instrument_tablename():
    from app.models.instrument import Instrument
    assert Instrument.__tablename__ == "instruments"
