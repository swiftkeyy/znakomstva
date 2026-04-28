from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings


def _get_async_db_url(url: str) -> str:
    """Convert postgresql:// to postgresql+asyncpg:// for async driver."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(
    _get_async_db_url(settings.database_url),
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=False,
)

AsyncSessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session


async def init_db() -> None:
    from database.models.base import Base  # noqa: F401 — import all models via __init__
    import database.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add new columns if they don't exist (safe migration)
        await conn.execute(text(
            "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS name VARCHAR(64)"
        ))
        await conn.execute(text(
            "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS gender VARCHAR(16)"
        ))
        await conn.execute(text(
            "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS looking_for VARCHAR(16)"
        ))


async def close_db() -> None:
    await engine.dispose()
