from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/{symbol}")
@limiter.limit("60/minute")
def get_ticker_detail(symbol: str, request: Request):
    """
    Fetch full ticker details (quote + stats).
    TODO: Use yahooquery Ticker(symbol) to get real data.
    Returns mock data for now.
    """
    return {
        "ticker": symbol.upper(),
        "name": f"{symbol.upper()} Inc.",
        "price": 0.0,
        "change": 0.0,
        "changePercent": 0.0,
        "open": 0.0,
        "previousClose": 0.0,
        "dayHigh": 0.0,
        "dayLow": 0.0,
        "fiftyTwoWeekHigh": 0.0,
        "fiftyTwoWeekLow": 0.0,
        "volume": 0,
        "avgVolume": 0,
        "marketCap": 0,
        "peRatio": None,
        "instrumentType": "stock",
    }
