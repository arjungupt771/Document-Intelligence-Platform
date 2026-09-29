from app.qa.cross_document import CrossDocumentContext
from app.qa.cross_document_validator import CrossDocumentGroundingValidator
from app.qa.models import AnswerSource


def test_requires_evidence_from_two_documents():
    context = CrossDocumentContext(
        query="Compare the invoices.",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="Total is 12000.",
            ),
            AnswerSource(
                document_id="doc-2",
                document_type="invoice",
                text="Total is 15000.",
            ),
        ],
    )

    validator = CrossDocumentGroundingValidator()

    assert validator.validate(context) is True


def test_same_document_chunks_are_not_cross_document_evidence():
    context = CrossDocumentContext(
        query="Compare the invoices.",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="Total is 12000.",
            ),
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="Vendor is ABC Ltd.",
            ),
        ],
    )

    validator = CrossDocumentGroundingValidator()

    assert validator.validate(context) is False


def test_empty_context_is_not_cross_document_grounded():
    context = CrossDocumentContext(
        query="Compare the invoices.",
    )

    validator = CrossDocumentGroundingValidator()

    assert validator.validate(context) is False