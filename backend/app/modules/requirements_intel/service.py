"""Requirements Intelligence service."""

from __future__ import annotations

import json

from app.ai.prompts import BASE_ENGINEERING_SYSTEM
from app.ai.provider import AIProvider
from app.core.domain import AgentResult
from app.modules.common import AGENT_JSON_CONTRACT, run_text_agent

_SYSTEM = (
    BASE_ENGINEERING_SYSTEM
    + "\nTask: review the requirements set. Identify contradictions, missing "
    "requirements, duplicates, ambiguities, and risks. Each insight must cite the "
    "requirement id(s) or line(s) involved. " + AGENT_JSON_CONTRACT
)


def review_requirements(*, provider: AIProvider, requirements: str) -> AgentResult:
    payload = json.dumps({"requirements_text": requirements[:20000]})
    return run_text_agent(
        provider=provider,
        module="requirements_intel",
        system_prompt=_SYSTEM,
        user_payload=payload,
    )
