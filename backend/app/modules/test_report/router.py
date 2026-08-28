"""Test Report Agent HTTP surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from starlette.concurrency import run_in_threadpool

from app.ai.provider import AIProvider, get_ai_provider
from app.core.config import settings
from app.core.security import Role, require_role
from app.modules.test_report import pdf, service
from app.modules.test_report.schemas import TestReportResponse
from app.pipeline.validation import FileValidationError, validate_upload

router = APIRouter(prefix="/test-report", tags=["Test Report Agent"])

_ANALYZABLE = {".csv", ".xlsx"}


def _provider() -> AIProvider:
    return get_ai_provider()


async def _read_tabular(file: UploadFile) -> tuple[str, bytes]:
    # FIX: close the spooled upload explicitly after reading to avoid descriptor leaks.
    try:
        # FIX: read one byte over the cap so oversized uploads are rejected without
        # buffering an unbounded request body in memory.
        data = await file.read(settings.max_upload_size_bytes + 1)
    finally:
        await file.close()
    if len(data) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the size limit.")
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
    # FIX: constrain multipart titles before they reach report generation/PDF output.
    title: str = Form("Untitled Test", max_length=200),
    provider: AIProvider = Depends(_provider),
    _: object = Depends(require_role(Role.ENGINEER)),
) -> TestReportResponse:
    """Analyze an uploaded CSV/XLSX and return a structured test report."""
    extension, data = await _read_tabular(file)
    try:
        # FIX: pandas/matplotlib are synchronous and CPU-heavy; keep them off the event loop.
        return await run_in_threadpool(
            service.generate_report,
            title=title.strip() or "Untitled Test",
            extension=extension,
            data=data,
            provider=provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/export/pdf")
async def export_pdf(
    file: UploadFile = File(...),
    # FIX: constrain multipart titles before they reach report generation/PDF output.
    title: str = Form("Untitled Test", max_length=200),
    provider: AIProvider = Depends(_provider),
    _: object = Depends(require_role(Role.ENGINEER)),
) -> Response:
    """Analyze and return the report as a downloadable PDF."""
    extension, data = await _read_tabular(file)
    try:
        # FIX: reuse the worker pool for the blocking dataframe/chart pipeline.
        report = await run_in_threadpool(
            service.generate_report,
            title=title.strip() or "Untitled Test",
            extension=extension,
            data=data,
            provider=provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # FIX: reportlab PDF rendering is synchronous; do not block other requests.
    pdf_bytes = await run_in_threadpool(pdf.build_pdf, report)
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:60]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_title or "report"}.pdf"'},
    )
