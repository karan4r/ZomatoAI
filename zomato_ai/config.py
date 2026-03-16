import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root (parent of this package)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def get_database_url() -> str:
    """
    Return the database URL for the data layer.

    DATABASE_URL:
        - Production: PostgreSQL, e.g. postgresql+psycopg2://user:pass@host:5432/dbname
        - Local/testing: SQLite, e.g. sqlite:///./zomato.db
    """
    return os.getenv("DATABASE_URL", "sqlite:///./zomato.db")


def get_groq_api_key() -> Optional[str]:
    """
    Return GROQ_API_KEY from environment (loaded from .env if present).
    """
    key = (os.getenv("GROQ_API_KEY") or "").strip()
    return key if key else None
