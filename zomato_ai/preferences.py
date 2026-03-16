from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class PriceRange:
    """
    Simple min/max price range in the same units as `avg_cost_for_two`.
    """

    min: Optional[int] = None
    max: Optional[int] = None


@dataclass
class Preference:
    """
    Preference model for core recommendation engine (Phase 2).
    """

    place: Optional[str] = None
    price_range: Optional[PriceRange] = None
    min_rating: Optional[float] = None
    cuisines: List[str] = None
    online_order: Optional[bool] = None
    book_table: Optional[bool] = None
    rest_type: Optional[str] = None

    def normalized_cuisines(self) -> List[str]:
        if not self.cuisines:
            return []
        return [c.strip().lower() for c in self.cuisines if c.strip()]

    def price_range_tuple(self) -> Tuple[Optional[int], Optional[int]]:
        if self.price_range is None:
            return None, None
        return self.price_range.min, self.price_range.max

