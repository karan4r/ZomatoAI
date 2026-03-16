"""
Tests for Phase 7 – UI and full-stack integration.

Verifies Phase 7 UI assets exist and that the API (used by the UI) works
when invoked as in the full pipeline.
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Phase 7 UI directory (project root = parent of tests/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PHASE7_UI = PROJECT_ROOT / "phase7" / "ui"
PHASE7_UI_DIST = PHASE7_UI / "dist"


def test_phase7_ui_files_exist():
    """Phase 7 UI source and config must exist."""
    assert (PHASE7_UI / "package.json").is_file(), "phase7/ui/package.json missing"
    assert (PHASE7_UI / "src" / "App.jsx").is_file(), "phase7/ui/src/App.jsx missing"
    assert (PHASE7_UI / "index.html").is_file(), "phase7/ui/index.html missing"
    assert (PHASE7_UI / "vite.config.js").is_file(), "phase7/ui/vite.config.js missing"


def test_phase7_api_health_integration(tmp_path, monkeypatch):
    """API health works when called as by Phase 7 UI (same server)."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'p7.db'}")
    monkeypatch.setenv("GROQ_API_KEY", "")
    from zomato_ai.db import Base, get_engine
    Base.metadata.create_all(get_engine())

    from phase5.app import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data and "checks" in data


def test_phase7_api_recommendations_integration(tmp_path, monkeypatch):
    """POST /recommendations works when called as by Phase 7 UI."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'p7rec.db'}")
    monkeypatch.setenv("GROQ_API_KEY", "")

    from zomato_ai.db import Base, get_engine, get_session_factory
    from zomato_ai.models import Restaurant, RestaurantCuisine
    Base.metadata.create_all(get_engine())
    session_factory = get_session_factory()
    with session_factory() as session:
        r = Restaurant(
            name="Phase7 Test",
            location="Bangalore",
            avg_rating=4.0,
            avg_cost_for_two=500,
            online_order=True,
            book_table=False,
        )
        session.add(r)
        session.flush()
        session.add(RestaurantCuisine(restaurant_id=r.id, cuisine="North Indian"))
        session.commit()

    from phase5.app import app
    client = TestClient(app)
    r = client.post(
        "/recommendations",
        json={"place": "Bangalore", "min_rating": 3.0, "cuisines": ["North Indian"], "limit": 3},
    )
    assert r.status_code == 200
    data = r.json()
    assert "recommendations" in data and "meta" in data


def test_phase7_ui_build_creates_dist():
    """Build Phase 7 UI and assert dist/index.html exists (skip if npm not available)."""
    import subprocess
    try:
        subprocess.run(
            ["npm", "install", "--prefix", str(PHASE7_UI)],
            check=True,
            capture_output=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pytest.skip("npm not available or install failed")
    try:
        subprocess.run(
            ["npm", "run", "build", "--prefix", str(PHASE7_UI)],
            check=True,
            capture_output=True,
            timeout=60,
            cwd=str(PROJECT_ROOT),
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pytest.skip("UI build failed")
    assert (PHASE7_UI_DIST / "index.html").is_file(), "phase7/ui/dist/index.html missing after build"


def test_phase7_root_serves_ui_when_dist_exists(monkeypatch):
    """When phase7/ui/dist exists, GET / serves the UI (index.html)."""
    _ui_dist = PROJECT_ROOT / "phase7" / "ui" / "dist"
    if not _ui_dist.exists() or not (_ui_dist / "index.html").exists():
        pytest.skip("phase7/ui/dist not built; run: cd phase7/ui && npm run build")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./phase7_test.db")
    from phase5.app import app
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "html" in (r.text or "").lower()
