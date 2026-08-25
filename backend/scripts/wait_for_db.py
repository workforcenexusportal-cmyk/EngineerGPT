"""Block until the database accepts connections (bounded retry).

Used as the first step of container startup so `alembic upgrade` and the admin
seed run only once Postgres is actually ready.

Usage:
    python -m scripts.wait_for_db
"""

from __future__ import annotations

import sys
import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.database import engine
from app.core.logging import configure_logging, get_logger

logger = get_logger("engineergpt.wait_for_db")


def main(max_retries: int = 60, delay_seconds: float = 2.0) -> None:
    configure_logging()
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("db_ready", extra={"extra_fields": {"attempt": attempt}})
            return
        except OperationalError:
            logger.info(
                "db_not_ready_retrying",
                extra={"extra_fields": {"attempt": attempt, "max": max_retries}},
            )
            time.sleep(delay_seconds)
    logger.error("db_unavailable")
    sys.exit(1)


if __name__ == "__main__":
    main()
