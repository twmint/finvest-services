from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import BalanceStatus
from models.ledger import CashAccount


class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(self, user_id: int) -> CashAccount | None:
        result = await self.db.execute(
            select(CashAccount).filter_by(user_id=user_id)
        )
        balance = result.scalar_one_or_none()
        return balance

    async def deposit(self, user_id: int, amount: Decimal) -> CashAccount | None:
        result = await self.db.execute(
            select(CashAccount).filter_by(user_id=user_id).with_for_update()
        )
        balance = result.scalar_one_or_none()

        if not balance:
            return None

        balance.cash_balance += amount
        await self.db.flush()
        return balance

    async def check_withdrawable(self, user_id: int, amount: Decimal) -> BalanceStatus:
        result = await self.db.execute(
            select(CashAccount).filter_by(user_id=user_id).with_for_update()
        )
        balance = result.scalar_one_or_none()

        if not balance:
            return BalanceStatus.NOT_FOUND
        if balance.buying_power <= amount:
            return BalanceStatus.INSUFFICIENT_FUNDS
        return BalanceStatus.OK

    async def withdraw(self, user_id: int, amount: Decimal) -> CashAccount | None:
        result = await self.db.execute(
            select(CashAccount).filter_by(user_id=user_id).with_for_update()
        )
        balance = result.scalar_one_or_none()

        if not balance:
            return None

        balance.cash_balance -= amount
        await self.db.flush()
        return balance