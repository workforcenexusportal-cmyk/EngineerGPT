"""Meeting Preparation HTTP surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.ai.provider import AIProvider, get_ai_provider
from app.core.domain import AgentResult
from app.core.security import Role, require_role
from app.modules.meeting_prep import service

router = APIRouter(prefix="/meeting-prep", tags=["Meeting Preparation Agent"])


class MeetingRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    context: str = Field(default="", max_length=100_000)
    open_issues: list[str] = Field(default_factory=list)


@router.post("/prepare", response_model=AgentResult)
def prepare(
    body: MeetingRequest,
    provider: AIProvider = Depends(get_ai_provider),
    _: object = Depends(require_role(Role.ENGINEER)),
) -> AgentResult:
    return service.prepare_meeting(
        provider=provider,
        topic=body.topic,
        context=body.context,
        open_issues=body.open_issues,
    )
