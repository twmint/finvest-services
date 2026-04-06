from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import RefreshToken, User
from schemas.auth import AuthRequest, RegisterRequest, UserResponse
from schemas.base import ProblemDetail
from utils.security import change_refresh_token, create_access_token, create_refresh_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        return ProblemDetail(title="Conflict", status=409, detail="Email already registered").to_response()

    user = User(
        email=body.email,
        fullname=body.fullname,
        hashed_password=hash_password(body.password),
    )

    db.add(user)
    await db.commit()


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(body: AuthRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        return ProblemDetail(title="Unauthorized", status=401, detail="Invalid combination of email and password").to_response()
    
    access_token = create_access_token(user.id)
    refresh_token = await create_refresh_token(user.id, db)

    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UserResponse.model_validate(user).model_dump(by_alias=True, mode="json"),
    )
    response.set_cookie("access_token", access_token, httponly=True)
    response.set_cookie("refresh_token", refresh_token, httponly=True)
    return response

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if refresh_token:
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token_record = result.scalar_one_or_none()
        if token_record and not token_record.revoked:
            token_record.revoked = True
            await db.commit()

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


@router.post("/refresh")
async def refresh(
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        return ProblemDetail(title="Unauthorized", status=401, detail="Refresh token missing").to_response()

    result = await change_refresh_token(refresh_token, db)
    if not result:
        resp = ProblemDetail(title="Unauthorized", status=401, detail="Invalid or expired refresh token").to_response()
        resp.delete_cookie("access_token")
        resp.delete_cookie("refresh_token")
        return resp

    new_refresh_token, user_id = result
    new_access_token = create_access_token(user_id)

    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    resp.set_cookie("access_token", new_access_token, httponly=True)
    resp.set_cookie("refresh_token", new_refresh_token, httponly=True)
    return resp