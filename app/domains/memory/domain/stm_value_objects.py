"""
Short-Term Memory (STM) value objects for hierarchical session context.

Tiered structure:
- Tier 1 (Active Window): last N turns (full text)
- Tier 2 (Recent Summary): summarized window
- Tier 3 (Session Summary): ultra-compressed summary
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class STMMessage:
    """Single turn in a session."""
    session_id: str
    user_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if self.role not in {"user", "assistant", "system"}:
            raise ValueError("role must be one of user|assistant|system")
        if not self.content:
            raise ValueError("content cannot be empty")
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.user_id:
            raise ValueError("user_id cannot be empty")


@dataclass(frozen=True)
class ConversationTier:
    """
    A tier in STM hierarchy.
    - messages: raw turns (Tier 1) or supporting turns for summary (Tier 2/3)
    - summary: optional compressed summary text for Tier 2/3
    """
    messages: List[STMMessage] = field(default_factory=list)
    summary: Optional[str] = None


@dataclass(frozen=True)
class STMContext:
    """
    Aggregated STM context with 3 tiers:
    - tier1_active: last N turns (uncompressed)
    - tier2_recent: summarized mid-window
    - tier3_session: long-horizon summary
    """
    tier1_active: ConversationTier
    tier2_recent: ConversationTier
    tier3_session: ConversationTier

