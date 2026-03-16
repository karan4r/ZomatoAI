from typing import Optional

import pandas as pd
from datasets import load_dataset, Dataset
from sqlalchemy.orm import Session

from .db import Base, get_engine, get_session_factory
from .models import Restaurant, RestaurantCuisine, ETLRun


def _parse_rating(raw: Optional[str]) -> Optional[float]:
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw or raw in {"-", "NEW"}:
        return None
    # Many ratings are like "4.1/5"
    if "/" in raw:
        raw = raw.split("/", 1)[0]
    try:
        return float(raw)
    except ValueError:
        return None


def _parse_cost(raw: Optional[str]) -> Optional[int]:
    if raw is None:
        return None
    raw = str(raw)
    # Remove commas and non-digit characters
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _normalize_bool(raw: Optional[str]) -> bool:
    if raw is None:
        return False
    return str(raw).strip().lower() == "yes"


def _split_cuisines(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    parts = [p.strip() for p in str(raw).split(",") if p.strip()]
    return parts


def load_zomato_dataset() -> Dataset:
    """
    Load the Zomato dataset from Hugging Face.

    Uses the default 'train' split from the ManikaSaini/zomato-restaurant-recommendation dataset.
    """
    return load_dataset("ManikaSaini/zomato-restaurant-recommendation", split="train")


def run_ingestion(hf_dataset: Optional[Dataset] = None, echo_sql: bool = False) -> int:
    """
    Run a full ingestion from the Hugging Face dataset into the configured database.

    Parameters
    ----------
    hf_dataset:
        Optionally provide an in-memory Dataset (used by tests). If None, the dataset
        is downloaded from Hugging Face.
    echo_sql:
        If True, SQLAlchemy engine will echo SQL for debugging.

    Returns
    -------
    int
        Number of restaurant rows ingested.
    """
    if hf_dataset is None:
        hf_dataset = load_zomato_dataset()

    df = hf_dataset.to_pandas()

    engine = get_engine(echo=echo_sql)
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    session_factory = get_session_factory(echo=echo_sql)

    session: Session
    row_count = 0
    with session_factory() as session:
        # Simple full-refresh strategy: clear existing data for now.
        session.query(RestaurantCuisine).delete()
        session.query(Restaurant).delete()
        session.commit()

        for _, row in df.iterrows():
            rating = _parse_rating(row.get("rate"))
            cost = _parse_cost(row.get("approx_cost(for two people)"))

            restaurant = Restaurant(
                name=row.get("name") or "",
                address=row.get("address"),
                location=(row.get("location") or "").strip() or None,
                rest_type=row.get("rest_type"),
                avg_rating=rating,
                review_count=int(row.get("votes") or 0),
                avg_cost_for_two=cost,
                online_order=_normalize_bool(row.get("online_order")),
                book_table=_normalize_bool(row.get("book_table")),
                source_url=row.get("url"),
            )
            session.add(restaurant)
            session.flush()  # assign ID

            for cuisine in _split_cuisines(row.get("cuisines")):
                session.add(
                    RestaurantCuisine(
                        restaurant_id=restaurant.id,
                        cuisine=cuisine,
                    )
                )

            row_count += 1

        # Log ETL run
        session.add(
            ETLRun(
                source="zomato_hf",
                row_count=row_count,
            )
        )

        session.commit()

    return row_count


if __name__ == "__main__":
    count = run_ingestion()
    print(f"Ingested {count} restaurants.")

