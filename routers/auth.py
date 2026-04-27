from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.user import User
from schemas.auth import AuthRequest, RegisterRequest, UserResponse
from schemas.base import ProblemDetail
from services.auth_service import AuthService
from utils.security import get_current_user

router = APIRouter()


@router.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.register(body.email, body.fullname, body.password)
    if not user:
        return ProblemDetail(title="Conflict", status=409, detail="Email already registered").to_response()


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(body: AuthRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.login(body.email, body.password)
    if not result:
        return ProblemDetail(title="Unauthorized", status=401, detail="Invalid combination of email and password").to_response()

    user, access_token, refresh_token = result
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UserResponse.model_validate(user).model_dump(by_alias=True, mode="json"),
    )
    response.set_cookie("access_token", access_token, httponly=True, samesite="strict", secure=settings.is_prod)
    response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="strict", secure=settings.is_prod)
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if refresh_token:
        service = AuthService(db)
        await service.logout(refresh_token)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


@router.post("/refresh")
async def refresh(
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        return ProblemDetail(title="Unauthorized", status=401, detail="Refresh token missing").to_response()

    service = AuthService(db)
    result = await service.refresh(refresh_token)
    if not result:
        resp = ProblemDetail(title="Unauthorized", status=401, detail="Invalid or expired refresh token").to_response()
        resp.delete_cookie("access_token")
        resp.delete_cookie("refresh_token")
        return resp

    new_access, new_refresh = result
    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    resp.set_cookie("access_token", new_access, httponly=True, samesite="strict", secure=settings.is_prod)
    resp.set_cookie("refresh_token", new_refresh, httponly=True, samesite="strict", secure=settings.is_prod)
    return resp