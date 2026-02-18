from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    FRONTEND_URL: str = "http://localhost:5173"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    COMMISSION_RATE: float = 0.15


settings = Settings()
