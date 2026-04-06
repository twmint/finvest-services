import os
from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from jose import jwt
from pwdlib import PasswordHash

from sqlalchemy import insert, select
from models.user import RefreshToken

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))

pwd_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_hasher.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire,
        "iss": os.getenv("JWT_ISSUER"),
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def create_refresh_token(user_id: int, db: AsyncSession) -> str:
    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=7)
    await db.execute(insert(RefreshToken).values(user_id=user_id, token=token, expires_at=expire))
    await db.commit()
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
    await db.commit()

    new_token = await create_refresh_token(user_id, db)
    return new_token, user_id
