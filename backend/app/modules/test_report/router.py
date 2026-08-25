"""Test Report Agent HTTP surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile

from app.ai.provider import AIProvider, get_ai_provider
from app.core.security import Role, require_role
from app.modules.test_report import pdf, service
from app.modules.test_report.schemas import TestReportResponse
from app.pipeline.validation import FileValidationError, validate_upload

router = APIRouter(prefix="/test-report", tags=["Test Report Agent"])

_ANALYZABLE = {".csv", ".xlsx"}


def _provider() -> AIProvider:
    return get_ai_provider()


async def _read_tabular(file: UploadFile) -> tuple[str, bytes]:
    data = await file.read()
    try:
        validated = validate_upload(file.filename or "upload", data)
    except FileValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if validated.extension not in _ANALYZABLE:
        raise HTTPException(
            status_code=422,
            detail=f"Test Report Agent accepts {sorted(_ANALYZABLE)}; got {validated.extension}.",
        )
    return validated.extension, data


@router.post("/analyze", response_model=TestReportResponse)
async def analyze(
    file: UploadFile = File(...),
    title: str = Form("Untitled Test"),
    provider: AIProvider = Depends(_provider),
    _: object = Depends(require_role(Role.ENGINEER)),
) -> TestReportResponse:
    """Analyze an uploaded CSV/XLSX and return a structured test report."""
    extension, data = await _read_tabular(file)
    try:
        return service.generate_report(
            title=title, extension=extension, data=data, provider=provider
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/export/pdf")
async def export_pdf(
    file: UploadFile = File(...),
    title: str = Form("Untitled Test"),
    provider: AIProvider = Depends(_provider),
    _: object = Depends(require_role(Role.ENGINEER)),
) -> Response:
    """Analyze and return the report as a downloadable PDF."""
    extension, data = await _read_tabular(file)
    try:
        report = service.generate_report(
            title=title, extension=extension, data=data, provider=provider
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    pdf_bytes = pdf.build_pdf(report)
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:60]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_title or "report"}.pdf"'},
    )
