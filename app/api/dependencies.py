"""
Dependency Injection

Shared FastAPI dependencies for dependency injection.
"""

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.memory.application.services.fact_extractor_service import FactExtractorService
    from app.domains.memory.application.services.fact_searcher_service import FactSearcherService


@lru_cache()
def get_fact_repository():
    """Get FactRepository instance (singleton)"""
    from app.domains.memory.infrastructure.repositories.fact_repository_impl import FactRepository
    return FactRepository()


@lru_cache()
def get_fact_extractor_service() -> "FactExtractorService":
    """Get FactExtractorService instance (singleton)"""
    from app.domains.memory.application.services.fact_extractor_service import FactExtractorService
    repository = get_fact_repository()
    return FactExtractorService(fact_repository=repository)


@lru_cache()
def get_fact_searcher_service() -> "FactSearcherService":
    """Get FactSearcherService instance (singleton)"""
    from app.domains.memory.application.services.fact_searcher_service import FactSearcherService
    repository = get_fact_repository()
    return FactSearcherService(fact_repository=repository)
