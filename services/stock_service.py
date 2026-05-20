import numpy as np
import pandas as pd
from yahooquery import Ticker

from constants import WATCHLIST_TICKERS

_QUOTE_TYPE_MAP = {"EQUITY": "stock", "ETF": "etf", "MUTUALFUND": "fund"}


class StockService:
    def get_ticker_detail(self, symbol: str) -> dict | None:
        try:
            t = Ticker(symbol)
            price_data = t.price.get(symbol, {})
            summary = t.summary_detail.get(symbol, {})

            if not price_data or isinstance(price_data, str):
                return None

            quote_type = (price_data.get("quoteType") or "EQUITY").upper()
            instrument_type = _QUOTE_TYPE_MAP.get(quote_type, "stock")
            pe = summary.get("trailingPE")

            return {
                "ticker": symbol.upper(),
                "name": price_data.get("shortName") or price_data.get("longName") or symbol.upper(),
                "price": round(price_data.get("regularMarketPrice") or 0.0, 2),
                "change": round(price_data.get("regularMarketChange") or 0.0, 4),
                "changePercent": round(price_data.get("regularMarketChangePercent") or 0.0, 4),
                "open": round(price_data.get("regularMarketOpen") or 0.0, 2),
                "previousClose": round(price_data.get("regularMarketPreviousClose") or 0.0, 2),
                "dayHigh": round(price_data.get("regularMarketDayHigh") or 0.0, 2),
                "dayLow": round(price_data.get("regularMarketDayLow") or 0.0, 2),
                "fiftyTwoWeekHigh": round(summary.get("fiftyTwoWeekHigh") or 0.0, 2),
                "fiftyTwoWeekLow": round(summary.get("fiftyTwoWeekLow") or 0.0, 2),
                "volume": int(price_data.get("regularMarketVolume") or 0),
                "avgVolume": int(summary.get("averageVolume") or 0),
                "marketCap": int(price_data.get("marketCap") or 0),
                "peRatio": round(pe, 2) if pe is not None else None,
                "instrumentType": instrument_type,
            }
        except Exception as e:
            print(f"Error fetching ticker detail for {symbol}: {e}")
            return None

    def get_stock_history(self) -> list[dict]:
        try:
            ticker = Ticker(WATCHLIST_TICKERS, asynchronous=True, progress=True)
            hist = ticker.history(period="1mo", interval="1wk").reset_index()
            hist["date"] = pd.to_datetime(hist["date"], utc=True).dt.tz_localize(None)
            hist["date"] = hist["date"].dt.date
            hist["close"] = np.round(hist["close"], 2)
            hist = hist.pivot(index="date", columns="symbol", values="close").fillna(0.00).reset_index()
            return hist.to_dict(orient="records")
        except Exception as e:
            print(f"Error fetching stock history: {e}")
            return []