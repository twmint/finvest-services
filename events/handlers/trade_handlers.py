from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from events.types import OrderPlaced
from models.ledger import CashAccount, CashLedger

async def create_ledger_entry(event: OrderPlaced, db: AsyncSession) -> None:
    result = await db.execute(
        select(CashAccount).filter_by(user_id=event.user_id).with_for_update()
    )
    user_balance = result.scalar_one_or_none()
    if user_balance:
        user_balance.cash_balance -= event.amount

    db.add(CashLedger(user_id=event.user_id, order_id=event.order_id, type=event.ledger_type, amount=event.amount))
    await db.flush()