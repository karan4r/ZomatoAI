"""
Phase 4 – Hardening & Observability.

Provides structured logging, in-memory metrics, and health checks for
the recommendation pipeline (DB, config, optional LLM readiness).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from .config import get_database_url, get_groq_api_key


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger configured for structured-style logging.
    Callers can use logger.info("message", extra={"key": "value"}) for context.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# In-memory metrics (single process). For production, use Prometheus or similar.
_metrics: Dict[str, Any] = {
    "recommendation_requests_total": 0,
    "recommendation_requests_errors": 0,
    "recommendation_latency_seconds_sum": 0.0,
    "llm_calls_total": 0,
    "llm_calls_errors": 0,
    "llm_latency_seconds_sum": 0.0,
    "candidate_count_sum": 0,
}


def record_recommendation_request(
    latency_seconds: float,
    candidate_count: int = 0,
    error: bool = False,
) -> None:
    """Record one recommendation pipeline invocation."""
    _metrics["recommendation_requests_total"] += 1
    if error:
        _metrics["recommendation_requests_errors"] += 1
    _metrics["recommendation_latency_seconds_sum"] += latency_seconds
    _metrics["candidate_count_sum"] += candidate_count


def record_llm_call(latency_seconds: float, error: bool = False) -> None:
    """Record one LLM API call (e.g. Groq)."""
    _metrics["llm_calls_total"] += 1
    if error:
        _metrics["llm_calls_errors"] += 1
    _metrics["llm_latency_seconds_sum"] += latency_seconds


def get_metrics() -> Dict[str, Any]:
    """Return a snapshot of current metrics (for health endpoint or debugging)."""
    total = _metrics["recommendation_requests_total"]
    return {
        "recommendation_requests_total": _metrics["recommendation_requests_total"],
        "recommendation_requests_errors": _metrics["recommendation_requests_errors"],
        "recommendation_latency_seconds_sum": _metrics["recommendation_latency_seconds_sum"],
        "recommendation_latency_seconds_avg": (
            _metrics["recommendation_latency_seconds_sum"] / total
            if total else 0.0
        ),
        "llm_calls_total": _metrics["llm_calls_total"],
        "llm_calls_errors": _metrics["llm_calls_errors"],
        "llm_latency_seconds_sum": _metrics["llm_latency_seconds_sum"],
        "candidate_count_sum": _metrics["candidate_count_sum"],
        "candidate_count_avg": (
            _metrics["candidate_count_sum"] / total if total else 0.0
        ),
    }


def reset_metrics() -> None:
    """Reset all metrics to zero (useful for tests)."""
    for k in _metrics:
        if isinstance(_metrics[k], (int, float)):
            _metrics[k] = 0 if isinstance(_metrics[k], int) else 0.0


def health_check(
    check_database: bool = True,
    check_groq_config: bool = False,
) -> Dict[str, Any]:
    """
    Run health checks and return a status payload.

    Parameters
    ----------
    check_database
        If True, attempt to connect to the database (e.g. execute a simple query).
    check_groq_config
        If True, include whether GROQ_API_KEY is set (does not call the API).

    Returns
    -------
    dict
        {"status": "ok" | "degraded",
         "checks": {"database": "ok" | "error", "groq_config": "ok" | "missing" (optional)}}
    """
    checks: Dict[str, str] = {}
    status = "ok"

    if check_database:
        try:
            from sqlalchemy import text
            from .db import get_engine
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {e!s}"
            status = "degraded"

    if check_groq_config:
        checks["groq_config"] = "ok" if get_groq_api_key() else "missing"

    return {"status": status, "checks": checks}
