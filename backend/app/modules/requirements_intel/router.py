"""Requirements Intelligence HTTP surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.ai.provider import AIProvider, get_ai_provider
from app.core.domain import AgentResult
from app.core.security import Role, require_role
from app.modules.requirements_intel import service

router = APIRouter(prefix="/requirements", tags=["Requirements Intelligence Agent"])


class RequirementsRequest(BaseModel):
    requirements: str = Field(..., min_length=10, max_length=100_000)


@router.post("/review", response_model=AgentResult)
def review(
    body: RequirementsRequest,
    provider: AIProvider = Depends(get_ai_provider),
    _: object = Depends(require_role(Role.ENGINEER)),
) -> AgentResult:
    return service.review_requirements(provider=provider, requirements=body.requirements)
