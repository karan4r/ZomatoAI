import os

from sqlalchemy import text

from zomato_ai.db import Base, get_engine, get_session_factory
from zomato_ai.models import Restaurant, RestaurantCuisine
from zomato_ai.preferences import Preference, PriceRange
from zomato_ai.recommendation import get_recommendations


def _setup_test_db(tmp_path):
    db_path = tmp_path / "test_phase2.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    engine = get_engine()
    Base.metadata.create_all(engine)

    session_factory = get_session_factory()
    with session_factory() as session:
        # Create three restaurants with varying attributes
        r1 = Restaurant(
            name="Jalsa",
            address="Banashankari",
            location="Banashankari",
            rest_type="Casual Dining",
            avg_rating=4.5,
            review_count=100,
            avg_cost_for_two=800,
            online_order=True,
            book_table=True,
        )
        r2 = Restaurant(
            name="Spice Elephant",
            address="Banashankari",
            location="Banashankari",
            rest_type="Casual Dining",
            avg_rating=4.0,
            review_count=50,
            avg_cost_for_two=700,
            online_order=True,
            book_table=False,
        )
        r3 = Restaurant(
            name="Budget Bites",
            address="Banashankari",
            location="Banashankari",
            rest_type="Quick Bites",
            avg_rating=3.0,
            review_count=10,
            avg_cost_for_two=200,
            online_order=False,
            book_table=False,
        )

        session.add_all([r1, r2, r3])
        session.flush()

        # Add cuisines
        cuisines = [
            RestaurantCuisine(restaurant_id=r1.id, cuisine="North Indian"),
            RestaurantCuisine(restaurant_id=r1.id, cuisine="Mughlai"),
            RestaurantCuisine(restaurant_id=r2.id, cuisine="Chinese"),
            RestaurantCuisine(restaurant_id=r2.id, cuisine="North Indian"),
            RestaurantCuisine(restaurant_id=r3.id, cuisine="South Indian"),
        ]
        session.add_all(cuisines)
        session.commit()

    return db_path


def test_get_recommendations_filters_and_ranks(tmp_path):
    """
    Ensure Phase 2 recommendation engine filters by preferences and ranks results sensibly.
    """
    _setup_test_db(tmp_path)

    pref = Preference(
        place="Banashankari",
        price_range=PriceRange(min=300, max=900),
        min_rating=3.5,
        cuisines=["North Indian"],
        online_order=True,
    )

    recs = get_recommendations(pref, limit=5)

    # Should not be empty and should not include Budget Bites (low rating and no online_order)
    names = [r["name"] for r in recs]
    assert "Budget Bites" not in names
    assert "Jalsa" in names
    assert "Spice Elephant" in names

    # Higher rated and more popular Jalsa should rank above Spice Elephant
    assert names.index("Jalsa") < names.index("Spice Elephant")

