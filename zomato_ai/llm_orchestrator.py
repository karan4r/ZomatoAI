from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Protocol, Optional

from .config import get_groq_api_key
from .preferences import Preference


class LLMClient(Protocol):
    """
    Protocol for an LLM client used by the orchestrator.

    Tests and demos can inject a fake client; a real Groq implementation
    can be added later that satisfies this interface.
    """

    def recommend(
        self,
        preference: Preference,
        candidates: List[Dict[str, Any]],
        limit: int,
    ) -> Dict[str, Any]:
        ...


@dataclass
class DummyLLMClient:
    """
    A simple in-process "LLM" used for testing and demos.

    It does not call any external service. Instead, it:
    - Sorts candidates by their existing `score` (fallback to 0.0).
    - Returns a JSON-like structure that mimics the expected Groq output.
    """

    def recommend(
        self,
        preference: Preference,
        candidates: List[Dict[str, Any]],
        limit: int,
    ) -> Dict[str, Any]:
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.get("score", 0.0),
            reverse=True,
        )
        top = sorted_candidates[:limit]

        recommendations = []
        for rank, c in enumerate(top, start=1):
            recommendations.append(
                {
                    "restaurant_id": c["id"],
                    "rank": rank,
                    "summary_reason": (
                        f"{c.get('name')} matches your preferences for "
                        f"{', '.join(c.get('cuisines', [])) or 'its cuisine'} "
                        f"in {c.get('location') or 'this area'}."
                    ),
                    "best_for": ["general dining"],
                }
            )

        return {"recommendations": recommendations}


def generate_llm_recommendations(
    preference: Preference,
    candidates: List[Dict[str, Any]],
    limit: int = 5,
    client: Optional[LLMClient] = None,
) -> List[Dict[str, Any]]:
    """
    Phase 3 entrypoint: call an LLM client with preference + candidates and
    interpret the structured response into a final ordered list.

    Parameters
    ----------
    preference:
        The user's structured preference.
    candidates:
        List of candidate restaurant dicts, typically produced by the Phase 2
        recommendation engine.
    limit:
        Maximum number of recommendations from the LLM.
    client:
        Optional custom LLM client. If None, DummyLLMClient is used.
    """
    if client is None:
        if get_groq_api_key():
            from .groq_client import GroqLLMClient
            client = GroqLLMClient()
        else:
            client = DummyLLMClient()

    if not candidates:
        return []

    raw = client.recommend(preference, candidates, limit)
    recs = raw.get("recommendations") or []

    # Index candidates by ID for quick lookup
    candidate_by_id = {c["id"]: c for c in candidates}

    final: List[Dict[str, Any]] = []
    for item in recs:
        rid = item.get("restaurant_id")
        if rid not in candidate_by_id:
            continue
        base = candidate_by_id[rid].copy()
        base["rank"] = item.get("rank")
        base["summary_reason"] = item.get("summary_reason")
        base["best_for"] = item.get("best_for", [])
        final.append(base)

    # Ensure ordering by rank if provided
    final.sort(key=lambda x: x.get("rank", 0))
    return final

