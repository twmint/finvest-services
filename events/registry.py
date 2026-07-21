from events.bus import event_bus
from events.handlers.user_handlers import create_user_balance
from events.types import OrderPlaced, UserRegistered
from events.handlers.trade_handlers import create_ledger_entry

def register_event_handlers() -> None:
    event_bus.subscribe(UserRegistered, create_user_balance)
    event_bus.subscribe(OrderPlaced, create_ledger_entry)
