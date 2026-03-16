## ZomatoAI Restaurant Recommendation Service – Architecture

This document describes the high-level architecture of the AI-powered restaurant recommendation service. The goal is to accept user preferences (place, price, rating, cuisine, etc.), retrieve relevant restaurants from a Zomato dataset hosted on Hugging Face, and use a Groq-hosted LLM to generate clear, conversational recommendations.

---

## 1. High-Level Overview

### 1.1 Core Flow

1. Client sends preferences (place, price range, minimum rating, preferred cuisines, and optional filters) to the API.
2. API validates the request and invokes the Recommendation Engine.
3. Recommendation Engine:
   - Queries the internal restaurant database using rule-based filters.
   - Scores and ranks candidates according to relevance.
4. LLM Orchestrator:
   - Packages top candidates and user preferences into a prompt.
   - Calls the Groq LLM to generate ranked, human-friendly recommendations.
5. API returns:
   - A structured list of recommended restaurants.
   - Optional natural-language reasoning for each recommendation.

Key external dependencies:

- **Dataset**: `ManikaSaini/zomato-restaurant-recommendation` on Hugging Face.
- **LLM**: Groq-hosted language model accessed via HTTP API.

---

## 2. Data & Storage Layer

### 2.1 Data Source

- **Zomato dataset** ([Hugging Face](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)).
- Important fields:
  - Identification & location: `name`, `address`, `location`, `url`.
  - Attributes: `cuisines`, `rest_type`, `online_order`, `book_table`.
  - Scoring: `rate`, `votes`.
  - Pricing: `approx_cost(for two people)`.
  - Textual: `dish_liked`, `reviews_list`.

### 2.2 Data Ingestion Service

**Service**: `data_ingestion_service`

Responsibilities:

- Download the dataset from Hugging Face (using the `datasets` library or direct CSV/Parquet).
- Validate schema and types.
- Clean/normalize data:
  - Normalize `rate` to numeric (strip `/5`, handle non-numeric or missing values).
  - Convert `approx_cost(for two people)` to integer.
  - Normalize `location` strings (trim, lowercase, optionally map aliases).
  - Split and normalize `cuisines` into a list of tokens.
  - Extract structured ratings and text from `reviews_list` where needed.
- Upsert data into the main relational database.

Execution model:

- Runs as a batch job:
  - On initial setup.
  - On demand for refresh or when source dataset updates.

### 2.3 Database Schema

**Primary store**: PostgreSQL (or equivalent relational DB).

Suggested tables:

- `restaurants`
  - `id` (PK)
  - `name`
  - `address`
  - `location`
  - `latitude`, `longitude` (optional, for future geo queries)
  - `cuisines` (array or normalized via join table)
  - `rest_type`
  - `avg_rating` (float)
  - `review_count` (int)
  - `avg_cost_for_two` (int)
  - `online_order` (bool)
  - `book_table` (bool)
  - `source_url` (string)

- `restaurant_cuisines`
  - `restaurant_id` (FK → `restaurants.id`)
  - `cuisine` (string)

- `restaurant_reviews`
  - `id` (PK)
  - `restaurant_id` (FK)
  - `rating` (float or enum)
  - `review_text` (text)

- `etl_runs`
  - `id`
  - `source` (e.g. `zomato_hf`)
  - `version` / `commit_hash` (optional)
  - `loaded_at`
  - `row_count`

### 2.4 Optional Search / Vector Layer

For more advanced querying or semantic ranking, optionally introduce:

- **Search index** (e.g. OpenSearch / Elasticsearch) on:
  - `name`, `location`, `cuisines`, `dish_liked`, `reviews_list`.
- **Vector DB / embeddings** (e.g. pgvector, Qdrant):
  - Store restaurant embeddings built from `name + cuisines + reviews`.
  - Enable semantic similarity search and advanced recommendation strategies.

---

## 3. Recommendation Engine

### 3.1 Preference Model

The API converts user input into a structured **preference object**:

- `place` (string; e.g. area or locality name).
- `price_range` (enum or `[min_price, max_price]`).
- `min_rating` (float).
- `cuisines` (list of strings).
- Optional filters:
  - `online_order` (bool).
  - `book_table` (bool).
  - `rest_type` (e.g. `Casual Dining`, `Cafe`).
  - `limit` (max results).

### 3.2 Candidate Selector

