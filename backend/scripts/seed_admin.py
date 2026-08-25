"""Seed an initial admin user (idempotent).

Creates the admin account defined by ADMIN_EMAIL / ADMIN_PASSWORD if it does not
already exist. Safe to run on every startup: it never overwrites an existing user
and is a no-op when ADMIN_PASSWORD is empty.

Usage:
    python -m scripts.seed_admin
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import configure_logging, get_logger
from app.core.security import Role, hash_password
from app.models.user import User

logger = get_logger("engineergpt.seed_admin")


def main() -> None:
    configure_logging()

    if not settings.admin_password:
        logger.info("seed_admin_skipped_no_password")
        return

    with SessionLocal() as db:
        existing = db.execute(
            select(User).where(User.email == settings.admin_email)
        ).scalar_one_or_none()
        if existing is not None:
            logger.info(
                "seed_admin_exists",
                extra={"extra_fields": {"email": settings.admin_email}},
            )
            return

        admin = User(
            email=settings.admin_email,
            full_name=settings.admin_full_name,
            hashed_password=hash_password(settings.admin_password),
            role=Role.ADMIN,
        )
        db.add(admin)
        db.commit()
        logger.info(
            "seed_admin_created",
            extra={"extra_fields": {"email": settings.admin_email}},
        )


if __name__ == "__main__":
    main()
