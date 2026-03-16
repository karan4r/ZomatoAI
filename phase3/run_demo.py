"""
Phase 3 demo script: run recommendations and pass them through the LLM orchestrator.

Assumes:
  - Phase 1 ingestion has populated the database (DATABASE_URL).
  - Phase 2 recommendation engine is functional.

Usage (from project root):

    export DATABASE_URL="sqlite:///./zomato.db"
    python -m phase3.run_demo
"""

from zomato_ai.preferences import Preference, PriceRange
from zomato_ai.recommendation import get_recommendations
from zomato_ai.llm_orchestrator import generate_llm_recommendations


def main() -> None:
    pref = Preference(
        place="Banashankari",
        price_range=PriceRange(min=300, max=900),
        min_rating=3.5,
        cuisines=["North Indian", "Chinese"],
    )
    candidates = get_recommendations(pref, limit=20)
    final = generate_llm_recommendations(pref, candidates, limit=5)

    for r in final:
        print(
            f"{r['rank']}. {r['name']} ({r['avg_rating']}) - {r['summary_reason']}"
        )


if __name__ == "__main__":
    main()

