"""
Phase 4: run health checks and print status.

Usage (from project root):

    python -m phase4.run_health
"""

import json
from zomato_ai.observability import health_check


def main() -> None:
    result = health_check(check_database=True, check_groq_config=True)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
