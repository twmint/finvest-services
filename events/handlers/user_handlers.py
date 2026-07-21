from sqlalchemy.ext.asyncio import AsyncSession

from events.types import UserRegistered
from models.ledger import CashAccount


async def create_user_balance(event: UserRegistered, db: AsyncSession) -> None:
    db.add(CashAccount(user_id=event.user_id))
    await db.flush()