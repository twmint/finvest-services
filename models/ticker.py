from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime,
    Enum as SAEnum, ForeignKey, Index, Numeric, String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base, TimestampMixin


class InstrumentType(str, enum.Enum):
    STOCK = "stock"
    ETF = "etf"
    FUND = "fund"


class Ticker(TimestampMixin, Base):
    __tablename__ = "tickers"
    __table_args__ = (
        Index("ix_tickers_instrument_type", "instrument_type"),
        Index("ix_tickers_sector", "sector"),
    )

    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    instrument_type: Mapped[InstrumentType] = mapped_column(
        SAEnum(InstrumentType, name="instrument_type_enum")
    )

    exchange: Mapped[Optional[str]] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    country: Mapped[Optional[str]] = mapped_column(String(100))

    sector: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    ipo_date: Mapped[Optional[date]] = mapped_column(Date)

    description: Mapped[Optional[str]] = mapped_column(String(2000))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    snapshot: Mapped[Optional["TickerSnapshot"]] = relationship(
        back_populates="ticker", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Ticker symbol={self.symbol!r} type={self.instrument_type}>"


class TickerSnapshot(Base):
    __tablename__ = "ticker_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_id: Mapped[int] = mapped_column(
        ForeignKey("tickers.id", ondelete="CASCADE"), unique=True, index=True
    )

    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    open: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    previous_close: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    day_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    day_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    fifty_two_week_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    fifty_two_week_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    change: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    change_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))

    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    avg_volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    market_cap: Mapped[Optional[int]] = mapped_column(BigInteger)

    pe_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ticker: Mapped["Ticker"] = relationship(back_populates="snapshot")

    def __repr__(self) -> str:
        return f"<TickerSnapshot ticker_id={self.ticker_id} price={self.price} fetched_at={self.fetched_at}>"
