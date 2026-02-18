from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_google_token, create_access_token
from app.models.user import User
from app.schemas.user import GoogleAuthRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse)
async def google_login(payload: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    user_info = await verify_google_token(payload.id_token)
    if not user_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    google_id = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name", email)
    avatar = user_info.get("picture")

    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        # Auto-create account on first login
        user = User(google_id=google_id, email=email, name=name, avatar=avatar)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=None)
async def me():
    """Placeholder — use /users/me instead."""
    return {"status": "ok"}
