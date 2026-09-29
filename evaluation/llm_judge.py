"""LLM-as-judge scoring for QA answers, reusing the same LLMClient interface
the production QA pipeline uses (app/qa/llm.py) so the judge model is
swappable the same way the answer model is."""
import json
from dataclasses import dataclass

from app.qa.llm import LLMClient

JUDGE_PROMPT_TEMPLATE = """You are grading an AI-generated answer for factual grounding.

Question: {question}

Evidence (the only source of truth):
{evidence}

Answer to grade:
{answer}

Score the answer on:
- "grounded": true if every factual claim in the answer is supported by the evidence, false otherwise
- "hallucinated_claims": list of specific claims in the answer NOT supported by the evidence (empty list if none)
- "relevance": a float from 0.0 to 1.0 for how directly the answer addresses the question

Respond with ONLY valid JSON, no other text:
{{"grounded": true/false, "hallucinated_claims": ["..."], "relevance": 0.0}}
"""


@dataclass(frozen=True)
class JudgeVerdict:
    grounded: bool
    hallucinated_claims: list[str]
    relevance: float
    raw_response: str


class LLMJudgeError(RuntimeError):
    """Raised when the judge model's response can't be parsed."""


class LLMJudge:
    def __init__(self, llm_client: LLMClient):
        self._llm_client = llm_client

    def judge(self, question: str, evidence: str, answer: str) -> JudgeVerdict:
        prompt = JUDGE_PROMPT_TEMPLATE.format(
            question=question, evidence=evidence or "(no evidence provided)", answer=answer
        )
        raw = self._llm_client.generate(prompt)

        try:
            payload = json.loads(self._extract_json(raw))
        except (json.JSONDecodeError, ValueError) as exc:
            raise LLMJudgeError(f"Judge response was not valid JSON: {raw!r}") from exc

        return JudgeVerdict(
            grounded=bool(payload.get("grounded", False)),
            hallucinated_claims=list(payload.get("hallucinated_claims", [])),
            relevance=float(payload.get("relevance", 0.0)),
            raw_response=raw,
        )

    @staticmethod
    def _extract_json(text: str) -> str:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("no JSON object found in judge response")
        return text[start : end + 1]