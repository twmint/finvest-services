from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import RefreshToken, User
from utils.security import DEFAULT_SCOPES, change_refresh_token, create_access_token, create_refresh_token, hash_password, verify_password


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, fullname: str, password: str) -> User | None:
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            return None
        user = User(email=email, fullname=fullname, hashed_password=hash_password(password))
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, email: str, password: str) -> tuple[User, str, str] | None:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            return None
        access_token = create_access_token(user.id, DEFAULT_SCOPES, user.role.value)
        refresh_token = await create_refresh_token(user.id, self.db)
        return user, access_token, refresh_token

    async def logout(self, refresh_token: str) -> None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token_record = result.scalar_one_or_none()
        if token_record and not token_record.revoked:
            token_record.revoked = True
            await self.db.commit()

    async def refresh(self, old_token: str) -> tuple[str, str] | None:
        result = await change_refresh_token(old_token, self.db)
        if not result:
            return None
        new_refresh, user_id = result
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        new_access = create_access_token(user_id, DEFAULT_SCOPES, user.role.value)
        return new_access, new_refresh