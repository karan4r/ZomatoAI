"""
Pydantic request/response models for Phase 5 API.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class PriceRangeRequest(BaseModel):
    min: Optional[int] = Field(None, description="Min cost for two")
    max: Optional[int] = Field(None, description="Max cost for two")


class RecommendationsRequest(BaseModel):
    place: Optional[str] = Field(None, description="Location/area name")
    price_range: Optional[PriceRangeRequest] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    cuisines: Optional[List[str]] = Field(default_factory=list)
    online_order: Optional[bool] = None
    book_table: Optional[bool] = None
    rest_type: Optional[str] = None
    limit: int = Field(5, ge=1, le=20, description="Max recommendations to return")


class RecommendationItem(BaseModel):
    id: int
    name: str
    location: Optional[str]
    cuisines: List[str]
    avg_rating: Optional[float]
    avg_cost_for_two: Optional[int]
    summary_reason: Optional[str] = None
    best_for: List[str] = Field(default_factory=list)
    rank: Optional[int] = None


class RecommendationsResponse(BaseModel):
    recommendations: List[RecommendationItem]
    meta: Optional[dict] = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    restaurant_id: int
    action: str = Field(..., pattern="^(clicked|liked|dismissed|booked)$")
    user_id: str = "anonymous"
    session_id: str = ""
