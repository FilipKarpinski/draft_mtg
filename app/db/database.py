from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import DATABASE_URL

# Convert PostgreSQL URL to async version
async_database_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(async_database_url, echo=True)
SessionLocal = async_sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=engine)
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
