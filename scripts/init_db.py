"""
Database Initialization Script

Manually create database tables if they don't exist.
Can be used instead of auto-create on startup.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.db.session import init_db, close_db
from app.core.logging import setup_logging

logger = setup_logging()


async def main():
    """Initialize database tables"""
    try:
        logger.info("Initializing database tables...")
        await init_db()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())

