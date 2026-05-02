"""Async SQLAlchemy engine + pgvector setup."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from app.config import settings

# Do not pool connections in Celery config because of Asyncio loop closing issues
engine = create_async_engine(
    settings.database_url, 
    echo=False, 
    poolclass=NullPool
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Create tables and enable pgvector."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        from app.models import place  # noqa: F401 — registers models
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """FastAPI dependency — yields a session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
