from app.parsing.errors import (
    CorruptedDocumentError,
    EmptyDocumentError,
    ParserError,
    UnsupportedFileTypeError,
)


def test_unsupported_file_type_error_message():
    error = UnsupportedFileTypeError(".exe")

    assert isinstance(error, ParserError)
    assert ".exe" in str(error)


def test_corrupted_document_error_message():
    error = CorruptedDocumentError("bad.pdf", "not a pdf")

    assert isinstance(error, ParserError)
    assert "bad.pdf" in str(error)
    assert "not a pdf" in str(error)


def test_empty_document_error_message():
    error = EmptyDocumentError("empty.pdf")

    assert isinstance(error, ParserError)
    assert "empty.pdf" in str(error)
