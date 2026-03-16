## Phase 3 – LLM Orchestration (Groq)

This folder groups Phase 3 artifacts: orchestration of an LLM (Groq) over the
structured recommendations produced in Phase 2.

Phase 3 responsibilities:

- Build a prompt (or structured input) describing:
  - The user's `Preference` (place, budget, rating, cuisines, etc.).
  - A list of candidate restaurants from the Phase 2 engine.
- Call a Groq-hosted LLM (abstracted behind an `LLMClient` interface).
- Interpret the LLM's structured response into a final ordered list of recommendations
  with explanations and tags.

Core implementation currently lives in:

- `zomato_ai/llm_orchestrator.py`
  - `LLMClient` protocol.
  - `DummyLLMClient` – local implementation used for tests/demos (no network).
  - `generate_llm_recommendations` – main entrypoint for Phase 3.

Real Groq integration is in `zomato_ai/groq_client.py` (`GroqLLMClient`). If `GROQ_API_KEY` is set (e.g. in `.env`), `generate_llm_recommendations(..., client=None)` uses Groq by default; otherwise it falls back to `DummyLLMClient`.

### Groq integration (real LLM)

1. Add your key to `.env` in the project root:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
2. Install dependencies: `pip install -r requirements.txt`
3. Run Phase 1 ingestion so the DB has restaurants (see Phase 1 README).
4. Trigger the Groq-powered pipeline:
   ```bash
   python -m phase3.run_groq_demo
   ```
   This uses the real Groq API to rank and explain recommendations.

Integration test: when `GROQ_API_KEY` is set in `.env`, run the Groq integration test with:

```bash
PYTHONPATH=. pytest tests/test_llm_orchestrator.py::test_groq_integration_returns_recommendations -v --override-ini "addopts=-v"
```

(This overrides the default pytest filter that excludes the integration test.)

### Simple usage example (Dummy or Groq by default)

```python
from zomato_ai.preferences import Preference, PriceRange
from zomato_ai.recommendation import get_recommendations
from zomato_ai.llm_orchestrator import generate_llm_recommendations

pref = Preference(
    place="Banashankari",
    price_range=PriceRange(min=300, max=900),
    min_rating=3.5,
    cuisines=["North Indian", "Chinese"],
)

phase2_candidates = get_recommendations(pref, limit=20)
final_recs = generate_llm_recommendations(pref, phase2_candidates, limit=5)

for r in final_recs:
    print(r["rank"], r["name"], "→", r["summary_reason"])
```

