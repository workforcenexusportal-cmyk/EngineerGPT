"""Design Review HTTP surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, get_ai_provider
from app.core.database import get_db
from app.core.domain import AgentResult
from app.core.security import CurrentUser, Role, require_role
from app.core.usage import enforce_analysis_quota
from app.modules.design_review import service
from app.modules.history import service as history

router = APIRouter(prefix="/design-review", tags=["Design Review Agent"])


class DesignReviewRequest(BaseModel):
    design: str = Field(..., min_length=10, max_length=100_000)
    specifications: str = Field(default="", max_length=100_000)


@router.post("/review", response_model=AgentResult)
def review(
    body: DesignReviewRequest,
    current: CurrentUser,
    provider: AIProvider = Depends(get_ai_provider),
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ENGINEER)),
    __: object = Depends(enforce_analysis_quota),
) -> AgentResult:
    result = service.review_design(
        provider=provider, design=body.design, specifications=body.specifications
    )
    history.record_analysis(
        db,
        module="design_review",
        title="Design review",
        request=body.model_dump(),
        result=result,
        org_id=current.org_id,
        owner_id=current.sub,
    )
    return result
