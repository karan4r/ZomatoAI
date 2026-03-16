"""
End-to-end test: all phases connected (1 → 2 → 3 → 4 → 5 → 6).

Uses a temporary DB and fake dataset. Verifies:
- Phase 1: ingestion populates DB
- Phase 2: get_recommendations returns candidates from that data
- Phase 3: generate_llm_recommendations enriches them (DummyLLM in test)
- Phase 4: health_check and metrics work
- Phase 5: API POST /recommendations and GET /health return correctly
- Phase 6: feedback can be recorded and semantic_rerank stub runs
"""

import pytest
from fastapi.testclient import TestClient
from datasets import Dataset

from zomato_ai.observability import get_metrics, health_check, reset_metrics
from zomato_ai.ingest import run_ingestion
from zomato_ai.preferences import Preference, PriceRange
from zomato_ai.recommendation import get_recommendations
from zomato_ai.llm_orchestrator import generate_llm_recommendations
from zomato_ai.semantic_rerank import semantic_rerank


def _fake_dataset():
    return Dataset.from_dict({
        "name": ["E2E Restaurant A", "E2E Restaurant B"],
        "address": ["Addr 1", "Addr 2"],
        "location": ["Bangalore", "Bangalore"],
        "rate": ["4.2/5", "4.0/5"],
        "votes": [50, 30],
        "approx_cost(for two people)": ["600", "500"],
        "online_order": ["Yes", "Yes"],
        "book_table": ["No", "No"],
        "cuisines": ["North Indian", "Chinese, North Indian"],
        "rest_type": ["Casual", "Cafe"],
        "url": [None, None],
    })


@pytest.fixture
def e2e_db(tmp_path, monkeypatch):
    db_path = tmp_path / "e2e.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("GROQ_API_KEY", "")  # use DummyLLM for reproducible E2E
    return db_path


def test_e2e_phase1_ingestion_then_phase2_recommendations(e2e_db):
    # Phase 1: ingest
    count = run_ingestion(hf_dataset=_fake_dataset())
    assert count == 2

    # Phase 2: recommend from that data
    pref = Preference(place="Bangalore", min_rating=4.0, cuisines=["North Indian"])
    candidates = get_recommendations(pref, limit=5)
    assert len(candidates) >= 1
    assert all("id" in c and "name" in c and "score" in c for c in candidates)


def test_e2e_phase2_to_phase3_llm_enrichment(e2e_db):
    run_ingestion(hf_dataset=_fake_dataset())
    pref = Preference(place="Bangalore", min_rating=3.0)
    candidates = get_recommendations(pref, limit=5)
    assert len(candidates) >= 1

    # Phase 3: LLM (DummyLLM when no Groq key)
    final = generate_llm_recommendations(pref, candidates, limit=3)
    assert len(final) >= 1
    for r in final:
        assert "summary_reason" in r and "rank" in r and "best_for" in r


def test_e2e_phase4_health_and_metrics(e2e_db):
    run_ingestion(hf_dataset=_fake_dataset())
    # Phase 4: health
    result = health_check(check_database=True, check_groq_config=True)
    assert result["status"] in ("ok", "degraded")
    assert "database" in result["checks"]
    # Phase 4: metrics (after a recommendation would be recorded by API)
    reset_metrics()
    m = get_metrics()
    assert "recommendation_requests_total" in m


def test_e2e_phase5_api_full_flow(e2e_db):
    run_ingestion(hf_dataset=_fake_dataset())
    from phase5.app import app
    client = TestClient(app)

    # Health
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["checks"]["database"] == "ok"

    # Recommendations
    r = client.post(
        "/recommendations",
        json={
            "place": "Bangalore",
            "min_rating": 3.0,
            "cuisines": ["North Indian", "Chinese"],
            "limit": 3,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "recommendations" in data and "meta" in data
    assert isinstance(data["recommendations"], list)

    # Feedback (Phase 6)
    r = client.post("/feedback", json={"restaurant_id": 1, "action": "liked"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_e2e_phase6_semantic_rerank_stub():
    candidates = [{"id": 1, "name": "X"}, {"id": 2, "name": "Y"}]
    out = semantic_rerank(candidates, user_preference_summary="Italian", top_k=2)
    assert out == candidates