**Component**: `candidate_selector`

Responsibilities:

- Translate preferences into DB queries:
  - Filter by `location` approximating `place`.
    - Optionally fuzzy match (e.g. `ILIKE '%banashankari%'` or search index).
  - Filter by `avg_cost_for_two` within requested `price_range`.
  - Filter by `avg_rating >= min_rating`.
  - Filter by cuisines:
    - Intersection of requested cuisines with restaurant cuisines (any or all).
  - Respect boolean filters (`online_order`, `book_table`, `rest_type`).
- Return a limited set of candidates (e.g. 100–200) for ranking.

### 3.3 Scoring & Ranking

**Component**: `ranking_service`

Responsibilities:

- Compute a composite score for each candidate:
  - `rating_score`: normalized rating.
  - `price_fit_score`: how close the cost is to desired price range.
  - `cuisine_match_score`: Jaccard or overlap ratio.
  - `popularity_score`: function of `review_count` or `votes`.
  - Optional: `distance_score` if geo coordinates are used.
- Use a configurable weighted formula:
  - `final_score = w_rating * rating_score + w_price * price_fit_score + ...`
- Sort candidates by `final_score` and return top N (e.g. 10–20).

### 3.4 Optional Semantic Re-ranker

**Component**: `semantic_reranker` (future enhancement)

Responsibilities:

- Compute embeddings for:
  - Restaurants (from name, cuisines, popular dishes, reviews).
  - User preferences (free-text query, cuisines, and context).
- For the top rule-based candidates, compute similarity scores and update ranking.
- May use Groq or a separate embeddings model for vector generation.

---

## 4. LLM Orchestration (Groq)

### 4.1 LLM Orchestrator Service

**Component**: `llm_orchestrator`

Responsibilities:

- Build prompts that include:
  - User preferences (normalized and paraphrased).
  - A machine-readable list of top candidate restaurants from the ranking engine.
- Call Groq-hosted LLM via HTTP client:
  - Include retry logic and timeouts.
  - Track latency and failures.
- Enforce output format:
  - Prefer JSON (or function-calling style if supported by Groq) with a clear schema.

### 4.2 Prompt Design

Inputs to LLM:

- **System message**:
  - Define role: restaurant recommendation assistant.
  - Constraints:
    - Recommend only from the provided candidate list.
    - Provide concise explanations.
    - Respect user preferences (place, budget, rating, cuisine).

- **Context message**:
  - Summarized user preferences.
  - JSON list of candidates with fields such as:
    - `id`, `name`, `location`, `cuisines`, `rating`, `approx_cost_for_two`, `rest_type`, `online_order`, `book_table`, and optional `popular_dishes`.

- **User message**:
  - Original user query or high-level description (optional).

Expected LLM output (example schema):

```json
{
  "recommendations": [
    {
      "restaurant_id": 123,
      "rank": 1,
      "summary_reason": "Great for North Indian food in Banashankari, within your budget and highly rated.",
      "best_for": ["family dinner", "casual outing"]
    }
  ]
}
```

### 4.3 Post-Processing

**Component**: `llm_result_interpreter`

Responsibilities:

- Parse and validate LLM output:
  - Ensure JSON conforms to expected schema.
  - Ensure restaurant IDs exist in the candidate set.
- Handle error cases:
  - If LLM output is invalid, fall back to deterministic ranking.
  - If only partial results are valid, filter out invalid entries.
- Enrich response:
  - Join restaurant details from DB.
  - Optionally add useful metadata (e.g. top cuisines, cost, rating).

---

## 5. API Layer

### 5.1 Public API

**Service**: `api_service` (e.g. FastAPI, Express, or similar).

Primary endpoint:

- `POST /recommendations`
  - **Request body**:
    - `place`: string
    - `price_range`: `{ "min": number, "max": number }` or enum (e.g. `cheap`, `moderate`, `expensive`)
    - `min_rating`: number
    - `cuisines`: string[]
    - Optional filters: `online_order`, `book_table`, `rest_type`, `limit`
  - **Flow**:
    1. Validate and normalize request → preference object.
    2. Call `candidate_selector` → candidate set.
    3. Call `ranking_service` → top N ranked candidates.
    4. Call `llm_orchestrator` → LLM-ranked recommendations with reasons.
    5. Call `llm_result_interpreter` → final structured response.
  - **Response**:
    - `recommendations`: array of objects containing:
      - Restaurant details (name, location, cuisines, rating, cost, url).
      - LLM-generated `reason` / `summary_reason`.
      - Optional `best_for` tags.
    - Optional `meta`:
      - `candidate_count`, timing info, etc. (for internal or debug use).

