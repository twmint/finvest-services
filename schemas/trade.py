from typing import Literal, Optional

from pydantic import BaseModel


class TradeOrderRequest(BaseModel):
    ticker: str
    instrument_type: Literal["stock", "etf", "fund"]
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: Literal["day", "gtc", "ioc"] = "day"


class OrderConfirmation(BaseModel):
    order_id: str
    status: Literal["submitted", "filled", "rejected"]
    ticker: str
    side: str
    order_type: str
    quantity: float
    estimated_total: float
