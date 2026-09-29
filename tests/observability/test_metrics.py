from app.observability.metrics import DOCUMENT_PROCESSED_TOTAL, estimate_tokens


def test_document_processed_counter_increments():
    before = DOCUMENT_PROCESSED_TOTAL.labels(document_type="invoice", status="completed")._value.get()

    DOCUMENT_PROCESSED_TOTAL.labels(document_type="invoice", status="completed").inc()

    after = DOCUMENT_PROCESSED_TOTAL.labels(document_type="invoice", status="completed")._value.get()
    assert after == before + 1


def test_estimate_tokens_is_positive_and_roughly_length_based():
    short = estimate_tokens("hi")
    long = estimate_tokens("a" * 400)

    assert short >= 1
    assert long > short