Supporting endpoints (optional):

- `GET /restaurants/{id}` – fetch restaurant details by ID.
- `GET /health` – health check.

### 5.2 Client Applications

Clients are not part of this architecture’s implementation scope, but the API is designed to be consumed by:

- Web frontend (e.g. React/Next.js) that:
  - Provides UI controls for place, budget, rating, and cuisine filters.
  - Displays recommendations as cards/list with explanations.
- Mobile apps or CLI tools.

---

## 6. Infrastructure & DevOps

### 6.1 Service Topology

Core deployable units:

- `api_service`
  - Hosts REST API.
  - Contains Recommendation Engine and LLM Orchestration logic.
- `data_ingestion_service`
  - Batch/cron job for loading/updating data from Hugging Face into DB.
- `db`
  - PostgreSQL instance for structured data.
- Optional:
  - `search_service` (Elasticsearch/OpenSearch).
  - `vector_db` (pgvector/Qdrant) for semantic search.

All stateless services are deployed as containers (Docker), orchestrated via:

- Kubernetes, or
- Simpler PaaS (Render/Fly.io/Heroku/etc.) for early stages.

### 6.2 Configuration & Secrets

- Configuration via environment variables:
  - Database URL and credentials.
  - Groq API key.
  - Hugging Face access token (if required).
  - Feature flags (e.g. enable/disable semantic re-ranking).
- Secrets stored using:
  - Cloud secrets manager (AWS Secrets Manager, GCP Secret Manager, etc.), or
  - Encrypted environment variables in CI/CD.

### 6.3 Observability

- **Logging**:
  - Structured logs for:
    - Incoming API requests (without sensitive content).
    - Database query failures.
    - LLM API calls (status, latency, token usage, but not full prompts/responses when containing PII).

- **Metrics** (Prometheus or similar):
  - Request latency and throughput for `/recommendations`.
  - Error rates for API, DB, and LLM calls.
  - Average candidate set size.

- **Tracing** (optional):
  - Distributed tracing for end-to-end latency analysis (API → DB → LLM).

---

## 7. Evaluation & Feedback

### 7.1 Offline Evaluation

**Component**: `evaluation_pipeline` (not user-facing).

Responsibilities:

- Define test scenarios (synthetic or curated real-world-like queries).
- For each scenario:
  - Capture recommendations from:
    - Rule-based ranking only.
    - Full pipeline including LLM.
  - Compare relevance and diversity (manual labels, heuristics, or small user studies).

### 7.2 Feedback Loop (Future)

**Component**: `feedback_collector`

Responsibilities:

- If/when there is authentication and user identity:
  - Store feedback events:
    - `user_id`, `restaurant_id`, `action` (e.g. `clicked`, `booked`, `liked`, `dismissed`), `timestamp`.
- Use data to:
  - Tune ranking weights.
  - Personalize future recommendations.
  - Refine prompt templates for the LLM.

---

## 8. Phased Implementation Roadmap

To implement this architecture incrementally:

1. **Phase 1 – Data Layer**
   - Implement `data_ingestion_service` and PostgreSQL schema.
   - Load and verify Zomato dataset from Hugging Face.
2. **Phase 2 – Core Recommendation Engine**
   - Implement candidate selection and scoring/ranking in the API service.
   - Expose a simple `/recommendations` endpoint using rule-based logic only.
3. **Phase 3 – LLM Integration**
   - Implement `llm_orchestrator` and `llm_result_interpreter`.
   - Integrate Groq API and refine prompts.
4. **Phase 4 – Hardening & Observability**
   - Add logging, metrics, health checks, and error handling.
5. **Phase 5 – Enhancements & UI**
   - Semantic re-ranking with embeddings.
   - Feedback loop and personalization.
   - Frontend UI:
     - Implement a web UI (e.g. React/Next.js) that consumes the `/recommendations` API.
     - Provide input controls for place, price, rating, and cuisines.
     - Display recommendations as cards/list with LLM-generated explanations and key attributes (rating, cost, tags).

