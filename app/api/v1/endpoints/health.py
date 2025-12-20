"""
Health Check Endpoint

GET /api/v1/health
Kubernetes readiness/liveness probes.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.core.logging import logger

router = APIRouter()


@router.get("/live")
async def liveness():
    """
    Kubernetes liveness probe
    
    Returns 200 if application is alive.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness():
    """
    Kubernetes readiness probe
    
    Returns 200 if ready to accept traffic, 503 if not ready.
    """
    # TODO: Check database connections, cache, etc.
    try:
        # Placeholder checks
        checks = {
            "database": True,  # TODO: Check PostgreSQL
            "milvus": True,    # TODO: Check Milvus
            "neo4j": True,     # TODO: Check Neo4j
            "redis": True      # TODO: Check Redis
        }
        
        if all(checks.values()):
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": checks
            }
        else:
            raise HTTPException(
                status_code=503,
                detail="Service not ready",
                headers={"X-Reason": "Dependencies unavailable"}
            )
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("")
async def health():
    """
    Detailed health check for monitoring
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

