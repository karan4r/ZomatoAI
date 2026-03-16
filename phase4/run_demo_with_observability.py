"""
Phase 4: run one recommendation with logging and metrics, then print metrics.

Requires Phase 1 ingestion to have populated the database.

Usage (from project root):

    python -m phase4.run_demo_with_observability
"""

import time
from zomato_ai.observability import (
    get_logger,
    get_metrics,
    record_recommendation_request,
    reset_metrics,
)
from zomato_ai.preferences import Preference, PriceRange
from zomato_ai.recommendation import get_recommendations
from zomato_ai.llm_orchestrator import generate_llm_recommendations


def main() -> None:
    logger = get_logger("phase4.demo")
    reset_metrics()

    pref = Preference(
        place="Banashankari",
        price_range=PriceRange(min=300, max=900),
        min_rating=3.5,
        cuisines=["North Indian", "Chinese"],
    )

    logger.info("Starting recommendation request", extra={"place": pref.place})
    start = time.time()
    try:
        candidates = get_recommendations(pref, limit=20)
        final = generate_llm_recommendations(pref, candidates, limit=5)
        elapsed = time.time() - start
        record_recommendation_request(elapsed, candidate_count=len(candidates), error=False)
        logger.info(
            "Recommendation completed",
            extra={"count": len(final), "candidates": len(candidates), "latency_sec": round(elapsed, 3)},
        )
        for r in final:
            print(f"  {r['rank']}. {r['name']} – {r.get('summary_reason', '')}")
    except Exception as e:
        record_recommendation_request(time.time() - start, candidate_count=0, error=True)
        logger.exception("Recommendation failed")
        raise SystemExit(1) from e

    print("\nMetrics:")
    for k, v in get_metrics().items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
