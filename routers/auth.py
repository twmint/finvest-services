from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from schemas.auth import RegisterRequest
from utils.security import hash_password

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Email already registered"},
        )

    user = User(
        email=body.email,
        fullname=body.fullname,
        hashed_password=hash_password(body.password),
    )

    db.add(user)
    await db.flush()

@router.post("/login")
async def login():
    pass


@router.post("/logout")
async def logout():
    pass


@router.post("/refresh")
async def refresh_token():
    pass
