from events.bus import event_bus
from events.handlers.user_handlers import create_user_balance
from events.types import OrderPlaced, OrderSubmitted, UserRegistered
from events.handlers.trade_handlers import attempt_fill, create_ledger_entry, update_cash_account

def register_event_handlers() -> None:
    event_bus.subscribe(UserRegistered, create_user_balance)
    event_bus.subscribe(OrderPlaced, create_ledger_entry)
    event_bus.subscribe(OrderSubmitted, [update_cash_account, attempt_fill])
