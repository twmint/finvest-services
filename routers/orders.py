from typing import Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.order_service import OrderService

router = APIRouter()


def order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(db)


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
def place_order(order: TradeOrderRequest, service: OrderService = Depends(order_service)):
    result = service.place_order(
        ticker=order.ticker,
        side=order.side,
        order_type=order.order_type,
        quantity=order.quantity,
    )
    return OrderConfirmation(
        order_id=result.order_id,
        status=result.status,
        ticker=result.ticker,
        side=result.side,
        order_type=result.order_type,
        quantity=result.quantity,
        estimated_total=result.estimated_total, # TODO: calculate from real price
    )
