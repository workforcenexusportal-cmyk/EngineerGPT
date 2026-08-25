"""Create database schema (dev/first-run helper).

Ensures the pgvector extension exists, then creates all ORM tables from the
SQLAlchemy metadata. In production, use Alembic migrations instead.

Usage:
    python -m scripts.init_db
"""

from __future__ import annotations

import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

# Import models so they register on Base.metadata.
import app.models  # noqa: F401
from app.core.database import Base, engine
from app.core.logging import configure_logging, get_logger

logger = get_logger("engineergpt.init_db")


def main(max_retries: int = 30, delay_seconds: float = 2.0) -> None:
    """Wait for the database, enable pgvector, and create all tables.

    Retries on connection errors so the container can start before Postgres is
    fully accepting connections without failing the boot.
    """
    configure_logging()
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            with engine.begin() as conn:
                if conn.dialect.name == "postgresql":
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            Base.metadata.create_all(bind=engine)
            logger.info("schema_created", extra={"extra_fields": {"attempt": attempt}})
            return
        except OperationalError as exc:  # database not ready yet
            last_error = exc
            logger.info(
                "db_not_ready_retrying",
                extra={"extra_fields": {"attempt": attempt, "max": max_retries}},
            )
            time.sleep(delay_seconds)
    raise RuntimeError(f"Database did not become available: {last_error}")


if __name__ == "__main__":
    main()
