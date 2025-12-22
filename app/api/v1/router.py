"""
API v1 router - aggregates all v1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import memory, jobs

# Note: prefix is added in main.py (settings.API_V1_PREFIX = "/api/v1")
# So we don't add prefix here to avoid double prefix
router = APIRouter()

router.include_router(memory.router, tags=["memory"])
router.include_router(jobs.router, tags=["jobs"])
