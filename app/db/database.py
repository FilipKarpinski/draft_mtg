import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL

# Check if we're running in test mode
TESTING = "pytest" in sys.modules

Base = declarative_base()

if TESTING:
    # Use synchronous connection for tests
    SYNC_DATABASE_URL = DATABASE_URL
    sync_engine = create_engine(SYNC_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

    def get_db() -> Generator[Session, None, None]:  # type: ignore
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
else:
    # Use async connection for normal operation
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql:", "postgresql+asyncpg:", 1)
    engine = create_async_engine(ASYNC_DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

    async def get_db() -> AsyncGenerator[AsyncSession, None]:  # type: ignore
        db = AsyncSessionLocal()
        try:
            yield db
        finally:
            await db.close()


@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
