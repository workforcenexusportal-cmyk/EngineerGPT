"""Tests for the deterministic mock AI provider."""

from __future__ import annotations

from app.core.config import settings


def test_mock_embedding_dimensions(mock_provider):
    vectors = mock_provider.embed(["hello world", "engineering data"])
    assert len(vectors) == 2
    assert all(len(v) == settings.embedding_dimensions for v in vectors)


def test_mock_embedding_is_deterministic(mock_provider):
    a = mock_provider.embed(["repeatable input"])[0]
    b = mock_provider.embed(["repeatable input"])[0]
    assert a == b


def test_mock_completion_returns_json_string(mock_provider):
    out = mock_provider.complete("system", "analyze this dataset")
    assert isinstance(out, str)
    assert "summary" in out
