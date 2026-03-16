from typing import List, Dict, Any

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, joinedload

from .db import get_session_factory
from .models import Restaurant, RestaurantCuisine
from .preferences import Preference


def _build_candidate_query(session: Session, pref: Preference, candidate_limit: int):
    """
    Build a SQLAlchemy query to select candidate restaurants according to the preference.
    """
    stmt = select(Restaurant).options(joinedload(Restaurant.cuisines))

    conditions = []

    # Place / location filter
    if pref.place:
        place = f"%{pref.place.strip().lower()}%"
        # Use case-insensitive match on location
        conditions.append(Restaurant.location.ilike(place))

    # Rating filter
    if pref.min_rating is not None:
        conditions.append(Restaurant.avg_rating >= pref.min_rating)

    # Price range filter
    min_price, max_price = pref.price_range_tuple()
    if min_price is not None:
        conditions.append(Restaurant.avg_cost_for_two >= min_price)
    if max_price is not None:
        conditions.append(Restaurant.avg_cost_for_two <= max_price)

    # Boolean filters
    if pref.online_order is not None:
        conditions.append(Restaurant.online_order == pref.online_order)
    if pref.book_table is not None:
        conditions.append(Restaurant.book_table == pref.book_table)

    # Rest type filter
    if pref.rest_type:
        conditions.append(Restaurant.rest_type.ilike(f"%{pref.rest_type.strip()}%"))

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # If specific cuisines requested, filter by any-matching cuisine via join
    cuisines = pref.normalized_cuisines()
    if cuisines:
        stmt = (
            stmt.join(RestaurantCuisine, Restaurant.id == RestaurantCuisine.restaurant_id)
            .where(
                or_(
                    *[
                        RestaurantCuisine.cuisine.ilike(f"%{c}%")
                        for c in cuisines
                    ]
                )
            )
        )

    # Coarse ordering: by rating desc, then reviews desc
    stmt = stmt.order_by(Restaurant.avg_rating.desc().nullslast(), Restaurant.review_count.desc().nullslast())
    stmt = stmt.limit(candidate_limit)

    return stmt


def _cuisine_set(restaurant: Restaurant) -> set:
    return {c.cuisine.strip().lower() for c in restaurant.cuisines if c.cuisine}


def _score_restaurant(restaurant: Restaurant, pref: Preference) -> float:
    """
    Compute a composite relevance score for a restaurant.
    """
    score = 0.0

    # Rating score
    if restaurant.avg_rating is not None:
        # normalize to 0-1 assuming rating in 0–5
        rating_score = max(0.0, min(1.0, restaurant.avg_rating / 5.0))
        score += 0.5 * rating_score

    # Popularity score (review count)
    if restaurant.review_count:
        # log-style scaling: using sqrt to avoid domination
        popularity_score = min(1.0, (restaurant.review_count ** 0.5) / 50.0)
        score += 0.2 * popularity_score

    # Cuisine match score
    pref_cuisines = set(pref.normalized_cuisines())
    if pref_cuisines:
        rest_cuisines = _cuisine_set(restaurant)
        if rest_cuisines:
            overlap = pref_cuisines & rest_cuisines
            cuisine_match_score = len(overlap) / len(pref_cuisines)
            score += 0.3 * cuisine_match_score

    return score


def get_recommendations(
    pref: Preference,
    limit: int = 10,
    candidate_limit: int = 200,
) -> List[Dict[str, Any]]:
    """
    Main Phase 2 entrypoint: select, score, and rank restaurants according to a preference.

    Returns a list of simple dicts suitable for further processing or API responses.
    """
    session_factory = get_session_factory()
    results: List[Dict[str, Any]] = []

    with session_factory() as session:
        stmt = _build_candidate_query(session, pref, candidate_limit)
        restaurants: List[Restaurant] = session.execute(stmt).scalars().unique().all()

        scored = []
        for r in restaurants:
            s = _score_restaurant(r, pref)
            scored.append((s, r))

        # Sort by score descending then by rating / reviews as tie-breakers
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:limit]

        for score, r in top:
            results.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "location": r.location,
                    "rest_type": r.rest_type,
                    "avg_rating": r.avg_rating,
                    "review_count": r.review_count,
                    "avg_cost_for_two": r.avg_cost_for_two,
                    "online_order": r.online_order,
                    "book_table": r.book_table,
                    "cuisines": sorted(list(_cuisine_set(r))),
                    "score": score,
                }
            )

    return results

