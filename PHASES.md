# Phase connectivity

All phases are wired and tested. Data and control flow:

```
Phase 1 (Data)          →  Writes to DB (config: DATABASE_URL, .env)
      ↓
Phase 2 (Recommendation)→  get_recommendations(pref) reads DB, returns candidates
      ↓
Phase 3 (LLM)           →  generate_llm_recommendations(pref, candidates) uses Groq or DummyLLM (config: GROQ_API_KEY in .env)
      ↓
Phase 4 (Observability) →  health_check(), record_recommendation_request(), record_llm_call() used by API and Groq client
      ↓
Phase 5 (API)           →  POST /recommendations = Phase 2 → Phase 3 + Phase 4 metrics; GET /health = Phase 4; POST /feedback = Phase 6
      ↓
Phase 6 (Enhancements)  →  record_feedback() from API; semantic_rerank() stub
      ↓
Phase 7 (UI)            →  React app in phase7/ui consumes Phase 5 API; API serves built UI at / when phase7/ui/dist exists
```

## Verification

- **Unit + integration**: `PYTHONPATH=. pytest tests/ -v --override-ini "addopts=-v"` (includes Phase 7 and Groq integration when key set).
- **E2E pipeline**: `tests/test_e2e_pipeline.py` runs Phase 1 → 2 → 3 → 4 → 5 → 6 in one go (temp DB, DummyLLM).
- **Phase 7**: `tests/test_phase7.py` checks UI files, API integration, and (if npm/dist present) build and root serve.

## Quick checks

| Check | Command |
|-------|--------|
| All tests | `PYTHONPATH=. pytest tests/ -v --override-ini "addopts=-v"` |
| Health only | `PYTHONPATH=. python -m phase4.run_health` |
| API server | `PYTHONPATH=. python -m phase5.run_server` then open http://127.0.0.1:8000/docs |
| API + UI (single server) | Build: `cd phase7/ui && npm run build` then `PYTHONPATH=. python -m phase7.run_serve` → http://127.0.0.1:8000 |
| UI dev | From `phase7/ui`: `npm install && npm run dev` (API must be running on 8000) |
