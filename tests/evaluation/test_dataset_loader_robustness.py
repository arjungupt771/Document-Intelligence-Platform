import json

import pytest

from evaluation.dataset_loader import DatasetLoader


def test_missing_ground_truth_fields(tmp_path):
    path = tmp_path / "invalid.json"

    path.write_text(
        json.dumps(
            {
                "document": "invoice.pdf",
                "document_type": "invoice",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(KeyError):
        DatasetLoader().load_file(path)


def test_missing_document(tmp_path):
    path = tmp_path / "invalid.json"

    path.write_text(
        json.dumps(
            {
                "document_type": "invoice",
                "ground_truth": {
                    "total": 1000,
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(KeyError):
        DatasetLoader().load_file(path)


def test_invalid_json(tmp_path):
    path = tmp_path / "invalid.json"

    path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    with pytest.raises(json.JSONDecodeError):
        DatasetLoader().load_file(path)