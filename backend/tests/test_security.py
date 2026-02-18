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
