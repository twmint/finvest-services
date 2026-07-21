from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CashAmountRequest(BaseModel):
    amount: Decimal = Field(gt=0, le=1_000_000)


class DepositRequest(CashAmountRequest):
    pass


class WithdrawRequest(CashAmountRequest):
    pass


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    cash_balance: Decimal
    locked_cash: Decimal
    buying_power: Decimal
