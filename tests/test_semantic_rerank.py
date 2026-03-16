"""Tests for Phase 6 semantic re-ranking (stub)."""

import pytest
from zomato_ai.semantic_rerank import semantic_rerank


def test_semantic_rerank_returns_same_order():
    candidates = [
        {"id": 1, "name": "First"},
        {"id": 2, "name": "Second"},
    ]
    result = semantic_rerank(candidates, user_preference_summary="Italian", top_k=10)
    assert result == candidates


def test_semantic_rerank_respects_top_k():
    candidates = [{"id": i, "name": f"R{i}"} for i in range(10)]
    result = semantic_rerank(candidates, top_k=3)
    assert len(result) == 3
    assert result[0]["id"] == 0 and result[2]["id"] == 2
