"""Database configuration and session management module.

Supports async SQLite (default zero-config) and async PostgreSQL.
"""

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config.settings import settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Determine database URL
db_url = settings.database_url
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Default to SQLite if Postgres connection string is placeholder
if "user:password@localhost" in db_url:
    db_file = Path(__file__).parent.parent.parent / "resume_analyzer.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

log_url = db_url.split("@")[-1] if "@" in db_url else db_url
logger.info("Initializing database with engine URL: %s", log_url)

engine = create_async_engine(
    db_url,
    echo=settings.debug,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for FastAPI async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
