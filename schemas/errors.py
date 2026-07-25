import enum

from typing import Optional
from pydantic import BaseModel
from fastapi.responses import JSONResponse


class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: Optional[str] = None

    def to_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.status, content=self.model_dump())

class OrderRejectReason(str, enum.Enum):
    TICKER_NOT_FOUND = "TickerNotFound"
    PRICE_UNAVAILABLE = "PriceUnavailable"
    MISSING_LIMIT_PRICE = "MissingLimitPrice"
    MISSING_STOP_PRICE = "MissingStopPrice"
    INVALID_ORDER_TYPE = "InvalidOrderType"
    INVALID_TOTAL = "InvalidTotal"
    INSUFFICIENT_FUNDS = "InsufficientFunds"
    ACCOUNT_NOT_FOUND = "AccountNotFound"