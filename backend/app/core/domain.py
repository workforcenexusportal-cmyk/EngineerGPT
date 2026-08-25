"""Shared domain primitives used across modules.

Central definitions of evidence-carrying AI outputs so every module returns
citations + confidence in a consistent shape (the platform's "never hallucinate"
contract is enforced at the type level).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A pointer to the source data that supports an AI claim."""

    source: str = Field(..., description="File name, table, or document reference")
    locator: str | None = Field(
        default=None, description="Page, row, sheet, timestamp, or chunk id"
    )
    excerpt: str | None = Field(default=None, description="Supporting text/value snippet")


class AIInsight(BaseModel):
    """An engineering statement grounded in evidence."""

    statement: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Common envelope returned by every agent module."""

    module: str
    summary: str
    insights: list[AIInsight] = Field(default_factory=list)
    generated_by: str = Field(..., description="Model or 'mock' identifier")
