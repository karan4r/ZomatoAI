import os

import pandas as pd
from datasets import Dataset
from sqlalchemy import text

from zomato_ai import ingest
from zomato_ai.db import Base, get_engine, get_session_factory


def make_fake_dataset() -> Dataset:
    """
    Create a tiny in-memory dataset that matches the Hugging Face schema shape
    for ingestion unit testing.
    """
    data = {
        "url": [
            "https://www.zomato.com/bangalore/jalsa-banashankari",
            "https://www.zomato.com/bangalore/spice-elephant-banashankari",
        ],
        "address": [
            "21st Main Road, Banashankari, Bangalore",
            "80 Feet Road, Banashankari, Bangalore",
        ],
        "name": ["Jalsa", "Spice Elephant"],
        "online_order": ["Yes", "Yes"],
        "book_table": ["Yes", "No"],
        "rate": ["4.1/5", "4.1/5"],
        "votes": [775, 787],
        "phone": ["080 42297555", "080 41714161"],
        "location": ["Banashankari", "Banashankari"],
        "rest_type": ["Casual Dining", "Casual Dining"],
        "dish_liked": ["Dum Biryani", "Chicken Biryani"],
        "cuisines": ["North Indian, Mughlai, Chinese", "Chinese, North Indian, Thai"],
        "approx_cost(for two people)": ["800", "800"],
        "reviews_list": ["[]", "[]"],
        "menu_item": ["[]", "[]"],
        "listed_in(type)": ["Buffet", "Buffet"],
        "listed_in(city)": ["Banashankari", "Banashankari"],
    }
    df = pd.DataFrame(data)
    return Dataset.from_pandas(df)


def test_run_ingestion_with_fake_dataset(tmp_path, monkeypatch):
    """
    Ensure that run_ingestion correctly populates the schema
    using a small in-memory dataset and a temporary SQLite database.
    """
    db_path = tmp_path / "test_zomato.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    # Recreate engine and metadata for this test DB
    engine = get_engine()
    Base.metadata.create_all(engine)

    fake_ds = make_fake_dataset()
    row_count = ingest.run_ingestion(hf_dataset=fake_ds)

    assert row_count == 2

    session_factory = get_session_factory()
    with session_factory() as session:
        # Verify restaurants inserted
        result = session.execute(text("SELECT COUNT(*) FROM restaurants"))
        count = result.scalar_one()
        assert count == 2

        # Verify cuisines inserted
        result = session.execute(text("SELECT COUNT(*) FROM restaurant_cuisines"))
        cuisine_count = result.scalar_one()
        # Jalsa: 3 cuisines, Spice Elephant: 3 cuisines
        assert cuisine_count == 6

        # Verify at least one ETL run recorded
        result = session.execute(text("SELECT COUNT(*) FROM etl_runs"))
        etl_count = result.scalar_one()
        assert etl_count == 1

