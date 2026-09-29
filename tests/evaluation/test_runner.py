from pathlib import Path

from evaluation.dataset_loader import DatasetLoader
from evaluation.runner import EvaluationRunner


DATASET_DIR = Path("evaluation/datasets/invoices")


def test_evaluate_single_case():
    case = DatasetLoader().load_file(
        DATASET_DIR / "invoice_001.json"
    )

    runner = EvaluationRunner()

    result = runner.evaluate_case(
        case,
        predicted={
            "vendor": "ACME Corporation",
            "invoice_number": "INV-1042",
            "total": 354000,
        },
    )

    assert result.metrics.total_expected_fields == 3
    assert result.metrics.total_predicted_fields == 3
    assert result.metrics.matched_fields == 3
    assert result.metrics.mismatched_fields == 0
    assert result.metrics.missing_fields == 0
    assert result.metrics.extra_fields == 0
    assert result.metrics.f1 == 1.0

def test_evaluate_single_case_with_errors():
    case = DatasetLoader().load_file(
        DATASET_DIR / "invoice_001.json"
    )

    runner = EvaluationRunner()

    result = runner.evaluate_case(
        case,
        predicted={
            "vendor": "ACME Corporation",
            "invoice_number": "INV-9999",
            "tax": 18000,
        },
    )

    assert result.metrics.matched_fields == 1
    assert result.metrics.mismatched_fields == 1
    assert result.metrics.missing_fields == 1
    assert result.metrics.extra_fields == 1

def test_evaluate_dataset():
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

    assert len(results) == 2

    assert results["invoice_001.pdf"].metrics.f1 == 1.0
    assert results["invoice_002.pdf"].metrics.f1 == 1.0