from pathlib import Path

from evaluation.dataset_loader import DatasetLoader
from evaluation.report import EvaluationReport
from evaluation.runner import EvaluationRunner


DATASET_DIR = Path("evaluation/datasets/invoices")


def test_end_to_end_evaluation():
    loader = DatasetLoader()

    cases = loader.load_directory(DATASET_DIR)

    predictions = {
        "invoice_001.pdf": {
            "vendor": "ACME Corporation",
            "invoice_number": "INV-1042",
            "total": 354000,
        },
        "invoice_002.pdf": {
            "vendor": "Globex Corporation",
            "invoice_number": "INV-2048",
            "total": 125000,
        },
    }

    runner = EvaluationRunner()

    results = runner.evaluate_dataset(
        cases,
        predictions,
    )

    report = EvaluationReport().generate(results)

    assert len(cases) == 2
    assert len(results) == 2

    assert report.total_expected_fields == 6
    assert report.total_predicted_fields == 6

    assert report.matched_fields == 6
    assert report.mismatched_fields == 0
    assert report.missing_fields == 0
    assert report.extra_fields == 0

    assert report.field_accuracy == 1.0
    assert report.precision == 1.0
    assert report.recall == 1.0
    assert report.f1 == 1.0

def test_end_to_end_evaluation_with_extraction_errors():
    loader = DatasetLoader()

    cases = loader.load_directory(DATASET_DIR)

    predictions = {
        "invoice_001.pdf": {
            "vendor": "ACME Corporation",
            "invoice_number": "INV-9999",
            "tax": 18000,
        },
        "invoice_002.pdf": {
            "vendor": "Globex Corporation",
            "invoice_number": "INV-2048",
            "total": 125000,
        },
    }

    runner = EvaluationRunner()

    results = runner.evaluate_dataset(
        cases,
        predictions,
    )

    report = EvaluationReport().generate(results)

    assert len(cases) == 2
    assert len(results) == 2

    assert report.total_expected_fields == 6
    assert report.total_predicted_fields == 6

    assert report.matched_fields == 4
    assert report.mismatched_fields == 1
    assert report.missing_fields == 1
    assert report.extra_fields == 1

    assert report.field_accuracy == 4 / 6
    assert report.precision == 4 / 6
    assert report.recall == 4 / 6
    assert report.f1 == 4 / 6

    assert report.missing_field_rate == 1 / 6
    assert report.hallucinated_field_rate == 1 / 6