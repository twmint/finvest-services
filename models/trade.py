from decimal import Decimal
from models.enums import OrderSide, OrderStatus, OrderType, TimeInForce
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Index, Numeric, String, Enum
from database import Base, TimestampMixin


class TradeOrder(TimestampMixin, Base):
    __tablename__ = "trade_orders"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    symbol: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True
    )

    side: Mapped[OrderSide] = mapped_column(
        Enum(OrderSide),
        nullable=False
    )

    order_type: Mapped[OrderType] = mapped_column(
        Enum(OrderType),
        nullable=False
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False
    )

    filled_quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        default=Decimal("0.00000000")
    )

    limit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    stop_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    average_fill_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    fees: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )

    total_value: Mapped[Decimal] = mapped_column(
        Numeric(16, 2), nullable=False, default=Decimal("0.00")
    )

    time_in_force: Mapped[TimeInForce] = mapped_column(
        Enum(TimeInForce),
        nullable=False,
        default=TimeInForce.DAY
    )

    client_order_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    broker_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index(
            "ix_trade_orders_user_id_status",
            "user_id",
            "status"
        ),
    )