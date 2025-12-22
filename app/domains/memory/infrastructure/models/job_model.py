"""
SQLAlchemy ORM model for Job entity.
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import Optional, Dict, Any

from app.infrastructure.database.postgres_session import Base


class JobModel(Base):
    """
    ORM model for jobs table.
    Maps to the Job domain entity.
    """
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    conversation_id = Column(String(256), nullable=True, index=True)
    status = Column(String(50), nullable=False, index=True)  # pending, processing, completed, failed
    progress = Column(Integer, default=0)
    current_step = Column(String(256), nullable=True)
    data = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "data": self.data,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

