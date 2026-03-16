import pytest

from zomato_ai.config import get_groq_api_key
from zomato_ai.llm_orchestrator import generate_llm_recommendations, DummyLLMClient
from zomato_ai.preferences import Preference, PriceRange
from zomato_ai.groq_client import GroqLLMClient


def test_generate_llm_recommendations_respects_ranking_and_enriches():
    """
    Ensure Phase 3 LLM orchestration:
    - Uses the LLM-provided ranking (here DummyLLMClient).
    - Returns enriched recommendation dicts with reasons and ranks.
    """
    pref = Preference(
        place="Banashankari",
        price_range=PriceRange(min=300, max=900),
        min_rating=3.5,
        cuisines=["North Indian"],
    )

    # Pretend these came from Phase 2 get_recommendations
    candidates = [
        {
            "id": 1,
            "name": "Jalsa",
            "location": "Banashankari",
            "rest_type": "Casual Dining",
            "avg_rating": 4.5,
            "review_count": 100,
            "avg_cost_for_two": 800,
            "online_order": True,
            "book_table": True,
            "cuisines": ["north indian", "mughlai"],
            "score": 0.9,
        },
        {
            "id": 2,
            "name": "Spice Elephant",
            "location": "Banashankari",
            "rest_type": "Casual Dining",
            "avg_rating": 4.0,
            "review_count": 50,
            "avg_cost_for_two": 700,
            "online_order": True,
            "book_table": False,
            "cuisines": ["chinese", "north indian"],
            "score": 0.8,
        },
    ]

    client = DummyLLMClient()
    final = generate_llm_recommendations(pref, candidates, limit=2, client=client)

    assert len(final) == 2

    # Jalsa should be first due to higher score
    assert final[0]["name"] == "Jalsa"
    assert final[0]["rank"] == 1
    assert isinstance(final[0].get("summary_reason"), str)
    assert final[0]["best_for"] == ["general dining"]

    assert final[1]["name"] == "Spice Elephant"
    assert final[1]["rank"] == 2


@pytest.mark.skipif(not get_groq_api_key(), reason="GROQ_API_KEY not set")
@pytest.mark.integration
def test_groq_integration_returns_recommendations():
    """
    Integration test: call real Groq API when GROQ_API_KEY is set.
    Verifies GroqLLMClient returns valid structure and enrichments.
    """
    pref = Preference(
        place="Banashankari",
        price_range=PriceRange(min=300, max=900),
        min_rating=3.0,
        cuisines=["North Indian"],
    )
    candidates = [
        {
            "id": 101,
            "name": "Test Restaurant A",
            "location": "Banashankari",
            "avg_rating": 4.2,
            "avg_cost_for_two": 600,
            "cuisines": ["north indian"],
            "score": 0.85,
        },
        {
            "id": 102,
            "name": "Test Restaurant B",
            "location": "Banashankari",
            "avg_rating": 4.0,
            "avg_cost_for_two": 500,
            "cuisines": ["north indian", "chinese"],
            "score": 0.75,
        },
    ]
    client = GroqLLMClient()
    final = generate_llm_recommendations(pref, candidates, limit=2, client=client)
    assert len(final) >= 1
    for r in final:
        assert "id" in r and "name" in r
        assert "rank" in r
        assert "summary_reason" in r
        assert "best_for" in r
        assert r["id"] in (101, 102)

