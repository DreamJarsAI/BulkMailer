"""Utilities for handling DOCX template uploads."""

from __future__ import annotations

from io import BytesIO

from docx import Document


class DocxProcessingError(Exception):
    """Raised when a DOCX file cannot be parsed."""


def extract_plain_text(docx_bytes: bytes) -> str:
    """Convert a DOCX file into plain text preserving basic paragraph breaks."""

    try:
        document = Document(BytesIO(docx_bytes))
    except Exception as exc:  # pragma: no cover - library specific
        raise DocxProcessingError("Unable to read DOCX file") from exc

    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs]
    text = "\n".join(filter(None, paragraphs))
    return text.strip()


__all__ = ["extract_plain_text", "DocxProcessingError"]
