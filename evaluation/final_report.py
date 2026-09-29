"""Aggregates extraction metrics, retrieval eval, grounding eval, and
regression status into one report — the artifact 17.18 asks for."""
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from evaluation.grounding_eval import GroundingEvalResult
from evaluation.models import EvaluationMetrics
from evaluation.regression import RegressionResult
from evaluation.thresholds import ThresholdViolation


@dataclass(frozen=True)
class FinalEvaluationReport:
    generated_at: str
    extraction_metrics: dict
    threshold_violations: list[str]
    grounding: dict
    regression: dict
    passed: bool


def build_final_report(
    extraction_metrics: EvaluationMetrics,
    violations: list[ThresholdViolation],
    grounding: GroundingEvalResult,
    regression: RegressionResult,
) -> FinalEvaluationReport:
    return FinalEvaluationReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        extraction_metrics=extraction_metrics.model_dump(),
        threshold_violations=[v.metric for v in violations],
        grounding={
            "grounding_rate": grounding.grounding_rate,
            "hallucination_rate": grounding.hallucination_rate,
            "verifier_agreement_rate": grounding.verifier_agreement_rate,
        },
        regression={"regressed": regression.regressed_metrics, "improved": regression.improved_metrics},
        passed=not violations and not regression.regressed_metrics,
    )


def write_report(report: FinalEvaluationReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.__dict__, indent=2))