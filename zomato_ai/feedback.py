"""
Phase 6 – Feedback collection (in-memory stub).

Stores user feedback events for recommendations (e.g. clicked, liked, dismissed).
Can be extended to persist to DB or use for personalization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

# In-memory store (single process). For production, use DB or event store.
_events: List["FeedbackEvent"] = []


@dataclass
class FeedbackEvent:
    restaurant_id: int
    action: str  # e.g. "clicked", "liked", "dismissed", "booked"
    user_id: str = "anonymous"
    session_id: str = ""


def record_feedback(
    restaurant_id: int,
    action: str,
    user_id: str = "anonymous",
    session_id: str = "",
) -> None:
    """Record one feedback event."""
    _events.append(
        FeedbackEvent(
            restaurant_id=restaurant_id,
            action=action,
            user_id=user_id,
            session_id=session_id,
        )
    )


def get_feedback_events(limit: int = 100) -> List[FeedbackEvent]:
    """Return recent feedback events (for debugging or analytics)."""
    return list(_events[-limit:])


def clear_feedback() -> None:
    """Clear all stored events (for tests)."""
    _events.clear()
