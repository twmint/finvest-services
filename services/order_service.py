from decimal import Decimal
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from events.types import OrderPlaced
from events.bus import event_bus
from models.ledger import CashAccount, CashLedger
from models.enums import BalanceStatus, LedgerType, OrderSide, OrderStatus, OrderType, TimeInForce
from models.trade import TradeOrder
from models.holding import Holding, OrderExecution
from schemas.trade import TradeOrderRequest
from services.stock_service import StockService


class OrderResult:
    def __init__(
        self,
        order_id: str,
        status: Literal["submitted", "filled", "rejected"],
        ticker: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        estimated_total: Decimal,
    ):
        self.order_id = order_id
        self.status = status
        self.ticker = ticker
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.estimated_total = estimated_total


class OrderService:
    def __init__(self, db: AsyncSession, stock_service: StockService):
        self.db = db
        self.stock_service = stock_service

    async def place_order(
        self,
        user_id: int,
        order: TradeOrderRequest,
    ) -> OrderResult | None:
        ticker = order.ticker.upper()
        ticker_detail = self.stock_service.get_ticker_detail(ticker)
        
        if ticker_detail is None:
            return None
        ticker_price_raw = ticker_detail.get("price")
        if not ticker_price_raw:
            return None
        ticker_price = Decimal(str(ticker_price_raw))

        if order.order_type in ("limit", "stop_limit") and order.limit_price is None:
            return None
        if order.order_type in ("stop", "stop_limit") and order.stop_price is None:
            return None

        to_fill = False
        execution_price: Decimal | None = None

        if order.order_type == "market":
            to_fill = True
            execution_price = ticker_price
        elif order.order_type == "limit":
            to_fill = self.check_condition(order.side, order.limit_price, ticker_price, check_type="limit")
            execution_price = order.limit_price if to_fill else None
        elif order.order_type == "stop":
            to_fill = self.check_condition(order.side, order.stop_price, ticker_price, check_type="stop")
            execution_price = ticker_price if to_fill else None
        elif order.order_type == "stop_limit":
            triggered = self.check_condition(order.side, order.stop_price, ticker_price, check_type="stop")
            to_fill = triggered and self.check_condition(order.side, order.limit_price, ticker_price, check_type="limit")
            execution_price = order.limit_price if to_fill else None
        else:
            return None

        quantity = order.quantity
        reference_price = execution_price if execution_price is not None else (order.limit_price or order.stop_price)
        total = quantity * reference_price
        if total <= 0:
            return None
        
        if order.side == OrderSide.BUY:
            balance_status = await self.check_buying_power(user_id, total)
            if balance_status != BalanceStatus.OK:
                return None

        trade_order = TradeOrder(
            user_id=user_id,
            symbol=ticker,
            side=OrderSide(order.side),
            order_type=OrderType(order.order_type),
            status=OrderStatus.PENDING,
            quantity=quantity,
            limit_price=order.limit_price,
            stop_price=order.stop_price,
            fees=Decimal("0.00"),
            total_value=total,
            time_in_force=TimeInForce(order.time_in_force),
        )
        self.db.add(trade_order)
        await self.db.flush()

        if not to_fill:
            trade_order.status = OrderStatus.OPEN
            return OrderResult(
                order_id=str(trade_order.id),
                status="submitted",
                ticker=ticker,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                estimated_total=total,
            )

        order_execution = OrderExecution(
            order_id=trade_order.id,
            symbol=ticker,
            side=OrderSide(order.side),
            quantity=quantity,
            price=execution_price,
            total=quantity * execution_price,
        )
        self.db.add(order_execution)
        await self.db.flush()

        await self.process_execution_fill(user_id, order_execution)
        trade_order.status = OrderStatus.FILLED
        trade_order.filled_quantity = quantity
        trade_order.average_fill_price = execution_price

        await event_bus.publish(OrderPlaced(
            user_id=user_id,
            order_id=trade_order.id,
            ledger_type=LedgerType.ORDER_SETTLE,
            quantity=quantity,
            amount=total if order.side == OrderSide.BUY else -total,
        ), self.db)

        return OrderResult(
            order_id=str(trade_order.id),
            status="filled",
            ticker=ticker,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            estimated_total=total,
        )
    
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
