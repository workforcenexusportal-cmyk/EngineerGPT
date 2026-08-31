"""Usage tracking and per-plan quota enforcement.

Quotas are counted from the append-only ``usage_events`` table over the current
calendar month, compared against the organization's plan limits. Superusers and
orgs without a tenant (legacy/admin) are never throttled.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.plans import get_limits, is_unlimited
from app.core.security import CurrentUser
from app.core.tenancy import get_organization
from app.models.analysis import UsageEvent
from app.models.document import Document

ANALYSIS = "analysis"
DOCUMENT = "document"


def _month_start(now: datetime | None = None) -> datetime:
    now = now or datetime.now(UTC)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def record_usage(
    db: Session, *, org_id: str | None, owner_id: str | None, kind: str
) -> None:
    """Append a usage event (best-effort; part of the caller's transaction)."""
    db.add(UsageEvent(org_id=org_id, owner_id=owner_id, kind=kind))


def monthly_usage(db: Session, *, org_id: str | None, kind: str) -> int:
    stmt = select(func.count(UsageEvent.id)).where(
        UsageEvent.kind == kind,
        UsageEvent.created_at >= _month_start(),
    )
    stmt = stmt.where(UsageEvent.org_id == org_id) if org_id else stmt.where(
        UsageEvent.org_id.is_(None)
    )
    return int(db.execute(stmt).scalar_one())


def document_count(db: Session, *, org_id: str | None) -> int:
    stmt = select(func.count(Document.id))
    stmt = stmt.where(Document.org_id == org_id) if org_id else stmt.where(
        Document.org_id.is_(None)
    )
    return int(db.execute(stmt).scalar_one())


def enforce_analysis_quota(
    current: CurrentUser, db: Session = Depends(get_db)
) -> CurrentUser:
    """Dependency: block analysis requests once the monthly plan quota is hit."""
    if current.is_superuser or current.org_id is None:
        return current
    org = get_organization(db, current.org_id)
    if org is None:
        return current
    limit = get_limits(org.plan).monthly_analyses
    if is_unlimited(limit):
        return current
    used = monthly_usage(db, org_id=current.org_id, kind=ANALYSIS)
    if used >= limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Monthly analysis limit reached ({limit}). "
                "Upgrade your plan to continue."
            ),
        )
    return current


def enforce_document_quota(
    current: CurrentUser, db: Session = Depends(get_db)
) -> CurrentUser:
    """Dependency: block new document uploads past the plan's storage limit."""
    if current.is_superuser or current.org_id is None:
        return current
    org = get_organization(db, current.org_id)
    if org is None:
        return current
    limit = get_limits(org.plan).max_documents
    if is_unlimited(limit):
        return current
    if document_count(db, org_id=current.org_id) >= limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Document limit reached ({limit}). Upgrade your plan or delete "
                "documents to add more."
            ),
        )
    return current
