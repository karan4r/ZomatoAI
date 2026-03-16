"""
Phase 7: run API server (serves built UI at / when phase7/ui/dist exists).

Usage (from project root):

  # Build UI first (optional; without it only API is served):
  cd phase7/ui && npm install && npm run build && cd ../..

  PYTHONPATH=. python -m phase7.run_serve

Then open http://127.0.0.1:8000 (UI if built) or http://127.0.0.1:8000/docs (API).
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "phase5.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
