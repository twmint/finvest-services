
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable]] = {}

    def subscribe(self, event_type: type, subscriber: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(subscriber)

    def unsubscribe(self, event_type: type, subscriber: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(subscriber)

    async def publish(self, event, db: AsyncSession) -> None:
        event_type = type(event)
        for subscriber in self._subscribers.get(event_type, []):
            await subscriber(event, db)

    def clear(self) -> None:
        self._subscribers = {}


event_bus = EventBus()