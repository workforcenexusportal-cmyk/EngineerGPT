"""End-to-end SaaS flow tests: signup creates a tenant, quota, history, admin.

Uses a temporary SQLite database wired through FastAPI's dependency override so
the full HTTP surface (auth, agents, history, admin) is exercised without any
external services.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  (register tables on Base.metadata)
from app.core.database import Base, get_db
from app.core.security import Role, TokenData, create_access_token, hash_password
from app.main import app
from app.models.user import User


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'saas.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, future=True)

    def override_get_db() -> Iterator[Session]:
        db = maker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        c.maker = maker  # type: ignore[attr-defined]
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def _register(client: TestClient, email: str = "eng@acme.com") -> dict:
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "supersecret1",
            "full_name": "Ada Lovelace",
            "company_name": "Acme Robotics",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_signup_creates_org_and_returns_token(client: TestClient) -> None:
    body = _register(client)
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["role"] == Role.MANAGER.value
    assert body["user"]["org_id"]


def test_duplicate_email_rejected(client: TestClient) -> None:
    _register(client)
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "eng@acme.com", "password": "supersecret1"},
    )
    assert resp.status_code == 409


def test_context_reports_free_plan_and_usage(client: TestClient) -> None:
    token = _register(client)["access_token"]
    resp = client.get("/api/v1/auth/context", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan"]["key"] == "free"
    assert data["organization"]["name"] == "Acme Robotics"
    assert data["usage"]["analyses_this_month"] == 0


def test_analysis_is_recorded_in_history(client: TestClient) -> None:
    token = _register(client)["access_token"]
    resp = client.post(
        "/api/v1/requirements/review",
        headers=_auth(token),
        json={"requirements": "R1 shall keep coolant below 105C at all loads."},
    )
    assert resp.status_code == 200, resp.text

    hist = client.get("/api/v1/history", headers=_auth(token))
    assert hist.status_code == 200
    items = hist.json()
    assert len(items) == 1
    assert items[0]["module"] == "requirements_intel"

    ctx = client.get("/api/v1/auth/context", headers=_auth(token)).json()
    assert ctx["usage"]["analyses_this_month"] == 1


def test_history_is_tenant_isolated(client: TestClient) -> None:
    token_a = _register(client, "a@acme.com")["access_token"]
    token_b = _register(client, "b@other.com")["access_token"]
    client.post(
        "/api/v1/requirements/review",
        headers=_auth(token_a),
        json={"requirements": "R1 shall do the thing correctly."},
    )
    # Org B must not see Org A's history.
    hist_b = client.get("/api/v1/history", headers=_auth(token_b)).json()
    assert hist_b == []


def test_billing_plans_catalog_public(client: TestClient) -> None:
    resp = client.get("/api/v1/billing/plans")
    assert resp.status_code == 200
    keys = {p["key"] for p in resp.json()}
    assert {"free", "pro", "team"} <= keys
    # Without Stripe configured, paid plans are not purchasable.
    assert all(not p["purchasable"] for p in resp.json())


def test_admin_requires_superuser(client: TestClient) -> None:
    token = _register(client)["access_token"]
    assert client.get("/api/v1/admin/stats", headers=_auth(token)).status_code == 403


def test_superuser_can_read_admin_stats(client: TestClient) -> None:
    _register(client)
    # Create a platform superuser directly and mint a token for them.
    maker = client.maker  # type: ignore[attr-defined]
    with maker() as db:
        su = User(
            email="root@engineergpt.local",
            full_name="Root",
            hashed_password=hash_password("supersecret1"),
            role=Role.ADMIN,
            is_superuser=True,
        )
        db.add(su)
        db.commit()
        token = create_access_token(
            TokenData(sub=su.id, role=Role.ADMIN, org_id=None, is_superuser=True)
        )
    resp = client.get("/api/v1/admin/stats", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["organizations"] >= 1
