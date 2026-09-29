
from app.qa.context import GroundingContext
from app.qa.deterministic_verifier import DeterministicEvidenceVerifier
from app.qa.models import AnswerSource


def create_context(text: str) -> GroundingContext:
    return GroundingContext(
        query="What is the invoice total?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text=text,
            )
        ],
    )


def test_supported_answer_is_verified():
    context = create_context(
        "The invoice total is 12000."
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        answer="The invoice total is 12000.",
        context=context,
    )

    assert result.verified is True
    assert result.unsupported_claims == []


def test_capitalization_and_punctuation_are_ignored():
    context = create_context(
        "The Invoice Total is 12,000."
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        answer="the invoice total is 12000!",
        context=context,
    )

    assert result.verified is True


def test_different_word_order_is_supported():
    context = create_context(
        "The invoice total is 12000."
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        answer="The total invoice is 12000.",
        context=context,
    )

    assert result.verified is True


def test_unsupported_value_is_rejected():
    context = create_context(
        "The invoice total is 12000."
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        answer="The invoice total is 15000.",
        context=context,
    )

    assert result.verified is False
    assert "The invoice total is 15000" in result.unsupported_claims


def test_unsupported_vendor_is_rejected():
    context = GroundingContext(
        query="Who is the vendor?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="Vendor is ABC Ltd.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        answer="The vendor is XYZ Ltd.",
        context=context,
    )

    assert result.verified is False
    assert "The vendor is XYZ Ltd" in result.unsupported_claims


def test_empty_context_is_not_verified():
    context = GroundingContext(
        query="What is the invoice total?",
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        answer="The invoice total is 12000.",
        context=context,
    )

    assert result.verified is False
    assert result.reason == "No evidence is available for verification."


def test_empty_answer_is_not_verified():
    context = create_context(
        "The invoice total is 12000."
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        answer="",
        context=context,
    )

    assert result.verified is False
    assert result.reason == "The generated answer is empty."


def test_multiple_claims_require_all_claims_to_be_supported():
    context = create_context(
        "The invoice total is 12000. The vendor is ABC Ltd."
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        answer=(
            "The invoice total is 12000. "
            "The vendor is XYZ Ltd."
        ),
        context=context,
    )

    assert result.verified is False
    assert "The vendor is XYZ Ltd" in result.unsupported_claims

def test_normalize_preserves_comma_separated_numbers():
    assert (
        DeterministicEvidenceVerifier._normalize(
            "The invoice total is ₹12,000."
        )
        == "the invoice total is 12000"
    )


def test_normalize_is_case_insensitive():
    assert (
        DeterministicEvidenceVerifier._normalize(
            "Invoice TOTAL"
        )
        == "invoice total"
    )


def test_normalize_collapses_whitespace():
    assert (
        DeterministicEvidenceVerifier._normalize(
            "The   invoice    total   is   ₹12,000."
        )
        == "the invoice total is 12000"
    )

def test_extract_numbers_handles_integers_and_decimals():
    assert DeterministicEvidenceVerifier._extract_numbers(
        "Total is 12000 and tax is 18.5 percent."
    ) == ["12000", "18.5"]


def test_extract_numbers_handles_comma_formatted_values():
    normalized = DeterministicEvidenceVerifier._normalize(
        "Total is ₹12,000."
    )

    assert DeterministicEvidenceVerifier._extract_numbers(normalized) == [
        "12000"
    ]


def test_extract_numbers_returns_empty_for_text_without_numbers():
    assert DeterministicEvidenceVerifier._extract_numbers(
        "The vendor is Acme."
    ) == []

def test_rejects_different_numeric_value():
    context = GroundingContext(
        query="What is the invoice total?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The invoice total is ₹12,000.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The invoice total is ₹50,000.",
        context,
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "The invoice total is ₹50,000"
    ]


def test_accepts_same_numeric_value_with_different_formatting():
    context = GroundingContext(
        query="What is the invoice total?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The invoice total is ₹12,000.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The invoice total is 12000.",
        context,
    )

    assert result.verified is True
    assert result.unsupported_claims == []

def test_normalize_phrases_handles_invoice_total_equivalence():
    normalized = DeterministicEvidenceVerifier._normalize(
        "The invoice total is ₹12,000."
    )

    assert (
        DeterministicEvidenceVerifier._normalize_phrases(normalized)
        == "the total amount is 12000"
    )


def test_normalize_phrases_handles_supplier_vendor_equivalence():
    normalized = DeterministicEvidenceVerifier._normalize(
        "The supplier is Acme."
    )

    assert (
        DeterministicEvidenceVerifier._normalize_phrases(normalized)
        == "the vendor is acme"
    )


def test_normalize_phrases_handles_payment_due_date_equivalence():
    normalized = DeterministicEvidenceVerifier._normalize(
        "The payment due date is 30 days."
    )

    assert (
        DeterministicEvidenceVerifier._normalize_phrases(normalized)
        == "the due date is 30 days"
    )

def test_verifier_accepts_semantically_equivalent_invoice_total():
    context = GroundingContext(
        query="What is the invoice total?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The invoice total is ₹12,000.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The total amount of the invoice is 12000.",
        context,
    )

    assert result.verified is True
    assert result.unsupported_claims == []

