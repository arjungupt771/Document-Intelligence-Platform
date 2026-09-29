import json
from pathlib import Path

from evaluation.models import EvaluationCase, GroundTruth


class DatasetLoader:
    def load_file(self, path: str | Path) -> EvaluationCase:
        file_path = Path(path)

        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return EvaluationCase(
            document=data["document"],
            document_type=data["document_type"],
            ground_truth=GroundTruth(
                fields=data["ground_truth"]
            ),
        )

    def load_directory(
        self,
        directory: str | Path,
    ) -> list[EvaluationCase]:
        directory_path = Path(directory)

        cases = []

        for file_path in sorted(directory_path.glob("*.json")):
            cases.append(self.load_file(file_path))

        return cases