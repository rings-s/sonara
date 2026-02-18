from app.core.deps import require_role
from app.models.user import UserRole


def test_require_role_creates_callable():
    checker = require_role(UserRole.admin)
    assert callable(checker)
