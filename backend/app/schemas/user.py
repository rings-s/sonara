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
