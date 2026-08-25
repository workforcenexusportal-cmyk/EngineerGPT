"""Shared pytest fixtures."""

from __future__ import annotations

import csv
import io
import random

import pytest

from app.ai.provider import MockProvider


@pytest.fixture
def mock_provider() -> MockProvider:
    return MockProvider()


@pytest.fixture
def sample_csv_bytes() -> bytes:
    """A small numeric dataset with a couple of deliberate outliers."""
    random.seed(42)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["time", "voltage", "current", "temperature"])
    for i in range(50):
        v = 12.0 + random.gauss(0, 0.1)
        c = 2.0 + random.gauss(0, 0.05)
        t = 45.0 + random.gauss(0, 0.5)
        if i == 25:  # inject outliers
            v, t = 25.0, 120.0
        writer.writerow([i, round(v, 3), round(c, 3), round(t, 3)])
    return buffer.getvalue().encode("utf-8")
