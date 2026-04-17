import asyncio
import traceback
from enum import StrEnum
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .manager import ConnectionManager
from services.market_data_service import MarketDataService


class ConnectionStatus(StrEnum):
    CONNECTING = 'connecting'
    CONNECTED = 'connected'
    DISCONNECTED = 'disconnected'
    ERROR = 'error'

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
market_data_service = MarketDataService()


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
                        data[dtype] = market_data_service.get_favourites()
                    case StockMessageTypes.INDICES:
                        data[dtype] = market_data_service.get_indices()
                    case StockMessageTypes.NEWS:
                        data[dtype] = market_data_service.get_news()
                    case StockMessageTypes.MOVERS:
                        data[dtype] = market_data_service.get_market_movers()
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