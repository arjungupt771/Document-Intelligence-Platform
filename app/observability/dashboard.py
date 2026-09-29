from app.observability.metrics import (
    DOCUMENT_PROCESSED_TOTAL,
    ERROR_TOTAL,
    EXTRACTION_CONFIDENCE,
    EXTRACTION_RESULT_TOTAL,
    RETRIEVAL_QUALITY_HIT_RATE,
    RETRIEVAL_QUALITY_MRR,
    RETRIEVAL_RESULT_TOTAL,
    VERIFICATION_RESULT_TOTAL,
)


def _samples(metric, suffix: str | None = None) -> list[dict]:
    result = []
    for family in metric.collect():
        for sample in family.samples:
            if suffix and not sample.name.endswith(suffix):
                continue
            result.append({"labels": sample.labels, "value": sample.value})
    return result


def _gauge_value(metric) -> float | None:
    samples = _samples(metric)
    return samples[0]["value"] if samples else None


def build_dashboard_snapshot() -> dict:
    """
    A point-in-time JSON summary of the metrics above -- for a quick
    operational check without standing up a full Grafana/Prometheus
    stack. `/metrics` (raw Prometheus exposition format) remains the
    source of truth for anything that needs to be scraped and graphed.
    """
    return {
        "documents_processed": _samples(DOCUMENT_PROCESSED_TOTAL, "_total"),
        "extraction_results": _samples(EXTRACTION_RESULT_TOTAL, "_total"),
        "extraction_confidence_buckets": _samples(EXTRACTION_CONFIDENCE, "_bucket"),
        "retrieval_results": _samples(RETRIEVAL_RESULT_TOTAL, "_total"),
        "retrieval_quality": {
            "hit_rate_at_k": _gauge_value(RETRIEVAL_QUALITY_HIT_RATE),
            "mrr": _gauge_value(RETRIEVAL_QUALITY_MRR),
        },
        "verification_results": _samples(VERIFICATION_RESULT_TOTAL, "_total"),
        "errors": _samples(ERROR_TOTAL, "_total"),
    }