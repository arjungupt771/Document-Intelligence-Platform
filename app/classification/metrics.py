from dataclasses import dataclass

from app.documents.models import DocumentType


@dataclass(frozen=True)
class ClassMetrics:
    precision: float
    recall: float
    f1: float
    support: int
    """Number of ground-truth examples of this class."""


@dataclass(frozen=True)
class EvaluationReport:
    accuracy: float
    per_class: dict[DocumentType, ClassMetrics]
    confusion_matrix: dict[DocumentType, dict[DocumentType, int]]
    """confusion_matrix[actual][predicted] = count."""

    unknown_rate: float
    """Fraction of predictions that came back UNKNOWN."""


def evaluate(
    y_true: list[DocumentType],
    y_pred: list[DocumentType],
) -> EvaluationReport:
    """
    Compute accuracy, per-class precision/recall/F1, a confusion matrix,
    and the UNKNOWN rate for a set of predictions. Used to benchmark and
    compare classifier approaches (rule-based vs. ML vs. embedding vs.
    LLM) on the same labeled set before picking one.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must be the same length")
    if not y_true:
        raise ValueError("Cannot evaluate an empty set of predictions")

    labels = sorted(set(y_true) | set(y_pred), key=lambda label: label.value)

    confusion_matrix: dict[DocumentType, dict[DocumentType, int]] = {
        actual: {predicted: 0 for predicted in labels} for actual in labels
    }
    for actual, predicted in zip(y_true, y_pred):
        confusion_matrix[actual][predicted] += 1

    correct = sum(1 for actual, predicted in zip(y_true, y_pred) if actual == predicted)
    accuracy = correct / len(y_true)

    per_class: dict[DocumentType, ClassMetrics] = {}
    for label in labels:
        true_positives = confusion_matrix[label][label]
        false_positives = sum(
            confusion_matrix[other][label] for other in labels if other != label
        )
        false_negatives = sum(
            confusion_matrix[label][other] for other in labels if other != label
        )
        support = sum(confusion_matrix[label].values())

        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives)
            else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives)
            else 0.0
        )
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )

        per_class[label] = ClassMetrics(
            precision=precision, recall=recall, f1=f1, support=support
        )

    unknown_rate = sum(1 for predicted in y_pred if predicted == DocumentType.UNKNOWN) / len(
        y_pred
    )

    return EvaluationReport(
        accuracy=accuracy,
        per_class=per_class,
        confusion_matrix=confusion_matrix,
        unknown_rate=unknown_rate,
    )