from app.routing.classifier import QueryClassifier
from app.routing.models import QueryType


def test_structured_query():
    classifier = QueryClassifier()

    result = classifier.classify(
        "What is the total amount of invoice INV-1042?"
    )

    assert result == QueryType.STRUCTURED


def test_semantic_query():
    classifier = QueryClassifier()

    result = classifier.classify(
        "What does the contract say about termination?"
    )

    assert result == QueryType.SEMANTIC


def test_cross_document_query():
    classifier = QueryClassifier()

    result = classifier.classify(
        "Compare invoice INV-1042 and invoice INV-2048"
    )

    assert result == QueryType.CROSS_DOCUMENT


def test_cross_document_takes_priority():
    classifier = QueryClassifier()

    result = classifier.classify(
        "Compare the total amount between invoices"
    )

    assert result == QueryType.CROSS_DOCUMENT


def test_case_insensitive():
    classifier = QueryClassifier()

    result = classifier.classify(
        "WHAT IS THE TOTAL AMOUNT?"
    )

    assert result == QueryType.STRUCTURED


def test_whitespace_is_ignored():
    classifier = QueryClassifier()

    result = classifier.classify(
        "   What is the total amount?   "
    )

    assert result == QueryType.STRUCTURED


def test_empty_query():
    classifier = QueryClassifier()

    assert classifier.classify("") == QueryType.UNKNOWN


def test_whitespace_query():
    classifier = QueryClassifier()

    assert classifier.classify("   ") == QueryType.UNKNOWN


def test_unknown_query():
    classifier = QueryClassifier()

    result = classifier.classify(
        "Tell me something interesting"
    )

    assert result == QueryType.UNKNOWN

def test_cross_document_comparison_with_amount():
    classifier = QueryClassifier()

    result = classifier.classify(
        "Compare the amount between invoices"
    )

    assert result == QueryType.CROSS_DOCUMENT


def test_cross_document_comparison_with_status():
    classifier = QueryClassifier()

    result = classifier.classify(
        "Compare the status between invoices"
    )

    assert result == QueryType.CROSS_DOCUMENT


def test_cross_document_comparison_with_date():
    classifier = QueryClassifier()

    result = classifier.classify(
        "Compare the due date between invoices"
    )

    assert result == QueryType.CROSS_DOCUMENT


def test_semantic_query_with_no_structured_keyword():
    classifier = QueryClassifier()

    result = classifier.classify(
        "Explain the termination clause"
    )

    assert result == QueryType.SEMANTIC