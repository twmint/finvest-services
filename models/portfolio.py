from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from models.user import User
    from models.transaction import Transaction

from sqlalchemy import ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, TimestampMixin


class Portfolio(TimestampMixin, Base):
    __tablename__ = "portfolios"
    __table_args__ = (
        Index("ix_portfolios_user_id", "user_id"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    user: Mapped["User"] = relationship(back_populates="portfolios")
    holdings: Mapped[List["Holding"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Portfolio id={self.id} name={self.name!r}>"


class Holding(TimestampMixin, Base):
    __tablename__ = "holdings"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "symbol", name="uq_holdings_portfolio_symbol"),
        Index("ix_holdings_portfolio_id", "portfolio_id"),
    )

    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE")
    )
    symbol: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4))

    portfolio: Mapped["Portfolio"] = relationship(back_populates="holdings")

    def __repr__(self) -> str:
        return f"<Holding symbol={self.symbol!r} qty={self.quantity}>"
