"""
Cache Infrastructure - Multi-layer caching system.

This package implements a 5-layer caching strategy:
- L0: Session cache (in-memory, request-scoped)
- L1: Redis cache (distributed, fast access)
- L2: Materialized views (PostgreSQL, pre-computed queries)
- L3: Embedding cache (vector similarity cache)
- Proactive cache: Predictive caching for common queries

Caching layers work together to optimize response times and reduce
load on downstream services (Mem0, vector stores, databases).
"""
