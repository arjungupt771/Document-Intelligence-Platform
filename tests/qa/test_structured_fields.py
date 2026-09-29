from app.qa.models import AnswerRequest
from app.qa.structured_fields import StructuredFieldResolver


def test_resolves_invoice_number():
    resolver = StructuredFieldResolver()

    result = resolver.resolve(
        AnswerRequest(query="What is the invoice number?")
    )

    assert result == "invoice_number"


def test_resolves_total_amount():
    resolver = StructuredFieldResolver()

    result = resolver.resolve(
        AnswerRequest(query="What is the invoice total?")
    )

    assert result == "total_amount"


def test_resolves_vendor():
    resolver = StructuredFieldResolver()

    result = resolver.resolve(
        AnswerRequest(query="Who is the vendor?")
    )

    assert result == "vendor"


def test_resolves_due_date():
    resolver = StructuredFieldResolver()

    result = resolver.resolve(
        AnswerRequest(query="When is the due date?")
    )

    assert result == "due_date"


def test_returns_none_for_unknown_field():
    resolver = StructuredFieldResolver()

    result = resolver.resolve(
        AnswerRequest(query="Tell me something about this invoice.")
    )

    assert result is None