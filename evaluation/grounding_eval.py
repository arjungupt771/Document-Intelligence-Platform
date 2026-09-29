from dataclasses import dataclass

from evaluation.llm_judge import LLMJudge


@dataclass(frozen=True)
class QACase:
    question: str
    evidence: str
    answer: str
    deterministic_grounded: bool  # output of your production verifier


@dataclass(frozen=True)
class GroundingEvalResult:
    total: int
    grounding_rate: float          # fraction judged grounded
    hallucination_rate: float      # fraction with any unsupported claim
    verifier_agreement_rate: float # how often deterministic verifier agrees with LLM judge
    disagreements: list[str]       # questions where they disagreed, for manual review


def evaluate_grounding(cases: list[QACase], judge: LLMJudge) -> GroundingEvalResult:
    if not cases:
        return GroundingEvalResult(0, 0.0, 0.0, 0.0, [])

    grounded_count = 0
    hallucinated_count = 0
    agreements = 0
    disagreements = []

    for case in cases:
        verdict = judge.judge(case.question, case.evidence, case.answer)

        if verdict.grounded:
            grounded_count += 1
        if verdict.hallucinated_claims:
            hallucinated_count += 1

        if verdict.grounded == case.deterministic_grounded:
            agreements += 1
        else:
            disagreements.append(case.question)

    total = len(cases)
    return GroundingEvalResult(
        total=total,
        grounding_rate=grounded_count / total,
        hallucination_rate=hallucinated_count / total,
        verifier_agreement_rate=agreements / total,
        disagreements=disagreements,
    )