from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from models.user import User

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base, TimestampMixin


class Watchlist(TimestampMixin, Base):
    __tablename__ = "watchlists"
    __table_args__ = (
        Index("ix_watchlists_user_id", "user_id"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))

    user: Mapped["User"] = relationship(back_populates="watchlists")
    items: Mapped[List["WatchlistItem"]] = relationship(
        back_populates="watchlist", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Watchlist id={self.id} name={self.name!r}>"


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_items_watchlist_symbol"),
        Index("ix_watchlist_items_watchlist_id", "watchlist_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    watchlist_id: Mapped[int] = mapped_column(
        ForeignKey("watchlists.id", ondelete="CASCADE")
    )
    symbol: Mapped[str] = mapped_column(String(20))

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    watchlist: Mapped["Watchlist"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"<WatchlistItem symbol={self.symbol!r}>"
