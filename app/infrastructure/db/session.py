"""
Database Session Management

SQLAlchemy async session factory and context manager for PostgreSQL.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logging import logger

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for ORM models
Base = declarative_base()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session
    
    Usage:
        async def my_endpoint(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database (create tables if they don't exist)"""
    try:
        # Import models here to avoid circular import
        # Models will register themselves with Base.metadata
        from app.infrastructure.db import models  # noqa: F401
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")

