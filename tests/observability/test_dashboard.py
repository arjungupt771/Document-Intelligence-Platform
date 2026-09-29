from app.observability.dashboard import build_dashboard_snapshot


def test_dashboard_snapshot_has_expected_sections():
    snapshot = build_dashboard_snapshot()

    for key in (
        "documents_processed",
        "extraction_results",
        "extraction_confidence_buckets",
        "retrieval_results",
        "retrieval_quality",
        "verification_results",
        "errors",
    ):
        assert key in snapshot