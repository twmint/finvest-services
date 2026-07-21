
import enum

class InstrumentType(str, enum.Enum):
    STOCK = "stock"
    ETF = "etf"
    FUND = "fund"

class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class LedgerType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    ORDER_LOCK = "order_lock"       # Lock cash when BUY order opens
    ORDER_UNLOCK = "order_unlock"   # Release cash if BUY order cancels
    ORDER_SETTLE = "order_settle"   # Permanent deduction when BUY fills

class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class TimeInForce(str, enum.Enum):
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"

class BalanceStatus(str, enum.Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    INSUFFICIENT_FUNDS = "insufficient_funds"
