"""Dialect-portable column types.

The platform targets Postgres + pgvector in production, but must also run with
zero external services locally (SQLite). :class:`Embedding` stores vectors as a
native ``pgvector`` column on PostgreSQL and as a JSON-encoded ``TEXT`` column on
every other dialect, so the same ORM models work in both environments.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.core.config import settings


class Embedding(TypeDecorator[list[float]]):
    """A float-vector column that adapts to the active database dialect."""

    impl = Text
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql" and settings.use_pgvector:
            from pgvector.sqlalchemy import Vector

            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(Text())

    def process_bind_param(
        self, value: list[float] | None, dialect: Any
    ) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql" and settings.use_pgvector:
            return value  # pgvector's own bind processor handles the list
        return json.dumps(list(value))

    def process_result_value(self, value: Any, dialect: Any) -> list[float] | None:
        if value is None:
            return None
        if dialect.name == "postgresql" and settings.use_pgvector:
            return list(value)
        return list(json.loads(value))
