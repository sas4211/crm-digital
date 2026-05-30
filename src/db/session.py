"""
Async SQLAlchemy session factory.
"""

import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import SQLAlchemyError

if os.environ.get("VERCEL"):
    DEFAULT_SQLITE_URL = "sqlite+aiosqlite:////tmp/crm_digital.db"
else:
    DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///./crm_digital.db"

DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_SQLITE_URL)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

def get_engine(url):
    return create_async_engine(url, echo=False, pool_pre_ping=True)

engine = get_engine(DATABASE_URL)
_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def AsyncSessionLocal():
    return _session_factory()

async def get_db() -> AsyncSession:
    """FastAPI dependency — yields a DB session."""
    global engine, _session_factory
    try:
        async with _session_factory() as session:
            yield session
    except (SQLAlchemyError, ConnectionRefusedError):
        # Fallback to SQLite if primary DB fails
        if DATABASE_URL != DEFAULT_SQLITE_URL:
            print(f"WARNING: Connection to {DATABASE_URL} failed. Falling back to SQLite.")
            engine = get_engine(DEFAULT_SQLITE_URL)
            _session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with _session_factory() as session:
                yield session
        else:
            raise

async def init_db() -> None:
    """Create all tables (dev only — use Alembic in production)."""
    global engine, _session_factory
    from src.db.models import Base
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except (SQLAlchemyError, Exception) as e:
        if DATABASE_URL != DEFAULT_SQLITE_URL:
            print(f"ERROR: Could not initialize {DATABASE_URL}: {e}")
            print(f"INFO: Falling back to SQLite at {DEFAULT_SQLITE_URL}")
            engine = get_engine(DEFAULT_SQLITE_URL)
            _session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            raise
