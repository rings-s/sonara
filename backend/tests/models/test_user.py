def test_user_role_values():
    from app.models.user import UserRole
    assert UserRole.student == "student"
    assert UserRole.teacher == "teacher"
    assert UserRole.admin == "admin"


def test_user_tablename():
    from app.models.user import User
    assert User.__tablename__ == "users"
