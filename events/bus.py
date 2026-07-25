
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable]] = {}

    def subscribe(self, event_type: type, subscriber: list[Callable] | Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if not isinstance(subscriber, list):
            self._subscribers[event_type].append(subscriber)
        else:
            self._subscribers[event_type].extend(subscriber)

    def unsubscribe(self, event_type: type, subscriber: list[Callable] | Callable) -> None:
        if event_type in self._subscribers:
            if not isinstance(subscriber, list):
                self._subscribers[event_type].remove(subscriber)
            else:
                for sub in subscriber:
                    self._subscribers[event_type].remove(sub)

    async def publish(self, event, db: AsyncSession) -> None:
        event_type = type(event)
        for subscriber in self._subscribers.get(event_type, []):
            await subscriber(event, db)

    def clear(self) -> None:
        self._subscribers = {}


event_bus = EventBus()