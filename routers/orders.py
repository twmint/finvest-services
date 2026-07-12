from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from utils.security import get_current_user
from models.user import User
from schemas.base import ProblemDetail
from schemas.trade import TradeOrderRequest, OrderConfirmation
from services.order_service import OrderService
from services.stock_service import StockService

router = APIRouter()


def order_service(
    db: AsyncSession = Depends(get_db),
    stock_service: StockService = Depends(StockService),
) -> OrderService:
    return OrderService(db, stock_service)


@router.post("/", response_model=OrderConfirmation)
async def place_order(
    order: TradeOrderRequest,
    user: User = Depends(get_current_user),
    service: OrderService = Depends(order_service),
):
    result = await service.place_order(user_id=user.id, order=order)
    if result is None:
        return ProblemDetail(
            title="Unprocessable Entity",
            status=422,
            detail=f"Could not place order for '{order.ticker}'",
        ).to_response()

    return OrderConfirmation(
        order_id=result.order_id,
        status=result.status,
        ticker=result.ticker,
        side=result.side,
        order_type=result.order_type,
        quantity=result.quantity,
        estimated_total=result.estimated_total,
    )
