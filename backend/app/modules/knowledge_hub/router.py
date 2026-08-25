"""Knowledge Hub HTTP surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, get_ai_provider
from app.core.database import get_db
from app.core.domain import AgentResult
from app.core.security import Role, require_role
from app.modules.knowledge_hub import service

router = APIRouter(prefix="/knowledge", tags=["Knowledge Hub"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


@router.post("/search", response_model=AgentResult)
def search(
    body: SearchRequest,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    _: object = Depends(require_role(Role.VIEWER)),
) -> AgentResult:
    return service.semantic_search(
        db=db, provider=provider, query=body.query, top_k=body.top_k
    )
