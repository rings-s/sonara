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
