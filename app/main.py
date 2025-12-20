"""
FastAPI Application Entry Point

Creates and configures the FastAPI application with all routers, middleware,
and lifecycle events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.infrastructure.db.connection import db
from app.infrastructure.db.session import init_db
from app.infrastructure.cache.client import cache
from app.infrastructure.search.milvus_client import milvus_client
from app.infrastructure.external.neo4j_client import neo4j_client

# Setup structured logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    
    - Startup: Initialize database connections, cache, etc.
    - Shutdown: Close connections, cleanup resources
    """
    # Startup
    logger.info("Starting PIKA Memory System...")
    
    try:
        # Initialize database connections
        await db.connect()
        logger.info("Database connected")
        
        # Auto-create tables if enabled and they don't exist
        if settings.AUTO_CREATE_TABLES:
            try:
                await init_db()
            except Exception as e:
                logger.warning(f"Failed to auto-create tables (they may already exist): {e}")
                # Don't fail startup if tables already exist
        
        # Initialize cache (optional)
        try:
            await cache.connect()
            logger.info("Cache connected")
        except Exception as e:
            if settings.REDIS_REQUIRED:
                logger.error(f"Redis is required but connection failed: {e}")
                raise
            else:
                logger.warning(f"Redis connection failed (optional): {e}")
        
        # Initialize Milvus
        try:
            await milvus_client.connect()
            logger.info("Milvus connected")
        except Exception as e:
            if settings.MILVUS_REQUIRED:
                logger.error(f"Milvus is required but connection failed: {e}")
                raise
            else:
                logger.warning(f"Milvus connection failed (optional): {e}")
        
        # Initialize Neo4j
        try:
            await neo4j_client.connect()
            logger.info("Neo4j connected")
        except Exception as e:
            if settings.NEO4J_REQUIRED:
                logger.error(f"Neo4j is required but connection failed: {e}")
                raise
            else:
                logger.warning(f"Neo4j connection failed (optional): {e}")
        
        logger.info("PIKA Memory System started successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down PIKA Memory System...")
    
    try:
        await db.disconnect()
        await cache.disconnect()
        await milvus_client.disconnect()
        await neo4j_client.disconnect()
        logger.info("All connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="PIKA Memory API",
    description="Self-hosted long-term memory system for PIKA robot",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "PIKA Memory API",
        "version": "1.0.0",
        "status": "healthy"
    }
