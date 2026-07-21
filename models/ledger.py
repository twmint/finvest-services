from decimal import Decimal
from typing import TYPE_CHECKING
from models.enums import LedgerType
from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric
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

class CashAccount(TimestampMixin, Base):
    __tablename__ = "cash_accounts"
    __table_args__ = (
        CheckConstraint("cash_balance >= 0", name="ck_cash_balance_nonneg"),
        CheckConstraint("locked_cash >= 0", name="ck_locked_cash_nonneg"),
        CheckConstraint("cash_balance >= locked_cash", name="ck_cash_covers_locked"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0.00"))
    locked_cash: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0.00"))

    user: Mapped["User"] = relationship(back_populates="balance")

    @property
    def buying_power(self) -> Decimal:
        return self.cash_balance - self.locked_cash
    
