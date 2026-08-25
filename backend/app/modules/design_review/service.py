"""Design Review service."""

from __future__ import annotations

import json

from app.ai.prompts import BASE_ENGINEERING_SYSTEM
from app.ai.provider import AIProvider
from app.core.domain import AgentResult
from app.modules.common import AGENT_JSON_CONTRACT, run_text_agent

_SYSTEM = (
    BASE_ENGINEERING_SYSTEM
    + "\nTask: perform an engineering design review of the supplied design document "
    "and specifications. Produce a review checklist, engineering risks, missing "
    "information, and proposed improvements. Cite the relevant section. "
    + AGENT_JSON_CONTRACT
)


def review_design(*, provider: AIProvider, design: str, specifications: str) -> AgentResult:
    payload = json.dumps(
        {"design_document": design[:16000], "specifications": specifications[:16000]}
    )
    return run_text_agent(
        provider=provider,
        module="design_review",
        system_prompt=_SYSTEM,
        user_payload=payload,
    )
