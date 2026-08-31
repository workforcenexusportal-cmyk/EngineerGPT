"""Failure Analysis HTTP surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, get_ai_provider
from app.core.database import get_db
from app.core.domain import AgentResult
from app.core.security import CurrentUser, Role, require_role
from app.core.usage import enforce_analysis_quota
from app.modules.failure_analysis import service
from app.modules.history import service as history

router = APIRouter(prefix="/failure-analysis", tags=["Failure Analysis Agent"])


class FailureRequest(BaseModel):
    dtc_codes: list[str] = Field(default_factory=list)
    sensor_data: dict[str, float] = Field(default_factory=dict)
    logs: str = Field(default="", max_length=100_000)


@router.post("/analyze", response_model=AgentResult)
def analyze(
    body: FailureRequest,
    current: CurrentUser,
    provider: AIProvider = Depends(get_ai_provider),
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ENGINEER)),
    __: object = Depends(enforce_analysis_quota),
) -> AgentResult:
    result = service.analyze_failure(
        provider=provider,
        dtc_codes=body.dtc_codes,
        sensor_data=body.sensor_data,
        logs=body.logs,
    )
    history.record_analysis(
        db,
        module="failure_analysis",
        title=", ".join(body.dtc_codes) or "Failure analysis",
        request=body.model_dump(),
        result=result,
        org_id=current.org_id,
        owner_id=current.sub,
    )
    return result
