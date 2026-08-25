"""Failure Analysis HTTP surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.ai.provider import AIProvider, get_ai_provider
from app.core.domain import AgentResult
from app.core.security import Role, require_role
from app.modules.failure_analysis import service

router = APIRouter(prefix="/failure-analysis", tags=["Failure Analysis Agent"])


class FailureRequest(BaseModel):
    dtc_codes: list[str] = Field(default_factory=list)
    sensor_data: dict[str, float] = Field(default_factory=dict)
    logs: str = Field(default="", max_length=100_000)


@router.post("/analyze", response_model=AgentResult)
def analyze(
    body: FailureRequest,
    provider: AIProvider = Depends(get_ai_provider),
    _: object = Depends(require_role(Role.ENGINEER)),
) -> AgentResult:
    return service.analyze_failure(
        provider=provider,
        dtc_codes=body.dtc_codes,
        sensor_data=body.sensor_data,
        logs=body.logs,
    )
