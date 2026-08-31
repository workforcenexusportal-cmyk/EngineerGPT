"""History service: persist and retrieve agent results per tenant."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.domain import AgentResult
from app.core.usage import ANALYSIS, record_usage
from app.models.analysis import AnalysisRecord


def record_analysis(
    db: Session,
    *,
    module: str,
    title: str,
    request: dict,
    result: AgentResult,
    org_id: str | None,
    owner_id: str | None,
) -> AnalysisRecord:
    """Persist an agent result and count it toward the org's monthly usage.

    Runs in its own transaction so history/usage bookkeeping never corrupts the
    primary response path.
    """
    record = AnalysisRecord(
        org_id=org_id,
        owner_id=owner_id,
        module=module,
        title=title[:512],
        request=request,
        result=result.model_dump(),
        generated_by=result.generated_by,
    )
    db.add(record)
    record_usage(db, org_id=org_id, owner_id=owner_id, kind=ANALYSIS)
    db.commit()
    db.refresh(record)
    return record


def list_analyses(
    db: Session,
    *,
    org_id: str | None,
    module: str | None = None,
    limit: int = 50,
) -> list[AnalysisRecord]:
    stmt = select(AnalysisRecord).order_by(AnalysisRecord.created_at.desc()).limit(limit)
    stmt = stmt.where(AnalysisRecord.org_id == org_id) if org_id else stmt.where(
        AnalysisRecord.org_id.is_(None)
    )
    if module:
        stmt = stmt.where(AnalysisRecord.module == module)
    return list(db.execute(stmt).scalars().all())


def get_analysis(
    db: Session, *, record_id: str, org_id: str | None
) -> AnalysisRecord | None:
    stmt = select(AnalysisRecord).where(AnalysisRecord.id == record_id)
    if org_id:
        stmt = stmt.where(AnalysisRecord.org_id == org_id)
    return db.execute(stmt).scalar_one_or_none()


def delete_analysis(db: Session, *, record_id: str, org_id: str | None) -> bool:
    record = get_analysis(db, record_id=record_id, org_id=org_id)
    if record is None:
        return False
    db.execute(delete(AnalysisRecord).where(AnalysisRecord.id == record.id))
    db.commit()
    return True
