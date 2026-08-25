"""Failure Analysis service."""

from __future__ import annotations

import json

from app.ai.prompts import BASE_ENGINEERING_SYSTEM
from app.ai.provider import AIProvider
from app.core.domain import AgentResult
from app.modules.common import AGENT_JSON_CONTRACT, run_text_agent

_SYSTEM = (
    BASE_ENGINEERING_SYSTEM
    + "\nTask: given DTC codes, sensor readings, and logs, propose the most probable "
    "cause(s), likely root cause, and concrete engineering next steps. Rank by "
    "likelihood and cite the specific evidence (DTC, signal, threshold). "
    + AGENT_JSON_CONTRACT
)


def analyze_failure(
    *,
    provider: AIProvider,
    dtc_codes: list[str],
    sensor_data: dict[str, float],
    logs: str,
) -> AgentResult:
    payload = json.dumps(
        {"dtc_codes": dtc_codes, "sensor_data": sensor_data, "logs": logs[:8000]}
    )
    return run_text_agent(
        provider=provider,
        module="failure_analysis",
        system_prompt=_SYSTEM,
        user_payload=payload,
    )
