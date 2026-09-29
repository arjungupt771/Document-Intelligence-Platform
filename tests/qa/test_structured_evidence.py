import uuid
from types import SimpleNamespace

from app.qa.structured_evidence import StructuredEvidenceAdapter


def test_extraction_is_converted_to_grounding_context():
    document_id = uuid.uuid4()

    extraction = SimpleNamespace(
        document_id=document_id,
        document_type=SimpleNamespace(value="invoice"),
        data={
            "invoice_number": "INV-1001",
            "total_amount": 12000,
            "vendor": "ABC Ltd",
        },
    )

    adapter = StructuredEvidenceAdapter()

    context = adapter.from_extraction(
        query="What is the invoice total?",
        extraction=extraction,
    )

    assert context.query == "What is the invoice total?"
    assert context.is_empty is False
    assert len(context.sources) == 1

    source = context.sources[0]

    assert source.document_id == str(document_id)
    assert source.document_type == "invoice"
    assert source.page_number is None
    assert source.score is None

    assert '"invoice_number": "INV-1001"' in source.text
    assert '"total_amount": 12000' in source.text
    assert '"vendor": "ABC Ltd"' in source.text


def test_empty_extraction_data_produces_valid_evidence():
    extraction = SimpleNamespace(
        document_id=uuid.uuid4(),
        document_type=SimpleNamespace(value="invoice"),
        data={},
    )

    adapter = StructuredEvidenceAdapter()

    context = adapter.from_extraction(
        query="What information is available?",
        extraction=extraction,
    )

    assert context.is_empty is False
    assert len(context.sources) == 1
    assert context.sources[0].text == "{}"



def test_creates_field_level_evidence():
    adapter = StructuredEvidenceAdapter()

    extraction = SimpleNamespace(
        document_id=uuid.uuid4(),
        document_type=SimpleNamespace(value="invoice"),
        data={
            "invoice_number": "INV-001",
            "total_amount": 12000,
            "vendor": "ABC Ltd",
        },
    )

    context = adapter.from_extraction(
        query="What is the invoice total?",
        extraction=extraction,
        field="total_amount",
    )

    assert len(context.sources) == 1
    assert context.sources[0].text == (
        "Field: total_amount\n"
        "Value: 12000"
    )

