"""
Database Connection Pool Setup

Alternative approach using asyncpg directly (if not using SQLAlchemy).
"""

from typing import Optional
import asyncpg
from asyncpg import Pool

from app.core.config import settings
from app.core.logging import logger


class Database:
    """Database connection pool manager"""
    
    def __init__(self):
        self.pool: Optional[Pool] = None
    
    async def ensure_database(self):
        """Ensure database exists, create if it doesn't"""
        try:
            # Connect to default 'postgres' database to check/create target database
            conn = await asyncpg.connect(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database='postgres',  # Connect to default database
            )
            
            try:
                # Check if database exists
                db_exists = await conn.fetchval(
                    "SELECT 1 FROM pg_database WHERE datname = $1",
                    settings.POSTGRES_DB
                )
                
                if not db_exists:
                    logger.info(f"Database '{settings.POSTGRES_DB}' does not exist, creating...")
                    # Create database (must be outside transaction)
                    await conn.execute(
                        f'CREATE DATABASE "{settings.POSTGRES_DB}"'
                    )
                    logger.info(f"Database '{settings.POSTGRES_DB}' created successfully")
                else:
                    logger.info(f"Database '{settings.POSTGRES_DB}' already exists")
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Failed to ensure database exists: {e}")
            raise
    
    async def connect(self):
        """Create connection pool"""
        try:
            # First, ensure database exists (if enabled)
            if settings.AUTO_CREATE_DB:
                await self.ensure_database()
            
            # Then create connection pool to the target database
            self.pool = await asyncpg.create_pool(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                min_size=5,
                max_size=20,
                command_timeout=60,
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def fetch(self, query: str, *args):
        """Execute SELECT query and fetch all rows"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """Execute SELECT query and fetch one row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """Execute SELECT query and fetch one value"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute(self, query: str, *args):
        """Execute INSERT/UPDATE/DELETE query"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)


# Global database instance
db = Database()

