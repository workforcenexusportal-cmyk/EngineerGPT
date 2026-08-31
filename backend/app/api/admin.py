"""Platform admin panel API (superuser only): tenants, users, and usage stats."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.plans import Plan
from app.core.security import require_superuser
from app.core.usage import ANALYSIS, monthly_usage
from app.models.analysis import AnalysisRecord
from app.models.document import Document
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(
    prefix="/admin", tags=["Admin"], dependencies=[Depends(require_superuser)]
)


class PlatformStats(BaseModel):
    organizations: int
    users: int
    documents: int
    analyses_total: int
    analyses_this_month: int


class OrgRow(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    subscription_status: str | None
    members: int
    documents: int
    created_at: datetime


class UserRow(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    org_id: str | None
    is_superuser: bool
    created_at: datetime


class SetPlanRequest(BaseModel):
    plan: Plan


@router.get("/stats", response_model=PlatformStats)
def stats(db: Session = Depends(get_db)) -> PlatformStats:
    return PlatformStats(
        organizations=int(db.execute(select(func.count(Organization.id))).scalar_one()),
        users=int(db.execute(select(func.count(User.id))).scalar_one()),
        documents=int(db.execute(select(func.count(Document.id))).scalar_one()),
        analyses_total=int(
            db.execute(select(func.count(AnalysisRecord.id))).scalar_one()
        ),
        analyses_this_month=monthly_usage(db, org_id=None, kind=ANALYSIS)
        + _month_analyses_all_orgs(db),
    )


def _month_analyses_all_orgs(db: Session) -> int:
    # UsageEvent with a null org is counted by monthly_usage(org_id=None); this
    # adds tenant-scoped events for a true platform-wide monthly total.
    from datetime import UTC

    from app.models.analysis import UsageEvent

    start = datetime.now(UTC).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    stmt = select(func.count(UsageEvent.id)).where(
        UsageEvent.kind == ANALYSIS,
        UsageEvent.created_at >= start,
        UsageEvent.org_id.is_not(None),
    )
    return int(db.execute(stmt).scalar_one())


@router.get("/organizations", response_model=list[OrgRow])
def list_organizations(db: Session = Depends(get_db)) -> list[OrgRow]:
    orgs = list(
        db.execute(
            select(Organization).order_by(Organization.created_at.desc())
        ).scalars()
    )
    rows: list[OrgRow] = []
    for org in orgs:
        members = int(
            db.execute(
                select(func.count(User.id)).where(User.org_id == org.id)
            ).scalar_one()
        )
        docs = int(
            db.execute(
                select(func.count(Document.id)).where(Document.org_id == org.id)
            ).scalar_one()
        )
        rows.append(
            OrgRow(
                id=org.id,
                name=org.name,
                slug=org.slug,
                plan=org.plan,
                subscription_status=org.subscription_status,
                members=members,
                documents=docs,
                created_at=org.created_at,
            )
        )
    return rows


@router.get("/users", response_model=list[UserRow])
def list_users(db: Session = Depends(get_db)) -> list[UserRow]:
    users = list(
        db.execute(select(User).order_by(User.created_at.desc()).limit(500)).scalars()
    )
    return [
        UserRow(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=str(u.role),
            org_id=u.org_id,
            is_superuser=u.is_superuser,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("/organizations/{org_id}/plan", response_model=OrgRow)
def set_org_plan(
    org_id: str, body: SetPlanRequest, db: Session = Depends(get_db)
) -> OrgRow:
    org = db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found.")
    org.plan = body.plan.value
    db.add(org)
    db.commit()
    db.refresh(org)
    members = int(
        db.execute(
            select(func.count(User.id)).where(User.org_id == org.id)
        ).scalar_one()
    )
    docs = int(
        db.execute(
            select(func.count(Document.id)).where(Document.org_id == org.id)
        ).scalar_one()
    )
    return OrgRow(
        id=org.id,
        name=org.name,
        slug=org.slug,
        plan=org.plan,
        subscription_status=org.subscription_status,
        members=members,
        documents=docs,
        created_at=org.created_at,
    )
