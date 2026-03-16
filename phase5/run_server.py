"""
Phase 5: run the FastAPI server.

Usage (from project root):

    python -m phase5.run_server

Server runs at http://127.0.0.1:8000. Use /docs for Swagger UI.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "phase5.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
