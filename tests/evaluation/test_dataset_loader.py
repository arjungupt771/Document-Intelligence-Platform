from pathlib import Path

from evaluation.dataset_loader import DatasetLoader


DATASET_DIR = Path("evaluation/datasets/invoices")


def test_load_single_dataset_file():
    loader = DatasetLoader()

    case = loader.load_file(
        DATASET_DIR / "invoice_001.json"
    )

    assert case.document == "invoice_001.pdf"
    assert case.document_type == "invoice"

    assert (
        case.ground_truth.fields["vendor"]
        == "ACME Corporation"
    )

    assert (
        case.ground_truth.fields["invoice_number"]
        == "INV-1042"
    )

    assert case.ground_truth.fields["total"] == 354000


def test_load_dataset_directory():
    loader = DatasetLoader()

    cases = loader.load_directory(DATASET_DIR)

    assert len(cases) == 2

    assert cases[0].document == "invoice_001.pdf"
    assert cases[1].document == "invoice_002.pdf"