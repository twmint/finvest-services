from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from events.types import OrderPlaced, OrderSubmitted
from models.ledger import CashAccount, CashLedger
from models.trade import TradeOrder
from services.execution_service import ExecutionService
from services.stock_service import StockService

async def create_ledger_entry(event: OrderPlaced, db: AsyncSession) -> None:
    result = await db.execute(
        select(CashAccount).filter_by(user_id=event.user_id).with_for_update()
    )
    user_balance = result.scalar_one_or_none()
    if user_balance:
        user_balance.cash_balance -= event.amount

    db.add(CashLedger(user_id=event.user_id, order_id=event.order_id, type=event.ledger_type, amount=event.amount))
    await db.flush()

async def attempt_fill(event: OrderSubmitted, db: AsyncSession) -> None:
    result = await db.execute(
        select(TradeOrder).filter_by(id=event.order_id).with_for_update()
    )
    trade_order = result.scalar_one_or_none()
    if trade_order is None:
        return

    execution_service = ExecutionService(db, StockService())
    await execution_service.try_fill(trade_order)