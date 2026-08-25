"""End-to-end Knowledge Hub tests on SQLite (portable, no external services).

These prove the dialect-portable Embedding type and the in-Python vector search
fallback work, so the platform runs locally without Postgres/pgvector.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  (register tables on Base.metadata)
from app.ai.provider import MockProvider
from app.core.database import Base
from app.models.document import DocumentChunk
from app.modules.knowledge_hub import service

SAMPLE = (
    b"The hydraulic pressure relief valve opens at 210 bar to protect the pump. "
    b"Coolant temperature must stay below 105 C during continuous load. "
    b"Battery isolation contactor opens within 50 ms on an insulation fault."
)


@pytest.fixture
def sqlite_session(tmp_path) -> Iterator[Session]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, future=True)
    with maker() as session:
        yield session
    engine.dispose()


def test_embedding_roundtrip_on_sqlite(sqlite_session: Session) -> None:
    provider = MockProvider()
    doc = service.ingest_document(
        db=sqlite_session,
        provider=provider,
        filename="specs.txt",
        data=SAMPLE,
    )
    chunk = sqlite_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    ).scalars().first()
    assert chunk is not None
    assert isinstance(chunk.embedding, list)
    assert len(chunk.embedding) == len(provider.embed(["x"])[0])


def test_ingest_list_search_delete(sqlite_session: Session) -> None:
    provider = MockProvider()

    doc = service.ingest_document(
        db=sqlite_session, provider=provider, filename="specs.txt", data=SAMPLE
    )
    assert doc.id
    assert len(doc.chunks) >= 1

    rows = service.list_documents(db=sqlite_session)
    assert len(rows) == 1
    listed_doc, chunk_count = rows[0]
    assert listed_doc.id == doc.id
    assert chunk_count == len(doc.chunks)

    result = service.semantic_search(
        db=sqlite_session, provider=provider, query="hydraulic relief valve", top_k=3
    )
    assert result.module == "knowledge_hub"
    assert result.generated_by == "mock"
    # A hit was found, so it is not the empty-corpus message.
    assert "Upload documents" not in result.summary
    assert result.insights and result.insights[0].citations

    assert service.delete_document(db=sqlite_session, document_id=doc.id) is True
    assert service.list_documents(db=sqlite_session) == []


def test_search_empty_corpus(sqlite_session: Session) -> None:
    result = service.semantic_search(
        db=sqlite_session, provider=MockProvider(), query="anything", top_k=3
    )
    assert result.insights == []
    assert "Upload documents" in result.summary
