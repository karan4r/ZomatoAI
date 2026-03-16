"""
Phase 6: demo semantic re-ranking (stub returns same order).
"""

from zomato_ai.semantic_rerank import semantic_rerank

def main() -> None:
    candidates = [
        {"id": 1, "name": "A", "score": 0.9},
        {"id": 2, "name": "B", "score": 0.8},
    ]
    out = semantic_rerank(candidates, user_preference_summary="North Indian", top_k=5)
    assert out == candidates
    print("semantic_rerank (stub): ok, returned", len(out), "candidates")

if __name__ == "__main__":
    main()
