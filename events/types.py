from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class UserRegistered:
    user_id: int

@dataclass(frozen=True)
class OrderPlaced:
    user_id: int
    order_id: int
    ledger_type: str
    quantity: Decimal
    amount: Decimal

@dataclass(frozen=True)
class OrderSubmitted:
    order_id: int
    user_id: int
    amount: Decimal