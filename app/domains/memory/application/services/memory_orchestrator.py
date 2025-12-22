"""
Memory Orchestrator
- Executes STM and LTM searches in parallel
- Merges and ranks results with STM recency bonus
"""
import asyncio
from typing import List, Tuple

from app.domains.memory.application.services.stm_service import STMService
from app.domains.memory.application.services.memory_service import MemoryService
from app.domains.memory.domain.value_objects import SearchQuery, SearchResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class MemoryOrchestrator:
    def __init__(
        self,
        stm_service: STMService,
        memory_service: MemoryService,
        stm_timeout: float = 1.0,
        ltm_timeout: float = 1.5,
    ):
        self.stm_service = stm_service
        self.memory_service = memory_service
        self.stm_timeout = stm_timeout
        self.ltm_timeout = ltm_timeout

    async def search(self, user_id: str, session_id: str, query: str, limit: int = 10) -> List[SearchResult]:
        """Search STM + LTM in parallel and merge results."""
        stm_task = self._search_stm(session_id, user_id, query)
        ltm_task = self._search_ltm(user_id, query, limit)

        stm_results, ltm_results = await asyncio.gather(stm_task, ltm_task)
        merged = self._merge_and_rank(stm_results, ltm_results)
        return merged[:limit]

    async def _search_stm(self, session_id: str, user_id: str, query: str) -> List[SearchResult]:
        try:
            ctx = await asyncio.wait_for(self.stm_service.get_context(session_id, user_id), timeout=self.stm_timeout)
            # Simple STM search: match query substring in tier1 messages; fallback to summaries
            results: List[SearchResult] = []
            for msg in ctx.tier1_active.messages:
                if query.lower() in msg.content.lower():
                    results.append(
                        SearchResult(
                            id=f"stm_{hash(msg.content)}",
                            score=0.8,
                            content=msg.content,
                            metadata={"source": "stm", "role": msg.role},
                        )
                    )
            # Add summaries as low-confidence facts
            for summary_text, tag, score in [
                (ctx.tier2_recent.summary, "stm_tier2", 0.6),
                (ctx.tier3_session.summary, "stm_tier3", 0.5),
            ]:
                if summary_text:
                    results.append(
                        SearchResult(
                            id=f"{tag}_{hash(summary_text)}",
                            score=score,
                            content=summary_text,
                            metadata={"source": "stm_summary"},
                        )
                    )
            return results
        except Exception as e:
            logger.warning(f"STM search failed: {e}")
            return []

    async def _search_ltm(self, user_id: str, query: str, limit: int) -> List[SearchResult]:
        try:
            sq = SearchQuery(query=query, user_id=user_id, limit=limit)
            return await asyncio.wait_for(self.memory_service.search_memories(sq), timeout=self.ltm_timeout)
        except Exception as e:
            logger.warning(f"LTM search failed: {e}")
            return []

    def _merge_and_rank(
        self, stm_results: List[SearchResult], ltm_results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Merge STM + LTM:
        - Deduplicate by content hash
        - Boost if appears in both
        - STM gets small recency bonus
        """
        merged = {}

        def key(res: SearchResult) -> str:
            return str(hash(res.content.lower()))

        for res in ltm_results:
            merged[key(res)] = res

        for res in stm_results:
            k = key(res)
            if k in merged:
                # boost if present in both STM & LTM
                existing = merged[k]
                boosted = min(1.0, max(existing.score, res.score) + 0.1)
                merged[k] = SearchResult(
                    id=existing.id,
                    score=boosted,
                    content=existing.content,
                    metadata={**existing.metadata, "stm_overlap": True},
                )
            else:
                # STM recency bonus
                merged[k] = SearchResult(
                    id=res.id,
                    score=min(1.0, res.score + 0.05),
                    content=res.content,
                    metadata=res.metadata,
                )

        # Sort by score desc
        return sorted(merged.values(), key=lambda r: r.score, reverse=True)

