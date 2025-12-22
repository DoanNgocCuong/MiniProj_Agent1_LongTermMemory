"""
Core configuration module using Pydantic Settings.
Loads configuration from environment variables with validation.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import Optional, Union
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "PIKA Memory System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    # Toggle to decide extraction mode:
    # - True: use async worker + RabbitMQ (default, production)
    # - False: run extract_facts inline in API process (for debugging worker issues)
    USE_ASYNC_WORKER_FOR_EXTRACTION: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: Union[str, list[str]] = ["*"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from string (JSON or comma-separated) to list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try JSON first
            if v.strip().startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fallback to comma-separated
            if "," in v:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
            # Single value
            return [v.strip()] if v.strip() else ["*"]
        return ["*"]
    
    # PostgreSQL
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_POOL_SIZE: int = 10
    POSTGRES_MAX_OVERFLOW: int = 20
    
    @model_validator(mode="before")
    @classmethod
    def map_postgres_username(cls, data: dict) -> dict:
        """Map POSTGRES_USERNAME to POSTGRES_USER if needed."""
        if isinstance(data, dict):
            # Handle POSTGRES_USERNAME from .env
            if "POSTGRES_USERNAME" in data and not data.get("POSTGRES_USER"):
                data["POSTGRES_USER"] = data["POSTGRES_USERNAME"]
        return data
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL database URL."""
        if not self.POSTGRES_USER:
            raise ValueError("POSTGRES_USER or POSTGRES_USERNAME must be set")
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 50
    
    # RabbitMQ
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_DEFAULT_USER: str = "guest"
    RABBITMQ_DEFAULT_PASS: str = "guest"
    # Support alternative naming
    RABBITMQ_USERNAME: Optional[str] = None
    RABBITMQ_PASSWORD: Optional[str] = None
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_EXTRACTION_QUEUE: str = "memory_extraction"
    RABBITMQ_EXCHANGE: Optional[str] = None
    RABBITMQ_QUEUE: Optional[str] = None
    RABBITMQ_PREFETCH_COUNT: int = 1
    NUMBER_WORKER_RABBITMQ: int = 5
    
    @property
    def RABBITMQ_USER(self) -> str:
        """Get RabbitMQ username, preferring RABBITMQ_USERNAME over RABBITMQ_DEFAULT_USER."""
        return self.RABBITMQ_USERNAME or self.RABBITMQ_DEFAULT_USER
    
    @property
    def RABBITMQ_PASS(self) -> str:
        """Get RabbitMQ password, preferring RABBITMQ_PASSWORD over RABBITMQ_DEFAULT_PASS."""
        return self.RABBITMQ_PASSWORD or self.RABBITMQ_DEFAULT_PASS
    
    @property
    def RABBITMQ_QUEUE_NAME(self) -> str:
        """Get RabbitMQ queue name, preferring RABBITMQ_QUEUE over RABBITMQ_EXTRACTION_QUEUE."""
        return self.RABBITMQ_QUEUE or self.RABBITMQ_EXTRACTION_QUEUE
    
    # Mem0 OSS Configuration (không cần API key)
    MEM0_USE_OSS: bool = True  # Set to False để dùng Enterprise API
    
    # Mem0 Enterprise API (chỉ dùng khi MEM0_USE_OSS=False)
    MEM0_API_KEY: Optional[str] = None
    MEM0_ORG_ID: Optional[str] = None
    MEM0_PROJECT_ID: Optional[str] = None
    
    # Mem0 OSS - Vector Store Configuration
    MEM0_VECTOR_STORE_PROVIDER: str = "milvus"  # Options: qdrant, chroma, pgvector, milvus
    MEM0_VECTOR_STORE_COLLECTION_NAME: str = "pika_memories"
    MEM0_VECTOR_STORE_HOST: str = "localhost"
    MEM0_VECTOR_STORE_PORT: int = 6333  # Qdrant default (19530 for Milvus)
    # Generic vector store overrides / credentials
    # For providers that use a single URL (e.g. Milvus url="http://host:port" or "./milvus.db")
    MEM0_VECTOR_STORE_URL: Optional[str] = None
    # For Milvus production mode (token = "user:password")
    MEM0_VECTOR_STORE_USER: Optional[str] = None
    MEM0_VECTOR_STORE_PASSWORD: Optional[str] = None
    
    # Mem0 OSS - LLM Configuration
    MEM0_LLM_PROVIDER: str = "openai"  # Options: openai, ollama, litellm, groq, together
    MEM0_LLM_MODEL: str = "gpt-4o-mini"
    MEM0_LLM_API_KEY: Optional[str] = None  # Will use OPENAI_API_KEY if not set
    
    # Mem0 OSS - Embedder Configuration
    MEM0_EMBEDDER_PROVIDER: str = "openai"  # Options: openai, huggingface, ollama, azure_openai
    MEM0_EMBEDDER_MODEL: str = "text-embedding-3-small"
    MEM0_EMBEDDER_API_KEY: Optional[str] = None  # Will use OPENAI_API_KEY if not set
    
    # Mem0 OSS - Graph Store (optional, for v1.1)
    MEM0_GRAPH_STORE_ENABLED: bool = False
    MEM0_GRAPH_STORE_PROVIDER: str = "neo4j"
    # v1.1 được recommend trong docs mới, hỗ trợ tốt hơn cho Milvus/graph
    MEM0_VERSION: str = "v1.1"
    
    # Mem0 OSS - History Database
    MEM0_HISTORY_DB_PATH: Optional[str] = None  # Default: ~/.mem0/history.db
    
    # OpenAI (for embeddings)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Vector Store (Milvus/Qdrant)
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "pika_memories"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j"
    
    # Caching Configuration
    CACHE_L0_ENABLED: bool = True
    CACHE_L0_TTL: int = 0  # Request lifetime
    
    CACHE_L1_ENABLED: bool = True
    CACHE_L1_TTL: int = 3600  # 1 hour
    CACHE_L1_KEY_PREFIX: str = "search"
    
    CACHE_L2_ENABLED: bool = True
    CACHE_L2_TTL: int = 86400  # 24 hours
    
    CACHE_L3_ENABLED: bool = True
    CACHE_L3_TTL: int = 86400  # 24 hours (embedding cache)
    CACHE_L3_KEY_PREFIX: str = "embedding"
    
    # Proactive Caching
    PROACTIVE_CACHE_ENABLED: bool = True
    PROACTIVE_CACHE_INTERVAL_SECONDS: int = 1800  # 30 minutes
    PROACTIVE_CACHE_USER_FAVORITE_QUERY: str = "user favorite (movie, character, pet, activity, friend, music, travel, toy)"
    
    # Job Configuration
    JOB_TIMEOUT_SECONDS: int = 300  # 5 minutes
    JOB_MAX_RETRIES: int = 3
    
    # Performance
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT_SECONDS: int = 30
    
    # STM (Short-Term Memory) Configuration
    STM_TIER1_MAX_TURNS: int = 10  # Active window
    STM_TIER2_SUMMARY_TURNS: int = 40  # Turns to accumulate before summarizing into tier2
    STM_TIER3_SUMMARY_TURNS: int = 200  # Turns before promoting tier2 summary into tier3
    STM_REDIS_TTL_SECONDS: int = 3600  # TTL for STM conversation state in Redis
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env (like POSTGRES_USERNAME, API_KEY_SECRET, etc.)


# Global settings instance
settings = Settings()

