"""
PostgreSQL ORM Models

SQLAlchemy models for PostgreSQL database.
"""

from sqlalchemy import Column, String, Float, Integer, BigInteger, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.infrastructure.db.session import Base


class UserModel(Base):
    """User metadata model"""
    __tablename__ = "users"
    
    id = Column(String(100), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    total_conversations = Column(Integer, default=0)
    total_facts = Column(Integer, default=0)
    meta_data = Column(JSON, default={})  # Renamed from 'metadata' (reserved in SQLAlchemy)


class ConversationModel(Base):
    """Conversation metadata model"""
    __tablename__ = "conversations"
    
    id = Column(String(100), primary_key=True)
    user_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    message_count = Column(Integer, nullable=False)
    facts_extracted = Column(Integer, default=0)
    raw_conversation = Column(JSON, nullable=False)
    meta_data = Column(JSON, default={})  # Renamed from 'metadata' (reserved in SQLAlchemy)


class FactMetadataModel(Base):
    """Fact metadata model"""
    __tablename__ = "facts_metadata"
    
    fact_id = Column(String(100), primary_key=True)
    user_id = Column(String(100), nullable=False, index=True)
    conversation_id = Column(String(100), index=True)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    milvus_id = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    accessed_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True))
    meta_data = Column(JSON, default={})  # Renamed from 'metadata' (reserved in SQLAlchemy)

