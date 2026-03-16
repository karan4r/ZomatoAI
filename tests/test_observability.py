"""
Tests for Phase 4 observability: health checks, metrics, logging.
"""

import os
import tempfile
import pytest

from zomato_ai.observability import (
    get_logger,
    get_metrics,
    health_check,
    record_recommendation_request,
    record_llm_call,
    reset_metrics,
)


def test_get_logger_returns_logger_with_handler():
    logger = get_logger("test.observability")
    assert logger.name == "test.observability"
    assert logger.handlers


def test_health_check_database_ok(monkeypatch):
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
        result = health_check(check_database=True, check_groq_config=False)
        assert result["status"] == "ok"
        assert result["checks"]["database"] == "ok"
    finally:
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_health_check_database_fail(monkeypatch):
    # Use a path whose parent directory does not exist so DB connection fails
    monkeypatch.setenv("DATABASE_URL", "sqlite:///nonexistent_subdir_xyz/foo.db")
    result = health_check(check_database=True, check_groq_config=False)
    assert result["status"] == "degraded"
    assert "error" in result["checks"]["database"].lower()


def test_health_check_groq_config():
    result = health_check(check_database=False, check_groq_config=True)
    assert "checks" in result
    assert "groq_config" in result["checks"]
    assert result["checks"]["groq_config"] in ("ok", "missing")


def test_metrics_record_and_read():
    reset_metrics()
    record_recommendation_request(0.5, candidate_count=10, error=False)
    record_recommendation_request(0.2, candidate_count=5, error=True)
    record_llm_call(0.3, error=False)

    m = get_metrics()
    assert m["recommendation_requests_total"] == 2
    assert m["recommendation_requests_errors"] == 1
    assert m["recommendation_latency_seconds_sum"] == pytest.approx(0.7)
    assert m["recommendation_latency_seconds_avg"] == pytest.approx(0.35)
    assert m["llm_calls_total"] == 1
    assert m["llm_calls_errors"] == 0
    assert m["candidate_count_sum"] == 15
    assert m["candidate_count_avg"] == pytest.approx(7.5)


def test_reset_metrics():
    record_recommendation_request(1.0, candidate_count=3, error=False)
    reset_metrics()
    m = get_metrics()
    assert m["recommendation_requests_total"] == 0
    assert m["recommendation_latency_seconds_sum"] == 0.0
    assert m["candidate_count_sum"] == 0
