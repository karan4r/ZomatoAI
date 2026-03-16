## Phase 4 – Hardening & Observability

This folder groups Phase 4 artifacts: logging, metrics, and health checks for the recommendation pipeline.

Phase 4 responsibilities:

- **Structured logging** for pipeline steps (request start/end, DB/LLM calls).
- **In-memory metrics** for recommendation requests (count, latency, candidate set size) and LLM calls (count, latency, errors).
- **Health checks** for database connectivity and optional config (e.g. Groq API key presence).

Core implementation lives in:

- `zomato_ai/observability.py`
  - `get_logger(name)` – structured logger
  - `record_recommendation_request(...)`, `record_llm_call(...)` – metrics
  - `get_metrics()`, `reset_metrics()` – read/reset metrics
  - `health_check(check_database=..., check_groq_config=...)` – health payload

The Groq client records LLM call latency and errors via `record_llm_call` when the observability module is available.

### Run health check

From project root:

```bash
python -m phase4.run_health
```

Prints a JSON-like health status (database and optional Groq config).

### Run demo with observability

Runs one recommendation flow with logging and metrics, then prints metrics:

```bash
# Ensure Phase 1 ingestion has run (database populated)
python -m phase4.run_demo_with_observability
```

### Tests

From project root (so `zomato_ai` is importable):

```bash
PYTHONPATH=. pytest tests/test_observability.py -v
```
