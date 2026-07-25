from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from utils.security import get_current_user
from models.user import User
from schemas.errors import ProblemDetail
from schemas.trade import ConfirmedOrder, TradeOrderRequest
from services.order_service import OrderService
from services.stock_service import StockService

router = APIRouter()


def order_service(
    db: AsyncSession = Depends(get_db),
    stock_service: StockService = Depends(StockService),
) -> OrderService:
    return OrderService(db, stock_service)


@router.post("/", response_model=ConfirmedOrder)
async def place_order(
    order: TradeOrderRequest,
    user: User = Depends(get_current_user),
    service: OrderService = Depends(order_service),
):
    result = await service.place_order(user_id=user.id, order=order)
    if not result.ok:
        return ProblemDetail(
            title="Unprocessable Entity",
            status=422,
            detail=f"Could not place order for '{order.ticker}', reason: {result.error.value}",
        ).to_response()

    return result.value
