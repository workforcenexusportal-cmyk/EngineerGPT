"""History HTTP surface: list, fetch, and delete saved analyses."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.domain import AgentResult
from app.core.security import CurrentUser, Role, require_role
from app.modules.history import service

router = APIRouter(prefix="/history", tags=["History"])


class HistoryItem(BaseModel):
    id: str
    module: str
    title: str
    generated_by: str
    created_at: datetime


class HistoryDetail(HistoryItem):
    request: dict
    result: AgentResult


@router.get("", response_model=list[HistoryItem])
def list_history(
    current: CurrentUser,
    module: str | None = Query(default=None, max_length=48),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.VIEWER)),
) -> list[HistoryItem]:
    rows = service.list_analyses(
        db=db, org_id=current.org_id, module=module, limit=limit
    )
    return [
        HistoryItem(
            id=r.id,
            module=r.module,
            title=r.title,
            generated_by=r.generated_by,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/{record_id}", response_model=HistoryDetail)
def get_history(
    record_id: str,
    current: CurrentUser,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.VIEWER)),
) -> HistoryDetail:
    r = service.get_analysis(db=db, record_id=record_id, org_id=current.org_id)
    if r is None:
        raise HTTPException(status_code=404, detail="History record not found.")
    return HistoryDetail(
        id=r.id,
        module=r.module,
        title=r.title,
        generated_by=r.generated_by,
        created_at=r.created_at,
        request=r.request,
        result=AgentResult.model_validate(r.result),
    )


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history(
    record_id: str,
    current: CurrentUser,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ENGINEER)),
) -> None:
    if not service.delete_analysis(db=db, record_id=record_id, org_id=current.org_id):
        raise HTTPException(status_code=404, detail="History record not found.")
