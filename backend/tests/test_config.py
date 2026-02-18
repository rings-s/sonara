from app.core.config import settings


def test_settings_load():
    assert settings.DATABASE_URL.startswith("postgresql")
    assert len(settings.SECRET_KEY) >= 32
    assert settings.COMMISSION_RATE == 0.15
