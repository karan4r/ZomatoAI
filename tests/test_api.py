"""
Tests for Phase 5 API (FastAPI endpoints).
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from zomato_ai.db import Base, get_engine, get_session_factory
from zomato_ai.models import Restaurant, RestaurantCuisine


def _setup_test_db(tmp_path):
    db_path = tmp_path / "test_phase5.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    engine = get_engine()
    Base.metadata.create_all(engine)

    session_factory = get_session_factory()
    with session_factory() as session:
        r1 = Restaurant(
            name="API Test Restaurant",
            location="Banashankari",
            rest_type="Casual Dining",
            avg_rating=4.2,
            review_count=80,
            avg_cost_for_two=600,
            online_order=True,
            book_table=True,
        )
        r2 = Restaurant(
            name="Another Place",
            location="Banashankari",
            rest_type="Cafe",
            avg_rating=4.0,
            review_count=30,
            avg_cost_for_two=400,
            online_order=True,
            book_table=False,
        )
        session.add_all([r1, r2])
        session.flush()
        session.add_all([
            RestaurantCuisine(restaurant_id=r1.id, cuisine="North Indian"),
            RestaurantCuisine(restaurant_id=r2.id, cuisine="Chinese"),
        ])
        session.commit()
        ids = (r1.id, r2.id)
    return db_path, ids


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    # Use DummyLLMClient in tests so we don't call Groq API
    monkeypatch.setenv("GROQ_API_KEY", "")
    _setup_test_db(tmp_path)
    from phase5.app import app
    return TestClient(app)


def test_health_returns_ok(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]


def test_recommendations_endpoint(api_client):
    response = api_client.post(
        "/recommendations",
        json={
            "place": "Banashankari",
            "min_rating": 3.5,
            "cuisines": ["North Indian"],
            "limit": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "meta" in data
    assert isinstance(data["recommendations"], list)
    if data["recommendations"]:
        r = data["recommendations"][0]
        assert "id" in r and "name" in r
        assert "summary_reason" in r or "rank" in r


def test_recommendations_validation(api_client):
    response = api_client.post(
        "/recommendations",
        json={"limit": 0},
    )
    assert response.status_code == 422


def test_restaurant_not_found(api_client):
    response = api_client.get("/restaurants/99999")
    assert response.status_code == 404


def test_restaurant_by_id(api_client, tmp_path):
    _, (r1_id, _) = _setup_test_db(tmp_path)
    from phase5.app import app
    client = TestClient(app)
    response = client.get(f"/restaurants/{r1_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == r1_id
    assert "name" in data
    assert "cuisines" in data


def test_feedback_endpoint(api_client):
    response = api_client.post(
        "/feedback",
        json={"restaurant_id": 42, "action": "liked", "user_id": "test"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}
