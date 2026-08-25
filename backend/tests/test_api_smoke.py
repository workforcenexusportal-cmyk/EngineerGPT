"""Smoke tests for the API layer that do not require a live database."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_openapi_lists_all_modules():
    schema = client.get("/openapi.json").json()
    paths = " ".join(schema["paths"].keys())
    for expected in [
        "/test-report/analyze",
        "/knowledge/search",
        "/failure-analysis/analyze",
        "/requirements/review",
        "/meeting-prep/prepare",
        "/design-review/review",
        "/auth/token",
    ]:
        assert expected in paths


def test_protected_endpoint_requires_auth():
    resp = client.post("/api/v1/requirements/review", json={"requirements": "R1 shall..."})
    assert resp.status_code == 401