def test_normalize_phrases_handles_invoice_id_number_equivalence():
    normalized = DeterministicEvidenceVerifier._normalize(
        "The invoice ID is INV-1001."
    )

    assert (
        DeterministicEvidenceVerifier._normalize_phrases(normalized)
        == "the invoice number is inv 1001"
    )

def test_verifier_accepts_semantically_equivalent_invoice_id():
    context = GroundingContext(
        query="What is the invoice number?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The invoice number is INV-1001.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The invoice ID is INV-1001.",
        context,
    )

    assert result.verified is True
    assert result.unsupported_claims == []

def test_verifier_rejects_different_invoice_id():
    context = GroundingContext(
        query="What is the invoice number?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The invoice number is INV-1001.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The invoice ID is INV-2002.",
        context,
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "The invoice ID is INV-2002"
    ]

def test_verifier_accepts_multiple_supported_values_in_one_claim():
    context = GroundingContext(
        query="What are the invoice number and total amount?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text=(
                    "The invoice number is INV-1001. "
                    "The total amount is ₹12,000."
                ),
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The invoice number is INV-1001 and the total amount is 12000.",
        context,
    )

    assert result.verified is True
    assert result.unsupported_claims == []


def test_verifier_rejects_one_unsupported_value_in_multi_value_claim():
    context = GroundingContext(
        query="What are the invoice number and total amount?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text=(
                    "The invoice number is INV-1001. "
                    "The total amount is ₹12,000."
                ),
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The invoice number is INV-1001 and the total amount is 50000.",
        context,
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "the total amount is 50000"
    ]


def test_verifier_rejects_unsupported_invoice_number_in_multi_value_claim():
    context = GroundingContext(
        query="What are the invoice number and total amount?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text=(
                    "The invoice number is INV-1001. "
                    "The total amount is ₹12,000."
                ),
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The invoice number is INV-9999 and the total amount is 12000.",
        context,
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "The invoice number is INV-9999"
    ]

def test_verifier_rejects_negation_conflict():
    context = GroundingContext(
        query="Is the invoice overdue?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The invoice is not overdue.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The invoice is overdue.",
        context,
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "The invoice is overdue"
    ]


def test_verifier_accepts_supported_negated_claim():
    context = GroundingContext(
        query="Is the invoice overdue?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The invoice is not overdue.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The invoice is not overdue.",
        context,
    )

    assert result.verified is True
    assert result.unsupported_claims == []


def test_verifier_rejects_missing_negation():
    context = GroundingContext(
        query="Is payment pending?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="Payment is not pending.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "Payment is pending.",
        context,
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "Payment is pending"
    ]

def test_verifier_accepts_matching_temporal_qualifier():
    context = GroundingContext(
        query="When is the payment due?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="Payment is due before 30 September 2026.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "Payment is due before 30 September 2026.",
        context,
    )

    assert result.verified is True
    assert result.unsupported_claims == []


def test_verifier_rejects_opposite_temporal_qualifier():
    context = GroundingContext(
        query="When is the payment due?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="Payment is due before 30 September 2026.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "Payment is due after 30 September 2026.",
        context,
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "Payment is due after 30 September 2026"
    ]


def test_verifier_rejects_different_temporal_value():
    context = GroundingContext(
        query="When is the payment due?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="Payment is due before 30 September 2026.",
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "Payment is due before 30 October 2026.",
        context,
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "Payment is due before 30 October 2026"
    ]

def test_verifier_accepts_matching_condition():
    context = GroundingContext(
        query="When does the late fee apply?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text=(
                    "A late fee applies if payment is received "
                    "after the due date."
                ),
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "A late fee applies if payment is received after the due date.",
        context,
    )

    assert result.verified is True
    assert result.unsupported_claims == []


def test_verifier_rejects_conflicting_condition():
    context = GroundingContext(
        query="When does the late fee apply?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text=(
                    "A late fee applies if payment is received "
                    "after the due date."
                ),
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "A late fee applies if payment is received before the due date.",
        context,
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "A late fee applies if payment is received before the due date"
    ]


def test_verifier_rejects_missing_condition():
    context = GroundingContext(
        query="When does the late fee apply?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text=(
                    "A late fee applies if payment is received "
                    "after the due date."
                ),
            )
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "A late fee applies.",
        context,
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "A late fee applies"
    ]

def test_verifier_accepts_claim_supported_by_multiple_evidence_fragments():
    context = GroundingContext(
        query="What are the invoice number and total amount?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The invoice number is INV-1001.",
            ),
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The total amount is ₹12,000.",
            ),
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The invoice number is INV-1001 and the total amount is 12000.",
        context,
    )

    assert result.verified is True
    assert result.unsupported_claims == []


def test_verifier_rejects_when_one_fragment_is_unsupported():
    context = GroundingContext(
        query="What are the invoice number and total amount?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The invoice number is INV-1001.",
            ),
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The total amount is ₹12,000.",
            ),
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The invoice number is INV-1001 and the total amount is 50000.",
        context,
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "the total amount is 50000"
    ]


def test_verifier_accepts_claims_from_different_document_fragments():
    context = GroundingContext(
        query="What are the vendor and invoice total?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The vendor is Acme Corp.",
            ),
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The total amount is ₹12,000.",
            ),
        ],
    )

    verifier = DeterministicEvidenceVerifier()

    result = verifier.verify(
        "The vendor is Acme Corp and the total amount is 12000.",
        context,
    )

    assert result.verified is True
    assert result.unsupported_claims == []