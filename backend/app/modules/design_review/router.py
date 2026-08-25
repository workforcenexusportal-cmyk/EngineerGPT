"""Design Review HTTP surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.ai.provider import AIProvider, get_ai_provider
from app.core.domain import AgentResult
from app.core.security import Role, require_role
from app.modules.design_review import service

router = APIRouter(prefix="/design-review", tags=["Design Review Agent"])


class DesignReviewRequest(BaseModel):
    design: str = Field(..., min_length=10, max_length=100_000)
    specifications: str = Field(default="", max_length=100_000)


@router.post("/review", response_model=AgentResult)
def review(
    body: DesignReviewRequest,
    provider: AIProvider = Depends(get_ai_provider),
    _: object = Depends(require_role(Role.ENGINEER)),
) -> AgentResult:
    return service.review_design(
        provider=provider, design=body.design, specifications=body.specifications
    )
