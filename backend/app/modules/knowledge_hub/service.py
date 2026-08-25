"""Knowledge Hub service: embed the query, retrieve nearest chunks, synthesize.

Retrieval uses pgvector cosine distance. The AI answer is constrained to the
retrieved context so it cannot fabricate beyond the corpus.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.prompts import BASE_ENGINEERING_SYSTEM
from app.ai.provider import AIProvider
from app.core.domain import AgentResult, AIInsight, Citation
from app.models.document import DocumentChunk


def semantic_search(
    *, db: Session, provider: AIProvider, query: str, top_k: int = 5
) -> AgentResult:
    query_vec = provider.embed([query])[0]
    stmt = (
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vec))
        .limit(top_k)
    )
    hits = db.execute(stmt).scalars().all()

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
