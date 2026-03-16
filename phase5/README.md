## Phase 5 – API Layer

REST API for the recommendation pipeline using FastAPI.

### Endpoints

- **POST /recommendations** – Request body: `place`, `price_range` (min/max), `min_rating`, `cuisines[]`, optional `online_order`, `book_table`, `rest_type`, `limit`. Returns LLM-ranked recommendations with reasons.
- **GET /health** – Health check (database + Groq config).
- **GET /metrics** – Observability metrics snapshot.
- **GET /restaurants/{id}** – Fetch one restaurant by ID.

### Run server

From project root:

```bash
PYTHONPATH=. python -m phase5.run_server
```

Then open http://127.0.0.1:8000/docs for Swagger UI.

### Tests

```bash
PYTHONPATH=. pytest tests/test_api.py -v
```
