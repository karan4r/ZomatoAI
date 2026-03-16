## Phase 7 – UI & full-stack integration

Phase 7 provides the production UI and its integration with the API (Phase 5).

### Contents

- **phase7/ui/** – React (Vite) app that consumes the recommendations API:
  - Place, price range, min rating, cuisines.
  - Displays recommendations with LLM summary, rating, cost, tags.
  - Shows API meta (candidate count, latency) and health status.
  - Like/Dismiss feedback (POST /feedback).

### Dev (API + UI separate)

1. Start API: `PYTHONPATH=. python -m phase5.run_server` (http://127.0.0.1:8000).
2. From **phase7/ui**: `npm install && npm run dev` (Vite proxies to API).

### Production-style (single server)

1. Build UI: `cd phase7/ui && npm install && npm run build`.
2. Start API: `PYTHONPATH=. python -m phase5.run_server`.  
   The API serves the built UI at http://127.0.0.1:8000/ when `phase7/ui/dist` exists.

### Tests

```bash
PYTHONPATH=. pytest tests/test_phase7.py -v
```
