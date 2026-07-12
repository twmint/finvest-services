from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from models.enums import OrderSide
from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class Holding(TimestampMixin, Base):
    __tablename__ = "holdings"

    __table_args__ = (
        UniqueConstraint("user_id", "symbol", name="uq_holdings_user_symbol"),
        Index("ix_holdings_user_id", "user_id"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, default=Decimal("0.00000000"))
    average_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    user: Mapped["User"] = relationship(back_populates="holdings")

    def __repr__(self) -> str:
        return f"<Holding symbol={self.symbol!r} qty={self.quantity}>"

class OrderExecution(Base):
    __tablename__ = "order_executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("trade_orders.id", ondelete="CASCADE"), index=True
    )
    symbol: Mapped[str] = mapped_column(String(10), index=True)
    side: Mapped[OrderSide] = mapped_column(SAEnum(OrderSide))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8)) # Amount filled in this exact execution
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))    # Execution price for this exact block
    total: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())