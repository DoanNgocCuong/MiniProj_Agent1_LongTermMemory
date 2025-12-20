"""
API v1 Router

Aggregates all v1 endpoints into a single router.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import extract, search, health, precompute


api_router = APIRouter(prefix="/v1", tags=["v1"])

# Include all endpoint routers
api_router.include_router(extract.router, prefix="/extract_facts", tags=["memory"])
api_router.include_router(search.router, prefix="/search_facts", tags=["memory"])
api_router.include_router(precompute.router, prefix="/precompute", tags=["optimization"])
api_router.include_router(health.router, prefix="/health", tags=["health"])

