"""
STM Service: manages short-term conversation context with 3 tiers.

Tiering strategy (aligns with docs/Step 2 - Output 3 - Caching 5 lớp.md):
- Tier 1 (Active Window): last N turns (no compression)
- Tier 2 (Recent Summary): summarized chunk of previous turns
- Tier 3 (Session Summary): ultra-compressed long-horizon summary

Storage:
- Redis (reuse L1 connection) key: stm:{session_id}
- TTL controlled by settings.STM_REDIS_TTL_SECONDS

Note: Summarization here is placeholder (heuristic concatenation).
In production, replace _summarize_text with LLM call.
"""
import json
from typing import Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger
from app.domains.memory.domain.stm_value_objects import (
    STMMessage,
    ConversationTier,
    STMContext,
)
from app.infrastructure.cache.l1_redis_cache import get_l1_cache

logger = get_logger(__name__)


class STMService:
    def __init__(self):
        self.tier1_max_turns = settings.STM_TIER1_MAX_TURNS
        self.tier2_summary_turns = settings.STM_TIER2_SUMMARY_TURNS
        self.tier3_summary_turns = settings.STM_TIER3_SUMMARY_TURNS
        self.ttl_seconds = settings.STM_REDIS_TTL_SECONDS

    # ---------- Public API ----------
    async def add_message(self, session_id: str, user_id: str, role: str, content: str) -> None:
        """Append a message to STM, maintaining tiered summaries."""
        msg = STMMessage(session_id=session_id, user_id=user_id, role=role, content=content)
        state = await self._load_state(session_id)
        state["tier1"].append(self._to_dict(msg))

        # Trim tier1 to max turns; move overflow to tier2 buffer
        overflow = max(0, len(state["tier1"]) - self.tier1_max_turns)
        if overflow > 0:
            moved = state["tier1"][:overflow]
            state["tier1"] = state["tier1"][overflow:]
            state["tier2_buffer"].extend(moved)

        # If tier2 buffer large enough, summarize into tier2 summary
        if len(state["tier2_buffer"]) >= self.tier2_summary_turns:
            summary_text = self._summarize_messages(state["tier2_buffer"])
            state["tier2_summary"] = self._merge_summaries(state["tier2_summary"], summary_text)
            state["tier2_buffer"] = []

        # If tier2 summary is large (based on number of summarized turns), promote to tier3
        if self._estimated_turns(state["tier2_summary"]) >= self.tier3_summary_turns:
            state["tier3_summary"] = self._merge_summaries(state["tier3_summary"], state["tier2_summary"])
            state["tier2_summary"] = ""

        await self._persist_state(session_id, state)

    async def get_context(self, session_id: str, user_id: str) -> STMContext:
        """Build STMContext for orchestrator/LLM."""
        state = await self._load_state(session_id)
        tier1_msgs = [self._from_dict(m) for m in state["tier1"]]
        tier2_msgs = [self._from_dict(m) for m in state["tier2_buffer"]]

        tier1 = ConversationTier(messages=tier1_msgs, summary=None)
        tier2 = ConversationTier(messages=tier2_msgs, summary=state["tier2_summary"] or None)
        tier3 = ConversationTier(messages=[], summary=state["tier3_summary"] or None)
        return STMContext(tier1_active=tier1, tier2_recent=tier2, tier3_session=tier3)

    # ---------- Internal helpers ----------
    async def _load_state(self, session_id: str) -> dict:
        cache = await get_l1_cache()
        key = f"stm:{session_id}"
        raw = await cache.get(key)
        if raw is None:
            return {"tier1": [], "tier2_buffer": [], "tier2_summary": "", "tier3_summary": ""}
        try:
            # cache.get already deserializes via CacheService, but ensure structure
            return raw
        except Exception as e:
            logger.warning(f"Failed to parse STM state, resetting. err={e}")
            return {"tier1": [], "tier2_buffer": [], "tier2_summary": "", "tier3_summary": ""}

    async def _persist_state(self, session_id: str, state: dict) -> None:
        cache = await get_l1_cache()
        key = f"stm:{session_id}"
        await cache.set(key, state, ttl=self.ttl_seconds)

    def _summarize_messages(self, messages: list) -> str:
        """
        Placeholder summarization: join trimmed messages.
        Replace with LLM summarization for production quality.
        """
        texts = []
        for msg in messages:
            content = msg.get("content", "")
            if content:
                texts.append(content.strip())
        if not texts:
            return ""
        # Keep it short: first 50 chars of each message, capped total
        joined = " ".join(t[:50] for t in texts)
        return joined[:500]

    def _merge_summaries(self, existing: str, new: str) -> str:
        if not existing:
            return new or ""
        if not new:
            return existing
        merged = f"{existing}\n{new}"
        # Trim to 1000 chars to avoid overgrowth
        return merged[:1000]

    def _estimated_turns(self, summary: str) -> int:
        # Heuristic: assume ~10 tokens per word, ~10 words per sentence (~100 chars)
        if not summary:
            return 0
        return max(1, len(summary) // 100)

    def _to_dict(self, msg: STMMessage) -> dict:
        return {
            "session_id": msg.session_id,
            "user_id": msg.user_id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }

    def _from_dict(self, data: dict) -> STMMessage:
        return STMMessage(
            session_id=data["session_id"],
            user_id=data["user_id"],
            role=data["role"],
            content=data["content"],
            # created_at optional parsing
        )

