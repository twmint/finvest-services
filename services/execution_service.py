from decimal import Decimal
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from events.types import OrderPlaced
from events.bus import event_bus
from models.enums import LedgerType, OrderSide, OrderStatus
from models.trade import TradeOrder
from models.holding import Holding, OrderExecution
from services.stock_service import StockService


class ExecutionService:
    def __init__(self, db: AsyncSession, stock_service: StockService):
        self.db = db
        self.stock_service = stock_service

    async def try_fill(self, trade_order: TradeOrder) -> None:
        ticker_detail = self.stock_service.get_ticker_detail(trade_order.symbol)
        if ticker_detail is None:
            return
        ticker_price_raw = ticker_detail.get("price")
        if not ticker_price_raw:
            return
        ticker_price = Decimal(str(ticker_price_raw))

        order_type = trade_order.order_type.value
        side = trade_order.side.value

        to_fill = False
        execution_price: Decimal | None = None

        if order_type == "market":
            to_fill = True
            execution_price = ticker_price
        elif order_type == "limit":
            to_fill = self.check_condition(side, trade_order.limit_price, ticker_price, check_type="limit")
            execution_price = trade_order.limit_price if to_fill else None
        elif order_type == "stop":
            to_fill = self.check_condition(side, trade_order.stop_price, ticker_price, check_type="stop")
            execution_price = ticker_price if to_fill else None
        elif order_type == "stop_limit":
            triggered = self.check_condition(side, trade_order.stop_price, ticker_price, check_type="stop")
            to_fill = triggered and self.check_condition(side, trade_order.limit_price, ticker_price, check_type="limit")
            execution_price = trade_order.limit_price if to_fill else None

        if not to_fill or execution_price is None:
            return

        quantity = trade_order.quantity
        order_execution = OrderExecution(
            order_id=trade_order.id,
            symbol=trade_order.symbol,
            side=trade_order.side,
            quantity=quantity,
            price=execution_price,
            total=quantity * execution_price,
        )
        self.db.add(order_execution)
        await self.db.flush()

        await self.process_execution_fill(trade_order.user_id, order_execution)
        trade_order.status = OrderStatus.FILLED
        trade_order.filled_quantity = quantity
        trade_order.average_fill_price = execution_price

        total = quantity * execution_price
        await event_bus.publish(OrderPlaced(
            user_id=trade_order.user_id,
            order_id=trade_order.id,
            ledger_type=LedgerType.ORDER_SETTLE,
            quantity=quantity,
            amount=total if trade_order.side == OrderSide.BUY else -total,
        ), self.db)

    async def process_execution_fill(self, user_id: int, execution: OrderExecution) -> None:
        result = await self.db.execute(
            select(Holding)
            .filter_by(user_id=user_id, symbol=execution.symbol)
            .with_for_update()
        )
        holding = result.scalar_one_or_none()

        exec_qty = Decimal(str(execution.quantity))
        exec_price = Decimal(str(execution.price))

        if execution.side == OrderSide.BUY:
            if not holding:
                holding = Holding(user_id=user_id, symbol=execution.symbol, quantity=exec_qty, average_cost=exec_price)
                self.db.add(holding)
            else:
                total_cost = (holding.average_cost * holding.quantity) + (exec_price * exec_qty)
                holding.quantity += exec_qty
                holding.average_cost = total_cost / holding.quantity
        elif execution.side == OrderSide.SELL:
            if holding:
                holding.quantity -= exec_qty
                if holding.quantity <= 0:
                    await self.db.delete(holding)

        await self.db.flush()

    def check_condition(self, side: str, price: Decimal, current_price: Decimal, check_type: Literal["limit", "stop"]) -> bool:
        if check_type == "limit":
            return current_price <= price if side == "buy" else current_price >= price
        elif check_type == "stop":
            return current_price >= price if side == "buy" else current_price <= price
        raise ValueError(f"Invalid check_type: {check_type}")
