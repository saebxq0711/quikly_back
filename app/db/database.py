from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from app.core.config import settings
from app.db.base import Base

engine = create_async_engine(
    settings.database_url,
    echo=True,
    pool_pre_ping=True,
    connect_args={
        "statement_cache_size": 0
    }
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

async def get_db():
    async with SessionLocal() as session:
        yield session