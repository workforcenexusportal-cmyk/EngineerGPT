"""Meeting Preparation service."""

from __future__ import annotations

import json

from app.ai.prompts import BASE_ENGINEERING_SYSTEM
from app.ai.provider import AIProvider
from app.core.domain import AgentResult
from app.modules.common import AGENT_JSON_CONTRACT, run_text_agent

_SYSTEM = (
    BASE_ENGINEERING_SYSTEM
    + "\nTask: prepare an engineering meeting. From the supplied reports, documents, "
    "and open issues produce an agenda, talking points, key risks, open decisions, "
    "and follow-up actions. Cite the source item for each point. " + AGENT_JSON_CONTRACT
)


def prepare_meeting(
    *, provider: AIProvider, topic: str, context: str, open_issues: list[str]
) -> AgentResult:
    payload = json.dumps(
        {"topic": topic, "context": context[:16000], "open_issues": open_issues}
    )
    return run_text_agent(
        provider=provider,
        module="meeting_prep",
        system_prompt=_SYSTEM,
        user_payload=payload,
    )
