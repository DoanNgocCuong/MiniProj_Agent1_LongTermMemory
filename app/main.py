"""
FastAPI application entry point.
Initializes app, middleware, and routes.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.v1.router import router as v1_router
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.error_handler import exception_handler
from app.infrastructure.database.postgres_session import init_db, close_db
from app.infrastructure.cache.l1_redis_cache import get_l1_cache
from app.infrastructure.cache.l2_materialized_view import L2MaterializedView
from app.infrastructure.database.postgres_session import get_db_session

# Setup logging
setup_logging(level="INFO" if not settings.DEBUG else "DEBUG", json_format=True)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting PIKA Memory System API...")
    
    try:
        # Initialize database
        await init_db()
        
        # Initialize L2 materialized view table
        async for db_session in get_db_session():
            await L2MaterializedView.create_table(db_session)
            break
        
        # Connect to Redis
        l1_cache = await get_l1_cache()
        logger.info("L1 Redis cache connected")
        
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down PIKA Memory System API...")
    
    try:
        # Disconnect from Redis
        l1_cache = await get_l1_cache()
        await l1_cache.disconnect()
        
        # Close database connections
        await close_db()
        
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="PIKA Memory System - Self-hosted Mem0 implementation",
    lifespan=lifespan,
)

# Add CORS middleware
# Parse CORS_ORIGINS - support both string and list
import json
cors_origins = settings.CORS_ORIGINS
if isinstance(cors_origins, str):
    try:
        # Try parsing as JSON array
        cors_origins = json.loads(cors_origins)
    except (json.JSONDecodeError, ValueError):
        # If not JSON, treat as comma-separated string
        cors_origins = [origin.strip() for origin in cors_origins.split(",")] if cors_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if isinstance(cors_origins, list) else [cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Add exception handlers
app.add_exception_handler(Exception, exception_handler)

# Include routers
app.include_router(v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }

