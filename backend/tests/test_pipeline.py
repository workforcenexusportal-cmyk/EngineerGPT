"""Unit tests for the document pipeline: validation, extraction, chunking."""

from __future__ import annotations

import pytest

from app.pipeline.chunking import chunk_text
from app.pipeline.extraction import extract_text
from app.pipeline.validation import FileValidationError, validate_upload


def test_validate_rejects_unknown_extension():
    with pytest.raises(FileValidationError):
        validate_upload("malware.exe", b"MZ...")


def test_validate_rejects_empty_file():
    with pytest.raises(FileValidationError):
        validate_upload("empty.csv", b"")


def test_validate_accepts_csv(sample_csv_bytes):
    result = validate_upload("data.csv", sample_csv_bytes)
    assert result.extension == ".csv"
    assert result.size_bytes == len(sample_csv_bytes)


def test_extract_csv_roundtrip(sample_csv_bytes):
    text = extract_text(".csv", sample_csv_bytes)
    assert "voltage" in text
    assert "temperature" in text


def test_chunking_overlap_and_bounds():
    text = "word " * 1000
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    assert all(c.char_end > c.char_start for c in chunks)
    assert chunks[0].index == 0


def test_chunking_empty_text_returns_no_chunks():
    assert chunk_text("   ") == []


def test_chunking_invalid_overlap_raises():
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=100, overlap=100)
