"""Public data types for the Test Report Agent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ColumnStat(BaseModel):
    name: str
    count: int
    mean: float | None = None
    std: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    missing: int = 0


class Anomaly(BaseModel):
    column: str
    description: str
    severity: str = Field(..., description="low | medium | high")
    sample_indices: list[int] = Field(default_factory=list)


class ChartArtifact(BaseModel):
    title: str
    kind: str = Field(..., description="line | histogram | correlation")
    image_base64: str = Field(..., description="PNG image encoded as base64 (no data URI prefix)")


class Finding(BaseModel):
    statement: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    citation: str


class TestReportResponse(BaseModel):
    report_id: str | None = None
    title: str
    row_count: int
    column_count: int
    executive_summary: str
    statistics: list[ColumnStat]
    findings: list[Finding]
    anomalies: list[Anomaly]
    charts: list[ChartArtifact]
    conclusions: list[str]
    recommendations: list[str]
    generated_by: str
