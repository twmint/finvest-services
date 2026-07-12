from decimal import Decimal
from typing import TYPE_CHECKING
from models.enums import LedgerType
from sqlalchemy import Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class CashLedger(TimestampMixin, Base):
    __tablename__ = "cash_ledger"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("trade_orders.id"), nullable=True)
    type: Mapped[LedgerType] = mapped_column(Enum(LedgerType))
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2)) # Can be negative

class UserBalance(TimestampMixin, Base):
    __tablename__ = "user_balances"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0.00"))
    locked_cash: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0.00"))
    # Margin accounts:
    # margin_balance: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0.00"))
    # equity_balance: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0.00"))

    user: Mapped["User"] = relationship(back_populates="balances")

    @property
    def buying_power(self) -> Decimal:
        return self.cash_balance - self.locked_cash
    
