## Phase 6 – Enhancements & UI

Semantic re-ranking (stub), feedback collection, and frontend UI.

### Components

- **Semantic re-rank** (`zomato_ai/semantic_rerank.py`): Stub that returns candidates unchanged; can be replaced with embedding-based re-ranking.
- **Feedback** (`zomato_ai/feedback.py`): In-memory store for events (clicked, liked, dismissed, booked). API: `POST /feedback` (see Phase 5).
- **Frontend** (`phase6/ui/`): React app that calls the recommendations API and displays results.

### Run semantic re-rank demo

```bash
PYTHONPATH=. python -m phase6.run_rerank_demo
```

### Run frontend

1. Start the API: `PYTHONPATH=. python -m phase5.run_server`
2. From `phase6/ui`: `npm install && npm run dev`
3. Open the URL shown (e.g. http://localhost:5173).

### Tests

```bash
PYTHONPATH=. pytest tests/test_semantic_rerank.py tests/test_feedback.py -v
```
