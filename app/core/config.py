"""
Configuration Management

Uses Pydantic BaseSettings for environment variable management
with type validation and auto-completion.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field, computed_field
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "PIKA Memory API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    # Store as string to prevent auto JSON parsing, then convert to list via property
    CORS_ORIGINS_STR: str = Field(default="*", validation_alias="CORS_ORIGINS")
    
    @field_validator("CORS_ORIGINS_STR", mode="before")
    @classmethod
    def parse_cors_origins_str(cls, v):
        """Parse CORS_ORIGINS from env (supports comma-separated or JSON)"""
        # If None or empty, return default
        if not v or (isinstance(v, str) and not v.strip()):
            return "*"
        
        # If already a list (shouldn't happen but handle it)
        if isinstance(v, list):
            return ",".join(str(origin) for origin in v)
        
        # Must be a string
        if not isinstance(v, str):
            return "*"
        
        return v.strip()
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Get CORS origins as list"""
        v = self.CORS_ORIGINS_STR
        
        # Handle single asterisk
        if v == "*":
            return ["*"]
        
        # Try JSON first
        try:
            import json
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return [str(origin) for origin in parsed if origin]
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Fallback to comma-separated
        origins = [origin.strip() for origin in v.split(",") if origin.strip()]
        return origins if origins else ["*"]
    
    # Database - PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "pika_mem0"
    POSTGRES_URL: str = ""
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        if self.POSTGRES_URL:
            return self.POSTGRES_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Milvus (Vector Store)
    MILVUS_HOST: str = "124.197.21.40"
    MILVUS_PORT: int = 19530  # Default Milvus gRPC port (8000 is HTTP API port)
    MILVUS_COLLECTION_NAME: str = "user_facts"
    MILVUS_USER: Optional[str] = None  # Milvus username (if authentication required)
    MILVUS_PASSWORD: Optional[str] = None  # Milvus password (if authentication required)
    MILVUS_TIMEOUT: int = 30  # Connection timeout in seconds (increased for slow networks)
    
    # Neo4j (Graph Store)
    NEO4J_URI: str = "bolt://124.197.21.40:8687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "mem0graph"
    
    # Redis (Cache)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None  # Redis password (if required)
    REDIS_USERNAME: Optional[str] = None  # Redis username (optional, for Redis 6+ ACL)
    REDIS_URL: Optional[str] = None  # Full Redis URL (overrides individual settings)
    
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL with optional authentication"""
        if self.REDIS_URL:
            return self.REDIS_URL
        
        # Build URL with authentication if provided
        if self.REDIS_PASSWORD:
            if self.REDIS_USERNAME:
                # Format: redis://username:password@host:port/db
                return f"redis://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            else:
                # Format: redis://:password@host:port/db
                return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            # No password: redis://host:port/db
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # OpenAI API
    OPENAI_API_KEY: str = ""
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_LLM_MODEL: str = "gpt-4o-mini"
    
    # Security
    API_KEY_SECRET: str = ""  # For API key hashing
    JWT_SECRET: str = ""  # If needed for admin panel
    ENCRYPTION_KEY: str = ""  # For data encryption at rest
    
    # Performance
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT: int = 30
    
    # Search Optimization
    USE_HYBRID_SEARCH: bool = True  # Enable hybrid search (vector + keyword)
    HYBRID_VECTOR_WEIGHT: float = 0.7  # Weight for vector search (0.0-1.0)
    HYBRID_KEYWORD_WEIGHT: float = 0.3  # Weight for keyword search (0.0-1.0)
    USE_GPU_ACCELERATION: bool = False  # Enable GPU acceleration for Milvus (requires GPU)
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    # Database Auto-Initialization
    AUTO_CREATE_DB: bool = True  # Auto-create database if it doesn't exist
    AUTO_CREATE_TABLES: bool = True  # Auto-create tables on startup if they don't exist
    
    # Optional Services (skip if unavailable)
    REDIS_REQUIRED: bool = False  # If False, app will continue even if Redis is unavailable
    MILVUS_REQUIRED: bool = True  # If False, app will continue even if Milvus is unavailable
    NEO4J_REQUIRED: bool = True  # If False, app will continue even if Neo4j is unavailable
    
    # Legacy/Docker variables (not used by Settings but may exist in .env)
    # These are ignored to avoid validation errors
    WORKERS: Optional[str] = None  # Used by docker-compose.yml for uvicorn workers
    MEM0_API_KEY: Optional[str] = None  # Legacy mem0ai package
    MEM0_ORG_ID: Optional[str] = None  # Legacy mem0ai package
    MEM0_PROJECT_ID: Optional[str] = None  # Legacy mem0ai package
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        # Don't auto-parse JSON for complex types, let validator handle it
        env_parse_none_str="",
        # Allow extra fields from .env that we don't use
        extra="ignore",
    )


# Global settings instance
settings = Settings()

