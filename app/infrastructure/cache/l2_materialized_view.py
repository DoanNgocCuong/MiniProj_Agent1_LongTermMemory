"""
L2 Cache: PostgreSQL Materialized View for pre-computed user favorite summaries.
Provides fast access to frequently queried data.
"""
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import CacheError
from app.infrastructure.database.postgres_session import Base

logger = get_logger(__name__)


class UserFavoriteSummaryModel(Base):
    """
    ORM model for user_favorite_summary table.
    Stores pre-computed favorite summaries for users.
    """
    __tablename__ = "user_favorite_summary"
    
    user_id = Column(String(255), primary_key=True, index=True)
    summary_json = Column(JSONB, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class L2MaterializedView:
    """
    L2 Materialized View Cache - Pre-computed results in PostgreSQL.
    Used for "user favorite" queries that are frequently accessed.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize L2 materialized view cache.
        
        Args:
            db_session: SQLAlchemy async session
        """
        self.enabled = settings.CACHE_L2_ENABLED
        self.db = db_session
    
    async def get_user_favorite_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user favorite summary from materialized view.
        
        Args:
            user_id: User ID
            
        Returns:
            Summary dictionary or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            stmt = select(UserFavoriteSummaryModel).where(
                UserFavoriteSummaryModel.user_id == user_id
            )
            result = await self.db.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                logger.debug(f"L2 cache HIT: user_id={user_id}")
                return model.summary_json
            logger.debug(f"L2 cache MISS: user_id={user_id}")
            return None
        except Exception as e:
            logger.warning(f"Error getting from L2 cache: {e}")
            return None
    
    async def set_user_favorite_summary(
        self,
        user_id: str,
        summary: Dict[str, Any],
    ) -> None:
        """
        Set user favorite summary in materialized view.
        
        Args:
            user_id: User ID
            summary: Summary dictionary to store
        """
        if not self.enabled:
            return
        
        try:
            # Use PostgreSQL UPSERT (INSERT ... ON CONFLICT UPDATE)
            stmt = (
                pg_insert(UserFavoriteSummaryModel)
                .values(
                    user_id=user_id,
                    summary_json=summary,
                    last_updated=datetime.utcnow(),
                )
                .on_conflict_do_update(
                    index_elements=["user_id"],
                    set_={
                        "summary_json": summary,
                        "last_updated": datetime.utcnow(),
                    },
                )
            )
            
            await self.db.execute(stmt)
            await self.db.commit()
            logger.debug(f"L2 cache SET: user_id={user_id}")
        except Exception as e:
            await self.db.rollback()
            logger.warning(f"Error setting L2 cache: {e}")
            # Don't raise - cache failures shouldn't break the app
    
    async def delete_user_favorite_summary(self, user_id: str) -> None:
        """
        Delete user favorite summary.
        
        Args:
            user_id: User ID
        """
        if not self.enabled:
            return
        
        try:
            from sqlalchemy import delete
            stmt = delete(UserFavoriteSummaryModel).where(
                UserFavoriteSummaryModel.user_id == user_id
            )
            await self.db.execute(stmt)
            await self.db.commit()
            logger.debug(f"L2 cache DELETE: user_id={user_id}")
        except Exception as e:
            await self.db.rollback()
            logger.warning(f"Error deleting from L2 cache: {e}")
    
    @staticmethod
    async def create_table(db_session: AsyncSession) -> None:
        """
        Create user_favorite_summary table if it doesn't exist.
        Should be called during database initialization.
        
        Args:
            db_session: SQLAlchemy async session
        """
        try:
            # asyncpg doesn't support multiple statements in one prepared statement
            # Execute each statement separately
            
            # 1. Create table
            create_table_sql = text("""
                CREATE TABLE IF NOT EXISTS user_favorite_summary (
                    user_id VARCHAR(255) PRIMARY KEY,
                    summary_json JSONB NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db_session.execute(create_table_sql)
            
            # 2. Create index on user_id
            create_index_user_id = text("""
                CREATE INDEX IF NOT EXISTS idx_user_favorite_summary_user_id 
                ON user_favorite_summary(user_id)
            """)
            await db_session.execute(create_index_user_id)
            
            # 3. Create index on last_updated
            create_index_last_updated = text("""
                CREATE INDEX IF NOT EXISTS idx_user_favorite_summary_last_updated 
                ON user_favorite_summary(last_updated)
            """)
            await db_session.execute(create_index_last_updated)
            
            await db_session.commit()
            logger.info("L2 materialized view table created successfully")
        except Exception as e:
            await db_session.rollback()
            logger.error(f"Error creating L2 materialized view table: {e}")
            raise CacheError(f"Failed to create L2 table: {e}") from e

