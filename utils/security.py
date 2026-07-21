import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt
from pwdlib import PasswordHash
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.user import RefreshToken, User

SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
DEFAULT_SCOPES = [
    "read:portfolio", "write:portfolio",
    "read:orders", "write:orders",
    "read:watchlist", "write:watchlist",
    "read:market",
]

pwd_hasher = PasswordHash.recommended()

class InvalidSessionException(HTTPException):
    def __init__(self, detail: str = "Session invalid"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_hasher.verify(plain, hashed)


def create_access_token(user_id: int, scopes: list[str], role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": str(uuid.uuid4()),
        "type": "access",
        "scope": " ".join(scopes),
        "roles": [role],
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def create_refresh_token(user_id: int, db: AsyncSession) -> str:
    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=7)
    await db.execute(insert(RefreshToken).values(user_id=user_id, token=token, expires_at=expire))
    return token

async def change_refresh_token(old_token: str, db: AsyncSession) -> tuple[str, int] | None:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == old_token)
    )
    refresh_token = result.scalar_one_or_none()

    if not refresh_token or refresh_token.revoked or refresh_token.expires_at < datetime.now(timezone.utc):
        return None

    user_id = refresh_token.user_id
    refresh_token.revoked = True

    new_token = await create_refresh_token(user_id, db)
    return new_token, user_id


async def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not access_token:
        raise InvalidSessionException()

    try:
        payload = jwt.decode(
                access_token, 
                SECRET_KEY, 
                algorithms=[ALGORITHM],
                issuer=settings.jwt_issuer,
                audience=settings.jwt_audience,
                options={"verify_nbf": True}
            )
    except JWTError:
        raise InvalidSessionException()

    if payload.get("type") != "access":
        raise InvalidSessionException()

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidSessionException()

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise InvalidSessionException()

    return user
