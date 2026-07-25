from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel


class TradeOrderRequest(BaseModel):
    ticker: str
    instrument_type: Literal["stock", "etf", "fund"]
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    quantity: Decimal
    order_market_price: Decimal
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: Literal["day", "gtc", "ioc"] = "day"


class ConfirmedOrder(BaseModel):
    order_id: str
    status: Literal["submitted", "filled", "rejected"]
    ticker: str
    side: str
    order_type: str
    quantity: Decimal
    estimated_total: Decimal
