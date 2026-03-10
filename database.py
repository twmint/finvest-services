import logging
import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import DateTime, func, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import AsyncAdaptedQueuePool
import psutil

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


engine = create_async_engine(
    DATABASE_URL,
    connect_args={"timeout": 15},
    future=True,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    max_overflow=0,
    echo=os.getenv("DB_ECHO", "false") == "true",
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass

class TimestampMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


async def check_db_connection() -> dict:
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "components": {},
    }

    try:
        start = time.perf_counter()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start) * 1000
        health_status["components"]["database"] = {
            "status": "healthy",
            "latency_ms": round(latency, 2),
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {"status": "unhealthy", "error": str(e)}

    memory_usage = psutil.virtual_memory().percent
    health_status["components"]["memory"] = {
        "status": "healthy" if memory_usage < 80 else "warning",
        "usage_percent": memory_usage,
    }

    return health_status


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
        finally:
            await session.close()