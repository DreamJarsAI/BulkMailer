"""CSV parsing utilities."""

from __future__ import annotations

import csv
import io
from typing import List

from fastapi import UploadFile
from pydantic import BaseModel

from app.models.domain import Recipient

REQUIRED_COLUMNS = ["title", "first_name", "last_name", "email"]


class CSVParsingError(Exception):
    """Raised when the uploaded CSV cannot be processed."""


class ParsedCSV(BaseModel):
    """Result of parsing a CSV upload."""

    recipients: List[Recipient]
    errors: List[str]


def _normalize_row(row: dict[str, str]) -> dict[str, str]:
    return {key: (value or "").strip() for key, value in row.items()}


def parse_recipients(file: UploadFile) -> ParsedCSV:
    """Parse uploaded CSV file into recipient objects."""

    contents = file.file.read()
    file.file.seek(0)

    try:
        decoded = contents.decode("utf-8-sig")
    except UnicodeDecodeError as exc:  # pragma: no cover - edge case
        raise CSVParsingError("CSV must be UTF-8 encoded") from exc

    reader = csv.DictReader(io.StringIO(decoded))
    headers = [header.strip().lower() for header in reader.fieldnames or []]
    missing = [column for column in REQUIRED_COLUMNS if column not in headers]
    if missing:
        raise CSVParsingError(
            "Missing required columns: " + ", ".join(missing)
        )

    recipients: List[Recipient] = []
    errors: List[str] = []

    for index, raw_row in enumerate(reader, start=2):
        row = _normalize_row({key.strip().lower(): value for key, value in raw_row.items()})
        try:
            recipient = Recipient(**{key: row.get(key, "") for key in REQUIRED_COLUMNS})
        except Exception as exc:  # pragma: no cover - Pydantic error detail formatting
            errors.append(f"Row {index}: {exc}")
            continue
        recipients.append(recipient)

    return ParsedCSV(recipients=recipients, errors=errors)


__all__ = ["parse_recipients", "CSVParsingError", "ParsedCSV"]
