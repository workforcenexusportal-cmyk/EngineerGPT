"""Shared helpers for agent modules that produce evidence-backed narratives."""

from __future__ import annotations

import json

from app.ai.provider import AIProvider
from app.core.domain import AgentResult, AIInsight, Citation


def run_text_agent(
    *,
    provider: AIProvider,
    module: str,
    system_prompt: str,
    user_payload: str,
) -> AgentResult:
    """Call the AI provider and coerce its JSON into a uniform AgentResult.

    Falls back to a safe, non-fabricated envelope when the model output cannot be
    parsed, preserving the platform's reliability contract.
    """
    raw = provider.complete(system_prompt, user_payload, temperature=0.15)
    try:
        parsed = json.loads(_strip_fence(raw))
        summary = str(parsed.get("summary", "")).strip()
        insights = [
            AIInsight(
                statement=str(item.get("statement", "")).strip(),
                confidence=float(item.get("confidence", 0.5)),
                citations=[
                    Citation(source=str(c.get("source", "input")), locator=c.get("locator"))
                    for c in item.get("citations", [])
                    if isinstance(c, dict)
                ],
            )
            for item in parsed.get("insights", [])
            if isinstance(item, dict)
        ]
    except (json.JSONDecodeError, TypeError, ValueError):
        summary = (
            "Model output could not be parsed into structured insights. "
            "Raw response withheld to avoid unverified claims."
        )
        insights = []

    return AgentResult(
        module=module, summary=summary, insights=insights, generated_by=provider.name
    )


def _strip_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.endswith("```"):
            t = t.rsplit("```", 1)[0]
    return t.strip()


AGENT_JSON_CONTRACT = (
    "Respond as strict JSON: {\"summary\": string, \"insights\": "
    "[{\"statement\": string, \"confidence\": number 0..1, "
    "\"citations\": [{\"source\": string, \"locator\": string}]}]}."
)
