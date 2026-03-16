"""
Phase 5 – FastAPI application: /recommendations, /health, /restaurants/{id}.
Serves Phase 7 UI at / when phase7/ui/dist is present.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from zomato_ai.db import get_engine, get_session_factory
from zomato_ai.llm_orchestrator import generate_llm_recommendations
from zomato_ai.models import Restaurant
from zomato_ai.observability import (
    get_logger,
    get_metrics,
    health_check,
    record_recommendation_request,
)
from zomato_ai.preferences import Preference, PriceRange
from zomato_ai.recommendation import get_recommendations

from zomato_ai.feedback import record_feedback

from .schemas import (
    FeedbackRequest,
    RecommendationItem,
    RecommendationsRequest,
    RecommendationsResponse,
)

logger = get_logger("phase5.api")
app = FastAPI(title="ZomatoAI Recommendations API", version="0.1.0")


def _request_to_preference(req: RecommendationsRequest) -> Preference:
    pr = None
    if req.price_range is not None:
        pr = PriceRange(min=req.price_range.min, max=req.price_range.max)
    return Preference(
        place=req.place,
        price_range=pr,
        min_rating=req.min_rating,
        cuisines=req.cuisines or [],
        online_order=req.online_order,
        book_table=req.book_table,
        rest_type=req.rest_type,
    )


def _rec_to_item(r: Dict[str, Any]) -> RecommendationItem:
    return RecommendationItem(
        id=r["id"],
        name=r["name"],
        location=r.get("location"),
        cuisines=r.get("cuisines") or [],
        avg_rating=r.get("avg_rating"),
        avg_cost_for_two=r.get("avg_cost_for_two"),
        summary_reason=r.get("summary_reason"),
        best_for=r.get("best_for") or [],
        rank=r.get("rank"),
    )


@app.post("/recommendations", response_model=RecommendationsResponse)
def post_recommendations(body: RecommendationsRequest) -> RecommendationsResponse:
    """Get LLM-powered restaurant recommendations for the given preferences."""
    start = time.time()
    pref = _request_to_preference(body)
    try:
        candidates = get_recommendations(
            pref,
            limit=min(body.limit * 4, 50),
            candidate_limit=200,
        )
        final = generate_llm_recommendations(pref, candidates, limit=body.limit)
        elapsed = time.time() - start
        record_recommendation_request(elapsed, candidate_count=len(candidates), error=False)
        logger.info(
            "recommendations_ok",
            extra={"count": len(final), "candidates": len(candidates), "latency_sec": round(elapsed, 3)},
        )
        return RecommendationsResponse(
            recommendations=[_rec_to_item(r) for r in final],
            meta={
                "candidate_count": len(candidates),
                "latency_seconds": round(elapsed, 3),
            },
        )
    except Exception as e:
        record_recommendation_request(time.time() - start, candidate_count=0, error=True)
        logger.exception("recommendations_failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
def get_health() -> dict:
    """Health check: database and optional Groq config."""
    return health_check(check_database=True, check_groq_config=True)


@app.get("/metrics")
def get_metrics_endpoint() -> dict:
    """Return current observability metrics (for debugging)."""
    return get_metrics()


@app.post("/feedback")
def post_feedback(body: FeedbackRequest) -> dict:
    """Record user feedback for a recommendation (Phase 6)."""
    record_feedback(
        restaurant_id=body.restaurant_id,
        action=body.action,
        user_id=body.user_id,
        session_id=body.session_id,
    )
    return {"ok": True}


@app.get("/restaurants/{restaurant_id}")
def get_restaurant(restaurant_id: int) -> dict:
    """Fetch a single restaurant by ID."""
    session_factory = get_session_factory()
    with session_factory() as session:
        stmt = (
            select(Restaurant)
            .options(joinedload(Restaurant.cuisines))
            .where(Restaurant.id == restaurant_id)
        )
        r = session.execute(stmt).scalars().unique().first()
        if not r:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        cuisines = sorted([c.cuisine for c in r.cuisines if c.cuisine])
        return {
            "id": r.id,
            "name": r.name,
            "address": r.address,
            "location": r.location,
            "rest_type": r.rest_type,
            "avg_rating": r.avg_rating,
            "review_count": r.review_count,
            "avg_cost_for_two": r.avg_cost_for_two,
            "online_order": r.online_order,
            "book_table": r.book_table,
            "cuisines": cuisines,
            "source_url": r.source_url,
        }


# Phase 7: serve built UI when dist exists (single-server deployment)
_ui_dist = Path(__file__).resolve().parent.parent / "phase7" / "ui" / "dist"
if (_ui_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(_ui_dist), html=True), name="ui")
