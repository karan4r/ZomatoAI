## Phase 1 – Data Layer

This folder groups together entrypoints and documentation related to **Phase 1: Data & Storage Layer** of the ZomatoAI project.

Phase 1 responsibilities:

- Ingest the Zomato dataset from Hugging Face (`ManikaSaini/zomato-restaurant-recommendation`).
- Normalize and clean key fields (rating, cost, location, cuisines, etc.).
- Populate the relational database schema:
  - `restaurants`
  - `restaurant_cuisines`
  - `restaurant_reviews` (reserved for later use)
  - `etl_runs`

The core logic for this phase lives in the reusable package:

- `zomato_ai/db.py` – database engine and session factory.
- `zomato_ai/models.py` – SQLAlchemy models.
- `zomato_ai/ingest.py` – ingestion pipeline.

This folder provides convenience entrypoints and is a logical boundary for Phase 1, without duplicating that core logic.

### Running the ingestion

From the project root:

```bash
export DATABASE_URL="sqlite:///./zomato.db"  # or your PostgreSQL URL
python -m phase1.run_ingestion
```

This will:

- Download the dataset from Hugging Face.
- Create tables if needed.
- Ingest all restaurants and cuisines.
- Record an `etl_runs` row with the total count.

