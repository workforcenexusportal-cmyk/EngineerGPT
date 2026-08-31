"""Tenant (organization) lifecycle helpers."""

from __future__ import annotations

import re
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.plans import Plan
from app.models.organization import Organization


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "org"


def _unique_slug(db: Session, base: str) -> str:
    """Return a slug not already taken, appending a short suffix on collision."""
    candidate = slugify(base)[:64]
    exists = db.execute(
        select(Organization.id).where(Organization.slug == candidate)
    ).first()
    if exists is None:
        return candidate
    return f"{candidate[:56]}-{secrets.token_hex(3)}"


def create_organization(
    db: Session, *, name: str, plan: Plan = Plan.FREE, commit: bool = True
) -> Organization:
    """Create a new tenant with a unique slug. Caller sets user.org_id."""
    org = Organization(
        name=name.strip() or "My Organization",
        slug=_unique_slug(db, name),
        plan=plan.value,
    )
    db.add(org)
    db.flush()
    if commit:
        db.commit()
        db.refresh(org)
    return org


def get_organization(db: Session, org_id: str | None) -> Organization | None:
    if not org_id:
        return None
    return db.get(Organization, org_id)
