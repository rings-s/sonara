from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.routes import auth, users, teachers, bookings, wallet, events, reviews, halls, courses

app = FastAPI(title="Sonara API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(teachers.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(wallet.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(halls.router, prefix="/api/v1")
app.include_router(courses.router, prefix="/api/v1")
