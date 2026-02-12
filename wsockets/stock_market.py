import random
import re
import asyncio
import traceback
from enum import StrEnum
from yahooquery import Ticker, Screener
from .manager import ConnectionManager
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from scrapers.base import Scraper
from constants import NEWS_PUBLISHERS, WATCHLIST_TICKERS

class ConnectionStatus(StrEnum):
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',

class MessageEvents(StrEnum):
    AUTH = 'authenticate'
    SUBSCRIBE = 'subscribe'
    UNSUBSCRIBE = 'unsubscribe'
    DATA = 'data'
    PING = 'ping'
    ERROR = 'error'
    CLOSE = 'close'

class StockMessageTypes(StrEnum):
    FAVOURITES = 'favourites'
    MOVERS = 'movers'
    INDICES = 'indices'
    NEWS = 'news'

interval = 5 #seconds
router = APIRouter()
manager = ConnectionManager()

HEADERS = {"User-Agent": "Mozilla/5.0"}

@router.websocket("/stock-market")
async def market_stream(
    websocket: WebSocket,
):
    client_id = await manager.connect(websocket)
    try:
        await manager.send_json({
            "connection_status": ConnectionStatus.CONNECTED,
            "client_id": client_id,
            "authenticated": False
        }, client_id)

        initial_message = await websocket.receive_json()

        if initial_message.get("event") == MessageEvents.AUTH:
            token = initial_message.get("token")
            is_valid = manager.validate_token(token)
            client = manager.get_client(client_id)
            if client is not None:
                client["token"] = token if is_valid else None
                client["authenticated"] = is_valid

            await manager.send_json({
                "event": MessageEvents.AUTH,
                "authenticated": is_valid
            }, client_id)

            if not is_valid:
                await websocket.close(code=401, reason="Authentication failed")
                return

            data_types: list[str] = initial_message.get("subscribe", [item.value for item in StockMessageTypes])
        else:
            await websocket.close(code=4001, reason="Authentication required")
            return

        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_json(), timeout=1)
                if message.get("event") == MessageEvents.PING:
                    await manager.ping(websocket)
            except asyncio.TimeoutError:
                pass  # No message received within timeout, continue to send data

            data: dict = {}
            for dtype in data_types:
                match dtype:
                    case StockMessageTypes.FAVOURITES:
                        data[dtype] = GetFavourites()
                    case StockMessageTypes.INDICES:
                        data[dtype] = GetIndices(None)
                    case StockMessageTypes.NEWS:
                        data[dtype] = GetNews()
                    case StockMessageTypes.MOVERS:
                        data[dtype] = GetMarketMovers()
                    case _:
                        continue
            
            await websocket.send_json({
                "event": MessageEvents.DATA,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            await asyncio.sleep(interval)

    except WebSocketDisconnect as e:
        manager.disconnect(client_id, e.code)
        print(f"Client {client_id} disconnected from stock-market stream")
    except Exception as e:
        manager.disconnect(client_id)
        print(f"Error for client {client_id}: {e}")
        traceback.print_exc()

def GetFavourites() -> dict[str, dict]:
    try:
        ticker_info = {}
        all_symbols = " ".join(WATCHLIST_TICKERS)
        myInfo = Ticker(all_symbols, asynchronous=True, progress=True)
        myDict = myInfo.price

        for ticker in WATCHLIST_TICKERS:
            ticker = str(ticker)
            info = myDict.get(ticker, {})
            ticker_info[ticker] = {
                "price": info.get('regularMarketPrice'),
                "marketCap": info.get('marketCap')
            }
        return ticker_info
    except Exception as e:
        print(f"Error fetching favourites: {e}")
        return {}

def GetMarketMovers() -> dict[str, list[dict]]:
    try:
        s = Screener()
        data = s.get_screeners(["day_gainers", "day_losers", "most_actives"], 5)
        response = {
            "gainers": normalize_quotes(
                data.get("day_gainers", {}).get("quotes", [])
            ),
            "losers": normalize_quotes(
                data.get("day_losers", {}).get("quotes", [])
            ),
            "actives": normalize_quotes(
                data.get("most_actives", {}).get("quotes", []),
                include_volume=True
            )
        }
        return response
    except Exception as e:
        print(f"Error fetching market movers: {e}")
        return {}

def GetIndices(regions: list[str]) -> dict[str, dict]:
    data = {}
    regions = regions or ["Americas", "Europe", "Asia"]
    url = "https://finance.yahoo.com/markets/"
    scraper = Scraper()
    soup = scraper.get_soup(url)
    if soup is None:
        return data

    for region in regions:
        region_section = soup.find("h3", string=lambda text: text and text.casefold() == region.casefold())
        if region_section:
            region_data = {}
            table = region_section.find_next("table")
            if not table:
                continue
            for row in table.find_all("tr")[1:]:
                columns = row.find_all("td")
                if len(columns) >= 3:
                    symbol = columns[0].get_text(strip=True)
                    price = columns[2].get_text(strip=True)
                    change = columns[3].get_text(strip=True)

                    formatted_price = re.sub(r'\([^)]*\)', '', price)
                    match = re.match(r'([\d,\.]+)([+-])([\d,\.]+)', formatted_price)
                    if match:
                        base_price, operator, change_amount = match.groups()
                        region_data[symbol] = {
                            "price": base_price,
                            "trend": operator,
                            "priceChange": change_amount,
                            "percentChange": change
                        }
            data[region] = region_data
    return data

def GetNews() -> dict[str, dict]:
    data = {}
    url = "https://finance.yahoo.com/topic/economic-news/"
    scraper = Scraper()
    soup = scraper.get_soup(url)
    if soup is None:
        return data
    featured = soup.find("section", {"class": "topic-featured"})
    if not featured:
        return data
    news_list = featured.find("div", {"class": "story-list"})
    if not news_list:
        return data
    now = int(datetime.now(timezone.utc).timestamp())
    yesterday = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
    for idx, news in enumerate(news_list, start=1):
        try:
            link = news.find("a", {"class": "subtle-link"})
            if not link:
                continue
            
            title_elem = news.find("h3", {"class": "clamp"})
            title = title_elem.get_text(strip=True) if title_elem else "No title"
            
            summary_elem = news.find("p", {"class": "clamp"})
            summary = summary_elem.get_text(strip=True) if summary_elem else ""
            
            href = link.get("href", "")
            
            img = news.find("img")
            img_src = img.get("src", "") if img else ""
            
            data[idx] = {
                "id": idx,
                "title": title,
                "summary": summary,
                "url": href,
                "provider": NEWS_PUBLISHERS[idx % len(NEWS_PUBLISHERS)],
                "time": random.randint(yesterday, now),
                "image": img_src
            }
        except Exception as e:
            print(f"Error parsing news item {idx}: {e}")
            continue
    return data

def normalize_quotes(quotes, include_volume=False):
    items = []
    for q in quotes:
        items.append({
            "symbol": q["symbol"],
            "name": q.get("shortName") or q.get("longName"),
            "price": q["regularMarketPrice"],
            "percentChange": f"{round(q['regularMarketChangePercent'], 2):+.2f}%",
            **({"volume": q["regularMarketVolume"]} if include_volume else {})
        })
    return items
