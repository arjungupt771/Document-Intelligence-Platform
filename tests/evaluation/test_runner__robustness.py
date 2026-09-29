from pathlib import Path

from evaluation.dataset_loader import DatasetLoader
from evaluation.runner import EvaluationRunner


DATASET_DIR = Path("evaluation/datasets/invoices")


def test_missing_prediction_is_skipped():
    loader = DatasetLoader()
    cases = loader.load_directory(DATASET_DIR)

    predictions = {
        "invoice_001.pdf": {
            "vendor": "ACME Corporation",
            "invoice_number": "INV-1042",
            "total": 354000,
        }
    }

    results = EvaluationRunner().evaluate_dataset(
        cases,
        predictions,
    )

    assert len(results) == 1
    assert "invoice_001.pdf" in results
    assert "invoice_002.pdf" not in results

def test_empty_predictions():
    loader = DatasetLoader()
    cases = loader.load_directory(DATASET_DIR)

    results = EvaluationRunner().evaluate_dataset(
        cases,
        {},
    )

    assert results == {}