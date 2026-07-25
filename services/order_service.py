from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from events.types import OrderSubmitted
from events.bus import event_bus
from utils.result import Result
from schemas.errors import OrderRejectReason
from models.ledger import CashAccount
from models.enums import BalanceStatus, OrderSide, OrderStatus, OrderType, TimeInForce
from models.trade import TradeOrder
from schemas.trade import ConfirmedOrder, TradeOrderRequest
from services.stock_service import StockService


class OrderService:
    def __init__(self, db: AsyncSession, stock_service: StockService):
        self.db = db
        self.stock_service = stock_service

    async def place_order(
        self,
        user_id: int,
        order: TradeOrderRequest,
    ) -> Result[ConfirmedOrder, OrderRejectReason]:
        ticker = order.ticker.upper()
        reference_price = self.resolve_reference_price(order, order.order_market_price)
        quantity = order.quantity
        total = quantity * reference_price
        trade_order = TradeOrder(
                    user_id=user_id,
                    symbol=ticker,
                    side=OrderSide(order.side),
                    order_type=OrderType(order.order_type),
                    status=OrderStatus.PENDING,
                    quantity=order.quantity,
                    limit_price=order.limit_price,
                    stop_price=order.stop_price,
                    fees=Decimal("1.00"),
                    total_value=total,
                    time_in_force=TimeInForce(order.time_in_force),
                )
        self.db.add(trade_order)
        await self.db.flush()
        
        ticker_price_res = await self.get_ticker_price(ticker)

        if not ticker_price_res.ok:
            trade_order.status = OrderStatus.REJECTED
            await self.db.flush()
            return Result(value=None, error=ticker_price_res.error)
        ticker_price = ticker_price_res.value

        validation = self.validate_order(order)
        if not validation.ok:
            trade_order.status = OrderStatus.REJECTED
            await self.db.flush()
            return Result(value=None, error=validation.error)

        reference_price = self.resolve_reference_price(order, ticker_price)
        quantity = order.quantity
        total = quantity * reference_price
        if total <= 0:
            trade_order.status = OrderStatus.REJECTED
            await self.db.flush()
            return Result(value=None, error=OrderRejectReason.INVALID_TOTAL)

        if order.side == OrderSide.BUY:
            balance_status = await self.check_buying_power(user_id, total)
            if balance_status != BalanceStatus.OK:
                trade_order.status = OrderStatus.REJECTED
                await self.db.flush()
                return Result(value=None, error=OrderRejectReason.INSUFFICIENT_FUNDS)

        trade_order.total_value = total
        await self.db.flush()

        await event_bus.publish(OrderSubmitted(order_id=trade_order.id, user_id=user_id, amount=total), self.db)

        return Result(value=ConfirmedOrder(
            order_id=str(trade_order.id),
            status="filled" if trade_order.status == OrderStatus.FILLED else "submitted",
            ticker=ticker,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            estimated_total=total,
        ), error=None)

    def resolve_reference_price(self, order: TradeOrderRequest, ticker_price: Decimal) -> Decimal:
        if order.order_type == "market":
            return ticker_price
        if order.order_type == "stop":
            return order.stop_price
        return order.limit_price

    async def get_ticker_price(self, ticker: str) -> Result[Decimal, OrderRejectReason]:
        ticker_detail = self.stock_service.get_ticker_detail(ticker)
                
        if ticker_detail is None:
            return Result(value=None, error=OrderRejectReason.TICKER_NOT_FOUND)
        ticker_price_raw = ticker_detail.get("price")
        if not ticker_price_raw:
            return Result(value=None, error=OrderRejectReason.PRICE_UNAVAILABLE)
        ticker_price = Decimal(str(ticker_price_raw))

        return Result(value=ticker_price, error=None)

    def validate_order(self, order: TradeOrderRequest) -> Result[None, OrderRejectReason]:
        if order.order_type in ("limit", "stop_limit") and order.limit_price is None:
            return Result(value=None, error=OrderRejectReason.MISSING_LIMIT_PRICE)
        if order.order_type in ("stop", "stop_limit") and order.stop_price is None:
            return Result(value=None, error=OrderRejectReason.MISSING_STOP_PRICE)
        return Result(value=None, error=None)
    
    async def check_buying_power(self, user_id: int, total_cost: Decimal) -> BalanceStatus:
        result = await self.db.execute(
            select(CashAccount).filter_by(user_id=user_id).with_for_update()
        )
        user_balance = result.scalar_one_or_none()

        if not user_balance:
            return BalanceStatus.NOT_FOUND
        if user_balance.buying_power < total_cost:
            return BalanceStatus.INSUFFICIENT_FUNDS
        return BalanceStatus.OK
