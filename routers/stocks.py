from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.stock_service import StockService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/history")
@limiter.limit("30/minute")
def get_stock_history(request: Request, service: StockService = Depends(StockService)):
    return service.get_stock_history()