"""Ingestion orchestrator: ties validation → extraction → chunking → embedding.

Kept independent of HTTP so it can be called from API endpoints, background
workers, or batch jobs alike.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.provider import AIProvider
from app.core.logging import get_logger
from app.pipeline.chunking import Chunk, chunk_text
from app.pipeline.extraction import extract_text
from app.pipeline.validation import ValidatedFile, validate_upload

logger = get_logger("engineergpt.pipeline.ingest")


@dataclass
class IngestionResult:
    file: ValidatedFile
    text: str
    chunks: list[Chunk]
    embeddings: list[list[float]]


def ingest(filename: str, data: bytes, provider: AIProvider) -> IngestionResult:
    """Run the full ingestion pipeline for a single uploaded file."""
    validated = validate_upload(filename, data)
    text = extract_text(validated.extension, data)
    chunks = chunk_text(text)
    embeddings = provider.embed([c.text for c in chunks]) if chunks else []
    logger.info(
        "ingested",
        extra={
            "extra_fields": {
                "filename": validated.filename,
                "chunks": len(chunks),
                "chars": len(text),
            }
        },
    )
    return IngestionResult(file=validated, text=text, chunks=chunks, embeddings=embeddings)
