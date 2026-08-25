"""Test Report Agent service: analysis + grounded AI narrative.

The statistical evidence is computed deterministically first; the AI is then
asked to *narrate* that evidence. If the AI call fails or returns unparseable
output, we fall back to a deterministic narrative derived from the statistics so
the endpoint never fails and never fabricates numbers.
"""

from __future__ import annotations

import json

import pandas as pd

from app.ai.prompts import TEST_REPORT_SYSTEM
from app.ai.provider import AIProvider
from app.core.logging import get_logger
from app.modules.test_report import analysis
from app.modules.test_report.schemas import (
    Anomaly,
    ColumnStat,
    Finding,
    TestReportResponse,
)

logger = get_logger("engineergpt.test_report")


def generate_report(
    *,
    title: str,
    extension: str,
    data: bytes,
    provider: AIProvider,
) -> TestReportResponse:
    df = analysis.load_dataframe(extension, data)
    stats = analysis.compute_statistics(df)
    anomalies = analysis.detect_anomalies(df)
    charts = analysis.render_charts(df)

    narrative = _ai_narrative(provider, title, df, stats, anomalies)

    return TestReportResponse(
        title=title,
        row_count=int(df.shape[0]),
        column_count=int(df.shape[1]),
        executive_summary=narrative["executive_summary"],
        statistics=stats,
        findings=narrative["findings"],
        anomalies=anomalies,
        charts=charts,
        conclusions=narrative["conclusions"],
        recommendations=narrative["recommendations"],
        generated_by=provider.name,
    )


def _ai_narrative(
    provider: AIProvider,
    title: str,
    df: pd.DataFrame,
    stats: list[ColumnStat],
    anomalies: list[Anomaly],
) -> dict:
    evidence = _build_evidence(title, df, stats, anomalies)
    try:
        raw = provider.complete(TEST_REPORT_SYSTEM, evidence, temperature=0.1)
        parsed = json.loads(_strip_code_fence(raw))
        return {
            "executive_summary": str(parsed.get("executive_summary", "")).strip()
            or _fallback_summary(df, anomalies),
            "findings": _coerce_findings(parsed.get("findings", [])),
            "conclusions": [str(c) for c in parsed.get("conclusions", [])]
            or _fallback_conclusions(anomalies),
            "recommendations": [str(r) for r in parsed.get("recommendations", [])]
            or _fallback_recommendations(anomalies),
        }
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.info("ai_narrative_unparseable_using_deterministic_fallback")
        return {
            "executive_summary": _fallback_summary(df, anomalies),
            "findings": _fallback_findings(stats),
            "conclusions": _fallback_conclusions(anomalies),
            "recommendations": _fallback_recommendations(anomalies),
        }


def _build_evidence(
    title: str, df: pd.DataFrame, stats: list[ColumnStat], anomalies: list[Anomaly]
) -> str:
    return json.dumps(
        {
            "title": title,
            "rows": int(df.shape[0]),
            "columns": [s.model_dump() for s in stats],
            "detected_anomalies": [a.model_dump() for a in anomalies],
        },
        default=str,
    )


def _coerce_findings(items: object) -> list[Finding]:
    findings: list[Finding] = []
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                findings.append(
                    Finding(
                        statement=str(item.get("statement", "")).strip(),
                        confidence=float(item.get("confidence", 0.5)),
                        citation=str(item.get("citation", "dataset")),
                    )
                )
            except (TypeError, ValueError):
                continue
    return findings


# --- deterministic fallbacks (never fabricate) -----------------------------
def _fallback_summary(df: pd.DataFrame, anomalies: list[Anomaly]) -> str:
    return (
        f"Analyzed {df.shape[0]} rows across {df.shape[1]} measured signals. "
        f"{len(anomalies)} column(s) exhibit statistical outliers. "
        "Narrative generated deterministically from computed statistics."
    )


def _fallback_findings(stats: list[ColumnStat]) -> list[Finding]:
    findings: list[Finding] = []
    for s in stats:
        if s.mean is not None and s.std is not None:
            findings.append(
                Finding(
                    statement=(
                        f"'{s.name}' mean={s.mean:.3g}, std={s.std:.3g}, "
                        f"range=[{s.minimum:.3g}, {s.maximum:.3g}]."
                    ),
                    confidence=0.9,
                    citation=f"column:{s.name}",
                )
            )
    return findings[:8]


def _fallback_conclusions(anomalies: list[Anomaly]) -> list[str]:
    if not anomalies:
        return ["No statistical outliers detected within the ±3σ threshold."]
    high = [a.column for a in anomalies if a.severity == "high"]
    if high:
        return [f"High-severity anomalies detected in: {', '.join(high)}."]
    return ["Minor outliers detected; within tolerance pending engineering review."]


def _fallback_recommendations(anomalies: list[Anomaly]) -> list[str]:
    if not anomalies:
        return ["Dataset appears nominal. Proceed with standard validation sign-off."]
    return [
        f"Investigate outliers in '{a.column}' ({a.severity} severity)." for a in anomalies[:5]
    ]


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.endswith("```"):
            t = t.rsplit("```", 1)[0]
    return t.strip()
