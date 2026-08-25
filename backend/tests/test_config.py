"""Tests for production database URL normalization and pgvector gating."""

from __future__ import annotations

import pytest

from app.core.config import Settings, _normalize_db_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "postgres://u:p@host:5432/db",
            "postgresql+psycopg://u:p@host:5432/db",
        ),
        (
            "postgresql://u:p@host:5432/db",
            "postgresql+psycopg://u:p@host:5432/db",
        ),
        (
            "postgresql+psycopg://u:p@host:5432/db",
            "postgresql+psycopg://u:p@host:5432/db",
        ),
        ("sqlite:///./engineergpt.db", "sqlite:///./engineergpt.db"),
    ],
)
def test_normalize_db_url(raw: str, expected: str) -> None:
    assert _normalize_db_url(raw) == expected


def test_database_url_override_is_normalized() -> None:
    s = Settings(DATABASE_URL="postgres://u:p@h:5432/db")
    assert s.database_url == "postgresql+psycopg://u:p@h:5432/db"
    assert s.is_postgres is True
    assert s.is_sqlite is False


def test_pgvector_disabled_by_default_on_postgres() -> None:
    s = Settings(DATABASE_URL="postgres://u:p@h:5432/db", use_pgvector=False)
    assert s.pgvector_enabled is False


def test_pgvector_enabled_requires_postgres_and_flag() -> None:
    on_pg = Settings(DATABASE_URL="postgres://u:p@h:5432/db", use_pgvector=True)
    assert on_pg.pgvector_enabled is True

    on_sqlite = Settings(sqlite_path="./x.db", postgres_host="", use_pgvector=True)
    assert on_sqlite.pgvector_enabled is False
