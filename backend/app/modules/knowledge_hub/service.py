"""Knowledge Hub service: embed the query, retrieve nearest chunks, synthesize.

Retrieval uses pgvector cosine distance on PostgreSQL and a portable in-Python
cosine ranking on SQLite/other backends. The AI answer is constrained to the
retrieved context so it cannot fabricate beyond the corpus.
"""

from __future__ import annotations

import math

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.ai.prompts import BASE_ENGINEERING_SYSTEM
from app.ai.provider import AIProvider
from app.core.domain import AgentResult, AIInsight, Citation
from app.models.document import Document, DocumentChunk
from app.pipeline.ingestion import ingest


def ingest_document(
    *,
    db: Session,
    provider: AIProvider,
    filename: str,
    data: bytes,
    owner_id: str | None = None,
    org_id: str | None = None,
) -> Document:
    """Validate, extract, chunk, embed and persist a document + its chunks.

    Runs in a single transaction so a partial ingest never leaves orphaned rows.
    """
    result = ingest(filename, data, provider)

    document = Document(
        org_id=org_id,
        owner_id=owner_id,
        filename=result.file.filename,
        extension=result.file.extension,
        mime=result.file.mime,
        size_bytes=result.file.size_bytes,
        status="processed",
    )
    for chunk, embedding in zip(result.chunks, result.embeddings, strict=True):
        document.chunks.append(
            DocumentChunk(
                chunk_index=chunk.index,
                content=chunk.text,
                embedding=embedding,
            )
        )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def list_documents(
    *, db: Session, org_id: str | None = None, limit: int = 100
) -> list[tuple[Document, int]]:
    """Return documents (optionally scoped to an org) with their chunk counts."""
    stmt = (
        select(Document, func.count(DocumentChunk.id))
        .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.created_at.desc())
        .limit(limit)
    )
    if org_id is not None:
        stmt = stmt.where(Document.org_id == org_id)
    return [(doc, count) for doc, count in db.execute(stmt).all()]


def delete_document(*, db: Session, document_id: str, org_id: str | None = None) -> bool:
    """Delete a document (and cascaded chunks). Returns False if not found."""
    stmt = select(Document).where(Document.id == document_id)
    if org_id is not None:
        stmt = stmt.where(Document.org_id == org_id)
    document = db.execute(stmt).scalar_one_or_none()
    if document is None:
        return False
    db.execute(delete(Document).where(Document.id == document.id))
    db.commit()
    return True


def semantic_search(
    *, db: Session, provider: AIProvider, query: str, top_k: int = 5
) -> AgentResult:
    query_vec = provider.embed([query])[0]
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        hits = _search_pgvector(db, query_vec, top_k)
    else:
        hits = _search_python(db, query_vec, top_k)

    if not hits:
        return AgentResult(
            module="knowledge_hub",
            summary="No indexed documents matched the query. Upload documents to build the corpus.",
            insights=[],
            generated_by=provider.name,
        )

    context = "\n\n".join(f"[chunk {c.chunk_index}] {c.content}" for c in hits)
    system = (
        BASE_ENGINEERING_SYSTEM
        + "\nAnswer ONLY from the provided context. If it is insufficient, say so."
    )
    answer = provider.complete(system, f"Question: {query}\n\nContext:\n{context}")

    citations = [
        Citation(source=f"document:{c.document_id}", locator=f"chunk:{c.chunk_index}")
        for c in hits
    ]
    return AgentResult(
        module="knowledge_hub",
        summary=answer.strip(),
        insights=[AIInsight(statement=answer.strip(), confidence=0.7, citations=citations)],
        generated_by=provider.name,
    )


def _search_pgvector(
    db: Session, query_vec: list[float], top_k: int
) -> list[DocumentChunk]:
    """Native pgvector nearest-neighbour search (cosine distance)."""
    stmt = (
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vec))
        .limit(top_k)
    )
    return list(db.execute(stmt).scalars().all())


def _search_python(
    db: Session, query_vec: list[float], top_k: int
) -> list[DocumentChunk]:
    """Portable cosine-similarity search for SQLite / non-pgvector backends.

    Scans the chunk table and ranks in Python. Suitable for local/dev corpora;
    production uses the indexed pgvector path above.
    """
    chunks = list(db.execute(select(DocumentChunk)).scalars().all())
    q_norm = math.sqrt(sum(v * v for v in query_vec)) or 1.0

    def similarity(chunk: DocumentChunk) -> float:
        vec = chunk.embedding
        dot = sum(a * b for a, b in zip(query_vec, vec, strict=False))
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return dot / (q_norm * norm)

    ranked = sorted(chunks, key=similarity, reverse=True)
    return ranked[:top_k]
