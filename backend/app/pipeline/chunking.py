"""Token-aware text chunking for embedding and retrieval.

Uses a character-based sliding window with overlap. This is deterministic and
dependency-free; a token-precise splitter can be substituted later without
changing the public signature.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    index: int
    text: str
    char_start: int
    char_end: int


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[Chunk] = []
    start = 0
    index = 0
    step = chunk_size - overlap
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunks.append(
            Chunk(index=index, text=normalized[start:end], char_start=start, char_end=end)
        )
        if end == len(normalized):
            break
        start += step
        index += 1
    return chunks
