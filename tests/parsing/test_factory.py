import pytest

from app.parsing.docx_parser import DOCXParser
from app.parsing.errors import UnsupportedFileTypeError
from app.parsing.factory import ParserFactory
from app.parsing.pdf_parser import PDFParser


def test_factory_resolves_pdf_parser():
    factory = ParserFactory()

    parser = factory.get_parser("invoice.pdf")

    assert isinstance(parser, PDFParser)


def test_factory_resolves_docx_parser_case_insensitively():
    factory = ParserFactory()

    parser = factory.get_parser("contract.DOCX")

    assert isinstance(parser, DOCXParser)


def test_factory_raises_for_unsupported_extension():
    factory = ParserFactory()

    with pytest.raises(UnsupportedFileTypeError):
        factory.get_parser("malware.exe")


def test_factory_can_be_constructed_with_a_custom_parser_set():
    pdf_parser = PDFParser()
    factory = ParserFactory(parsers=[pdf_parser])

    assert factory.get_parser("a.pdf") is pdf_parser
    with pytest.raises(UnsupportedFileTypeError):
        factory.get_parser("a.docx")
