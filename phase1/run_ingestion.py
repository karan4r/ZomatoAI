"""
Phase 1 CLI entrypoint for running the data ingestion pipeline.

Usage (from project root):

    export DATABASE_URL="sqlite:///./zomato.db"  # or your PostgreSQL URL
    python -m phase1.run_ingestion
"""

from zomato_ai.ingest import run_ingestion


def main() -> None:
    count = run_ingestion()
    print(f"Ingested {count} restaurants.")


if __name__ == "__main__":
    main()

