"""Regression tracking: freeze current metrics as a baseline, then diff
future runs against it so a silent quality drop fails CI instead of
shipping. Mirrors the pattern already used in app/drift/baseline_builder.py."""
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from evaluation.models import EvaluationMetrics

DEFAULT_BASELINE_PATH = Path("evaluation/datasets/regression_baseline.json")


@dataclass(frozen=True)
class RegressionResult:
    regressed_metrics: list[str]
    improved_metrics: list[str]
    baseline: dict
    current: dict


# Metrics where LOWER is better; everything else assumes higher is better.
_LOWER_IS_BETTER = {"missing_field_rate", "hallucinated_field_rate", "mismatched_fields", "missing_fields", "extra_fields"}
_TOLERANCE = 0.02  # allow small run-to-run noise before flagging


def save_baseline(metrics: EvaluationMetrics, path: Path = DEFAULT_BASELINE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(metrics) if not hasattr(metrics, "model_dump") else metrics.model_dump()))


def compare_to_baseline(
    metrics: EvaluationMetrics, path: Path = DEFAULT_BASELINE_PATH
) -> RegressionResult:
    if not path.exists():
        raise FileNotFoundError(f"No regression baseline at {path}. Run save_baseline() first.")

    baseline = json.loads(path.read_text())
    current = metrics.model_dump() if hasattr(metrics, "model_dump") else asdict(metrics)

    regressed, improved = [], []

    for key, current_value in current.items():
        if key not in baseline or not isinstance(current_value, (int, float)):
            continue

        baseline_value = baseline[key]
        delta = current_value - baseline_value
        lower_is_better = key in _LOWER_IS_BETTER
        got_worse = delta > _TOLERANCE if lower_is_better else delta < -_TOLERANCE

        if got_worse:
            regressed.append(key)
        elif abs(delta) > _TOLERANCE:
            improved.append(key)

    return RegressionResult(regressed, improved, baseline, current)