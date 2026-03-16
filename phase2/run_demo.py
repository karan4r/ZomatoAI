"""
Phase 2 demo script: run a simple recommendation query against the existing DB.

Assumes Phase 1 ingestion has already populated the database configured by DATABASE_URL.

Usage (from project root):

    export DATABASE_URL="sqlite:///./zomato.db"
    python -m phase2.run_demo
"""

from zomato_ai.preferences import Preference, PriceRange
from zomato_ai.recommendation import get_recommendations


def main() -> None:
    pref = Preference(
        place="Banashankari",
        price_range=PriceRange(min=300, max=900),
        min_rating=3.5,
        cuisines=["North Indian", "Chinese"],
        online_order=True,
    )
    recs = get_recommendations(pref, limit=5)
    for r in recs:
        print(
            f"{r['name']} ({r['location']}): rating={r['avg_rating']}, "
            f"cost_for_two={r['avg_cost_for_two']}, cuisines={', '.join(r['cuisines'])}"
        )


if __name__ == "__main__":
    main()

