## Phase 2 – Core Recommendation Engine

This folder groups Phase 2 artifacts: preference model usage, candidate selection, scoring, and ranking.

Phase 2 responsibilities:

- Accept a structured `Preference` object describing user intent:
  - `place`, `price_range`, `min_rating`, `cuisines`, `online_order`, `book_table`, `rest_type`.
- Select candidate restaurants from the Phase 1 database using rule-based filters.
- Score and rank candidates using a composite relevance score.
- Return top-N recommended restaurants as simple dicts suitable for API responses or further processing.

Core implementation lives in:

- `zomato_ai/preferences.py` – `Preference` and `PriceRange` dataclasses.
- `zomato_ai/recommendation.py` – candidate selection and ranking logic (`get_recommendations`).

### Simple usage example

```python
from zomato_ai.preferences import Preference, PriceRange
from zomato_ai.recommendation import get_recommendations

pref = Preference(
    place="Banashankari",
    price_range=PriceRange(min=300, max=900),
    min_rating=4.0,
    cuisines=["North Indian", "Chinese"],
    online_order=True,
)

recs = get_recommendations(pref, limit=5)
for r in recs:
    print(r["name"], r["avg_rating"], r["cuisines"])
```

