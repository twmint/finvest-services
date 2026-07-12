from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from models.ledger import UserBalance
    from models.holding import Holding
    from models.watchlist import Watchlist

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database import Base, TimestampMixin

class Role(str, enum.Enum):
    user = "user"
    admin = "admin"

class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email"),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True)
    fullname: Mapped[Optional[str]] = mapped_column(String(255))

    hashed_password: Mapped[str] = mapped_column(String(255))

    role: Mapped[Role] = mapped_column(
        SQLAlchemyEnum(Role, name="role"), default=Role.user, server_default="user", nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    balances: Mapped[list["UserBalance"]] = relationship(
        "UserBalance", back_populates="user", cascade="all, delete-orphan"
    )

    holdings: Mapped[list["Holding"]] = relationship(
        "Holding", back_populates="user", cascade="all, delete-orphan"
    )

    watchlists: Mapped[List["Watchlist"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_token", "token"),
        Index("ix_refresh_tokens_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    # Random 64-byte hex string
    token: Mapped[str] = mapped_column(String(128), unique=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken user_id={self.user_id} revoked={self.revoked}>"