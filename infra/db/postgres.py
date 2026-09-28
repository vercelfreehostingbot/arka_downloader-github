"""Async PostgreSQL infrastructure; opt-in via DATABASE_URL."""
from __future__ import annotations
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

_engine: AsyncEngine | None = None
_factory: async_sessionmaker[AsyncSession] | None = None


def database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


def enabled() -> bool:
    return bool(database_url())


def init() -> None:
    global _engine, _factory
    if not enabled() or _engine is not None:
        return
    _engine = create_async_engine(
        database_url(),
        pool_pre_ping=True,
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_recycle=1800,
    )
    _factory = async_sessionmaker(_engine, expire_on_commit=False)

@asynccontextmanager
async def session() -> AsyncIterator[AsyncSession]:
    if _factory is None:
        raise RuntimeError("PostgreSQL is not enabled; set DATABASE_URL")
    async with _factory() as db:
        yield db

async def ping() -> bool:
    """Return whether PostgreSQL accepts a lightweight connection."""
    if _engine is None:
        return False
    from sqlalchemy import text
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def close() -> None:
    global _engine, _factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _factory = None
