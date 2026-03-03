from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool
from dotenv import load_dotenv
import os
import logging

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Logger
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
        echo=True, 
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

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
