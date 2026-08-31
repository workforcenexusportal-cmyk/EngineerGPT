"""Knowledge Hub HTTP surface."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.ai.provider import AIProvider, get_ai_provider
from app.core.config import settings
from app.core.database import get_db
from app.core.domain import AgentResult
from app.core.security import CurrentUser, Role, require_role
from app.core.usage import enforce_analysis_quota, enforce_document_quota
from app.modules.history import service as history
from app.modules.knowledge_hub import service
from app.pipeline.validation import FileValidationError

router = APIRouter(prefix="/knowledge", tags=["Knowledge Hub"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class DocumentResponse(BaseModel):
    id: str
    filename: str
    extension: str
    mime: str
    size_bytes: int
    status: str
    chunk_count: int
    created_at: datetime


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    current: CurrentUser,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    _: object = Depends(require_role(Role.ENGINEER)),
    __: object = Depends(enforce_document_quota),
) -> DocumentResponse:
    # FIX: explicitly close the upload after reading to release temporary files.
    try:
        # FIX: cap buffering at one byte over the configured limit (memory-safe upload guard).
        data = await file.read(settings.max_upload_size_bytes + 1)
    finally:
        await file.close()
    if len(data) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_size_mb} MB limit.",
        )
    try:
        # FIX: extraction/embedding are blocking; run the pipeline in a worker thread.
        document = await run_in_threadpool(
            service.ingest_document,
            db=db,
            provider=provider,
            filename=file.filename or "upload",
            data=data,
            owner_id=current.sub,
            org_id=current.org_id,
        )
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        extension=document.extension,
        mime=document.mime,
        size_bytes=document.size_bytes,
        status=document.status,
        chunk_count=len(document.chunks),
        created_at=document.created_at,
    )


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(
    current: CurrentUser,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.VIEWER)),
) -> list[DocumentResponse]:
    rows = service.list_documents(db=db, org_id=current.org_id)
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            extension=doc.extension,
            mime=doc.mime,
            size_bytes=doc.size_bytes,
            status=doc.status,
            chunk_count=count,
            created_at=doc.created_at,
        )
        for doc, count in rows
    ]


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current: CurrentUser,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ENGINEER)),
) -> None:
    deleted = service.delete_document(
        db=db, document_id=document_id, org_id=current.org_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )


@router.post("/search", response_model=AgentResult)
def search(
    body: SearchRequest,
    current: CurrentUser,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    _: object = Depends(require_role(Role.VIEWER)),
    __: object = Depends(enforce_analysis_quota),
) -> AgentResult:
    result = service.semantic_search(
        db=db,
        provider=provider,
        query=body.query,
        top_k=body.top_k,
        # FIX: pass tenant identity through every retrieval path.
        org_id=current.org_id,
    )
    history.record_analysis(
        db,
        module="knowledge_hub",
        title=body.query[:120],
        request=body.model_dump(),
        result=result,
        org_id=current.org_id,
        owner_id=current.sub,
    )
    return result
