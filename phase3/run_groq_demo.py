"""
Phase 3 Groq integration: run full pipeline with real Groq LLM.

Requires:
  - GROQ_API_KEY in .env (or environment).
  - Phase 1 ingestion has populated the database (DATABASE_URL).

Usage (from project root):

    pip install -r requirements.txt
    # Ensure .env contains GROQ_API_KEY=...
    python -m phase3.run_groq_demo
"""

from zomato_ai.config import get_groq_api_key
from zomato_ai.preferences import Preference, PriceRange
from zomato_ai.recommendation import get_recommendations
from zomato_ai.llm_orchestrator import generate_llm_recommendations
from zomato_ai.groq_client import GroqLLMClient


def main() -> None:
    if not get_groq_api_key():
        raise SystemExit(
            "GROQ_API_KEY not set. Add it to .env in the project root and try again."
        )

    pref = Preference(
        place="Banashankari",
        price_range=PriceRange(min=300, max=900),
        min_rating=3.5,
        cuisines=["North Indian", "Chinese"],
    )
    candidates = get_recommendations(pref, limit=20)
    if not candidates:
        print("No candidates from Phase 2. Run Phase 1 ingestion first.")
        return

    # Explicit Groq client for this demo
    client = GroqLLMClient()
    final = generate_llm_recommendations(pref, candidates, limit=5, client=client)

    print("Groq-powered recommendations:\n")
    for r in final:
        print(f"  {r['rank']}. {r['name']} (rating: {r.get('avg_rating')})")
        print(f"     {r.get('summary_reason')}")
        if r.get("best_for"):
            print(f"     Best for: {', '.join(r['best_for'])}")
        print()


if __name__ == "__main__":
    main()
