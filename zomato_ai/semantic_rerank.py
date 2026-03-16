"""
Phase 6 – Semantic re-ranking (stub).

Re-ranks candidate restaurants. Current implementation is a no-op (identity);
a future version can use embeddings and similarity to user query.
"""

from __future__ import annotations

from typing import Any, List


def semantic_rerank(
    candidates: List[dict],
    user_preference_summary: str = "",
    top_k: int = 20,
) -> List[dict]:
    """
    Optionally re-rank candidates by semantic similarity to user preference.

    Stub: returns the same list in the same order. Replace with
    embedding-based similarity (e.g. sentence-transformers) when needed.
    """
    return list(candidates[:top_k])
