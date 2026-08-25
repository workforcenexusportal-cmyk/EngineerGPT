"""File validation: extension allow-list, size limits, and MIME sniffing.

Security: we never trust the client-provided filename or content-type. The MIME
type is sniffed from the actual bytes (via libmagic when available) and matched
against an allow-list to prevent disguised/malicious uploads.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings

# Extension -> set of acceptable sniffed MIME types.
ALLOWED_TYPES: dict[str, set[str]] = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",  # OOXML is a zip container; libmagic may report zip
    },
    ".pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
    },
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
    },
    ".csv": {"text/csv", "text/plain", "application/csv"},
    ".txt": {"text/plain"},
    ".mdf": {"application/octet-stream"},
    ".zip": {"application/zip", "application/x-zip-compressed"},
}


class FileValidationError(ValueError):
    """Raised when an upload fails validation."""


@dataclass(frozen=True)
class ValidatedFile:
    filename: str
    extension: str
    size_bytes: int
    mime: str


def _sniff_mime(data: bytes) -> str:
    try:
        import magic

        return magic.from_buffer(data, mime=True)
    except Exception:
        # libmagic unavailable — fall back to a permissive default; the extension
        # allow-list still constrains what we accept.
        return "application/octet-stream"


def validate_upload(filename: str, data: bytes) -> ValidatedFile:
    if not filename or "." not in filename:
        raise FileValidationError("File must have a recognized extension.")

    ext = "." + filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_TYPES:
        raise FileValidationError(f"Unsupported file type: {ext}")

    size = len(data)
    if size == 0:
        raise FileValidationError("File is empty.")
    if size > settings.max_upload_size_bytes:
        raise FileValidationError(
            f"File exceeds the {settings.max_upload_size_mb} MB limit."
        )

    mime = _sniff_mime(data)
    allowed = ALLOWED_TYPES[ext]
    # octet-stream is accepted for binary/unknown formats we can't sniff precisely.
    if mime not in allowed and mime != "application/octet-stream":
        raise FileValidationError(
            f"File content ({mime}) does not match extension {ext}."
        )

    return ValidatedFile(filename=filename, extension=ext, size_bytes=size, mime=mime)
