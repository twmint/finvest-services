import uuid
from typing import Literal


class OrderResult:
    def __init__(
        self,
        order_id: str,
        status: Literal["submitted", "filled", "rejected"],
        ticker: str,
        side: str,
        order_type: str,
        quantity: float,
        estimated_total: float,
    ):
        self.order_id = order_id
        self.status = status
        self.ticker = ticker
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.estimated_total = estimated_total


class OrderService:
    def __init__(self, db):
        self.db = db
        
    def place_order(
        self,
        ticker: str,
        side: str,
        order_type: str,
        quantity: float,
    ) -> OrderResult:
        # TODO: real order processing, validation, and brokerage integration
        return OrderResult(
            order_id=str(uuid.uuid4()),
            status="submitted",
            ticker=ticker.upper(),
            side=side,
            order_type=order_type,
            quantity=quantity,
            estimated_total=0.0,
        )