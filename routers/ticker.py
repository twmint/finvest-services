from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from schemas.base import ProblemDetail
from services.stock_service import StockService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/{symbol}")
@limiter.limit("60/minute")
def get_ticker_detail(symbol: str, request: Request):
    service = StockService()
    detail = service.get_ticker_detail(symbol)
    if detail is None:
        return ProblemDetail(
            title="Not Found",
            status=404,
            detail=f"No data found for symbol '{symbol.upper()}'",
        ).to_response()
    return JSONResponse(content=detail)