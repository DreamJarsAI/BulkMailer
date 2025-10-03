import io

from fastapi import UploadFile

from app.services.csv_loader import CSVParsingError, parse_recipients


def make_upload(contents: str, filename: str = "recipients.csv") -> UploadFile:
    buffer = io.BytesIO(contents.encode("utf-8"))
    return UploadFile(filename=filename, file=buffer)


def test_parse_recipients_success() -> None:
    csv_content = "title,first_name,last_name,email\nDr.,Ada,Lovelace,ada@example.com\n"
    upload = make_upload(csv_content)
    result = parse_recipients(upload)
    assert len(result.recipients) == 1
    recipient = result.recipients[0]
    assert recipient.email == "ada@example.com"
    assert result.errors == []


def test_parse_recipients_missing_column() -> None:
    csv_content = "first_name,last_name,email\nAda,Lovelace,ada@example.com\n"
    upload = make_upload(csv_content)
    try:
        parse_recipients(upload)
    except CSVParsingError as exc:
        assert "Missing required columns" in str(exc)
    else:
        raise AssertionError("Expected CSVParsingError")
