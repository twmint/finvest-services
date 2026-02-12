import numpy as np
import pandas as pd
from fastapi import APIRouter, Request
from yahooquery import Ticker
from constants import WATCHLIST_TICKERS
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/history")
@limiter.limit("30/minute")
def get_stock_history(request: Request):
    try:
        ticker = Ticker(WATCHLIST_TICKERS, asynchronous=True, progress=True)
        hist = ticker.history(period="1mo", interval="1wk").reset_index()
        hist['date'] = pd.to_datetime(hist['date'], utc=True).dt.tz_localize(None)
        hist['date'] = hist['date'].dt.date
        hist["close"] = np.round(hist["close"], 2)
        hist = hist.pivot(index="date", columns="symbol", values="close").fillna(0.00).reset_index()
        result = hist.to_dict(orient="records")
        return result
    except Exception as e:
        print(f"Error fetching stock history: {e}")
        return []
