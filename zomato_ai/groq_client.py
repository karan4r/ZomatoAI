"""
Groq API client for Phase 3 LLM recommendations.

Uses GROQ_API_KEY from environment (loaded via .env in config).
"""

from __future__ import annotations

import json
import re
import time
from typing import List, Dict, Any, Optional

from .config import get_groq_api_key
from .preferences import Preference


def _build_candidates_text(candidates: List[Dict[str, Any]], limit: int) -> str:
    """Format candidate list for the prompt."""
    lines = []
    for i, c in enumerate(candidates[: limit * 2], start=1):  # send a few extra for context
        lines.append(
            f"  {i}. id={c.get('id')} | {c.get('name')} | {c.get('location') or 'N/A'} | "
            f"rating={c.get('avg_rating')} | cost_for_two={c.get('avg_cost_for_two')} | "
            f"cuisines={', '.join(c.get('cuisines') or [])}"
        )
    return "\n".join(lines) if lines else " (none)"


def _build_preference_summary(pref: Preference) -> str:
    """Summarize user preference for the prompt."""
    parts = []
    if pref.place:
        parts.append(f"Place: {pref.place}")
    if pref.min_rating is not None:
        parts.append(f"Minimum rating: {pref.min_rating}")
    if pref.price_range:
        pr = pref.price_range
        if pr.min is not None or pr.max is not None:
            parts.append(f"Budget (cost for two): {pr.min or 'any'} - {pr.max or 'any'}")
    if pref.cuisines:
        parts.append(f"Cuisines: {', '.join(pref.cuisines)}")
    if pref.online_order is not None:
        parts.append(f"Online order: {'Yes' if pref.online_order else 'No'}")
    if pref.book_table is not None:
        parts.append(f"Table booking: {'Yes' if pref.book_table else 'No'}")
    if pref.rest_type:
        parts.append(f"Restaurant type: {pref.rest_type}")
    return "\n".join(parts) if parts else "No specific preferences."


def _extract_json_from_response(content: str) -> Optional[Dict[str, Any]]:
    """Try to parse JSON from LLM response (handles markdown code blocks)."""
    content = (content or "").strip()
    # Try ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Try raw { ... }
    start = content.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(content)):
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(content[start : i + 1])
                    except json.JSONDecodeError:
                        break
    return None


class GroqLLMClient:
    """
    LLM client that calls Groq's chat API to generate restaurant recommendations.

    Expects GROQ_API_KEY to be set (e.g. via .env). If not set, recommend()
    will raise RuntimeError.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
    ):
        self._api_key = api_key or get_groq_api_key()
        self._model = model

    def recommend(
        self,
        preference: Preference,
        candidates: List[Dict[str, Any]],
        limit: int,
    ) -> Dict[str, Any]:
        if not self._api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to .env or pass api_key to GroqLLMClient."
            )

        from groq import Groq

        client = Groq(api_key=self._api_key)

        pref_summary = _build_preference_summary(preference)
        candidates_text = _build_candidates_text(candidates, limit)

        system_content = """You are a restaurant recommendation assistant. You must recommend ONLY from the list of candidates provided. Return your response as valid JSON only, with no other text before or after.

Required JSON shape:
{
  "recommendations": [
    {
      "restaurant_id": <integer id from the list>,
      "rank": 1,
      "summary_reason": "One short sentence why this fits the user.",
      "best_for": ["tag1", "tag2"]
    }
  ]
}

Pick the best up to the requested number, in order of fit. Use the exact restaurant id from the list."""

        user_content = f"""User preferences:
{pref_summary}

Candidates (use only these ids):
{candidates_text}

Return exactly {limit} recommendations as JSON with "recommendations" array. Use only restaurant ids from the list above."""

        try:
            from .observability import record_llm_call
        except ImportError:
            record_llm_call = None

        start = time.time()
        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
            )
            if record_llm_call is not None:
                record_llm_call(time.time() - start, error=False)
        except Exception:
            if record_llm_call is not None:
                record_llm_call(time.time() - start, error=True)
            raise

        content = response.choices[0].message.content if response.choices else ""
        parsed = _extract_json_from_response(content)
        if not parsed or "recommendations" not in parsed:
            # Fallback: return top by score so caller still gets a valid structure
            sorted_candidates = sorted(
                candidates,
                key=lambda c: c.get("score", 0.0),
                reverse=True,
            )[:limit]
            return {
                "recommendations": [
                    {
                        "restaurant_id": c["id"],
                        "rank": i + 1,
                        "summary_reason": f"Recommended: {c.get('name')}.",
                        "best_for": ["general dining"],
                    }
                    for i, c in enumerate(sorted_candidates, start=1)
                ]
            }
        return parsed
