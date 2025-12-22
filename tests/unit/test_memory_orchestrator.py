import asyncio
import pytest

from app.domains.memory.application.services.memory_orchestrator import (
    MemoryOrchestrator,
)
from app.domains.memory.domain.value_objects import SearchResult


class DummySTMService:
    async def get_context(self, session_id: str, user_id: str):
        class Ctx:
            tier1_active = type("tier", (), {"messages": []})
            tier2_recent = type("tier", (), {"summary": None})
            tier3_session = type("tier", (), {"summary": None})
        return Ctx()

    async def search(self, session_id, user_id, query):
        return []


class DummyMemoryService:
    async def search_memories(self, query):
        return [
            SearchResult(id="ltm1", score=0.8, content="User likes pizza", metadata={"source": "ltm"})
        ]


@pytest.mark.asyncio
async def test_orchestrator_merge_prefers_boost():
    stm = DummySTMService()
    ltm = DummyMemoryService()
    orch = MemoryOrchestrator(stm_service=stm, memory_service=ltm)

    results = await orch.search(user_id="u1", session_id="s1", query="pizza", limit=5)
    assert len(results) == 1
    assert results[0].content == "User likes pizza"
    assert results[0].score >= 0.8

