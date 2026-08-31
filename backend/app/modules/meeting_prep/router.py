"""Meeting Preparation HTTP surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, get_ai_provider
from app.core.database import get_db
from app.core.domain import AgentResult
from app.core.security import CurrentUser, Role, require_role
from app.core.usage import enforce_analysis_quota
from app.modules.history import service as history
from app.modules.meeting_prep import service

router = APIRouter(prefix="/meeting-prep", tags=["Meeting Preparation Agent"])


class MeetingRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    context: str = Field(default="", max_length=100_000)
    open_issues: list[str] = Field(default_factory=list)


@router.post("/prepare", response_model=AgentResult)
def prepare(
    body: MeetingRequest,
    current: CurrentUser,
    provider: AIProvider = Depends(get_ai_provider),
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ENGINEER)),
    __: object = Depends(enforce_analysis_quota),
) -> AgentResult:
    result = service.prepare_meeting(
        provider=provider,
        topic=body.topic,
        context=body.context,
        open_issues=body.open_issues,
    )
    history.record_analysis(
        db,
        module="meeting_prep",
        title=body.topic,
        request=body.model_dump(),
        result=result,
        org_id=current.org_id,
        owner_id=current.sub,
    )
    return result
