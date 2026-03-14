import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Literal

router = APIRouter()


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


@router.post("/", response_model=OrderConfirmation)
def place_order(order: TradeOrderRequest):
    """
    Submit a trade order.
    TODO: Add real order processing, validation, and brokerage integration.
    Returns mock confirmation for now.
    """
    return OrderConfirmation(
        order_id=str(uuid.uuid4()),
        status="submitted",
        ticker=order.ticker.upper(),
        side=order.side,
        order_type=order.order_type,
        quantity=order.quantity,
        estimated_total=0.0,  # TODO: calculate from real price
    )
