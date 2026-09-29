from app.analyst.generator import GroundedInsightGenerator
from app.analyst.models import Insight, InsightEvidence, InsightType, Severity
from app.qa.verification import VerificationResult


class FakeLLM:
    def __init__(self, response: str):
        self._response = response

    def generate(self, prompt: str) -> str:
        return self._response


class FakeVerifier:
    def __init__(self, verified: bool, reason: str = "ok"):
        self._verified = verified
        self._reason = reason

    def verify(self, answer, context):
        return VerificationResult(verified=self._verified, reason=self._reason)


def _insight(evidence=None):
    return Insight(
        type=InsightType.FINANCIAL,
        severity=Severity.HIGH,
        title="Mismatch",
        description="Totals don't line up",
        confidence=0.9,
        evidence=evidence
        if evidence is not None
        else [InsightEvidence(document_id="doc-1", document_type="invoice", text="total=200, subtotal=100")],
    )


class TestGroundedInsightGenerator:
    def test_attaches_verified_narrative(self):
        generator = GroundedInsightGenerator(
            llm_client=FakeLLM("The invoice total doesn't match its subtotal."),
            evidence_verifier=FakeVerifier(verified=True),
        )

        result = generator.generate(_insight())

        assert result.narrative == "The invoice total doesn't match its subtotal."
        assert result.narrative_verified is True

    def test_drops_unverified_narrative(self):
        generator = GroundedInsightGenerator(
            llm_client=FakeLLM("Some ungrounded claim."),
            evidence_verifier=FakeVerifier(verified=False, reason="not supported"),
        )

        result = generator.generate(_insight())

        assert result.narrative is None
        assert result.narrative_verified is False
        assert result.metadata["narrative_rejected_reason"] == "not supported"

    def test_skips_generation_when_no_evidence(self):
        generator = GroundedInsightGenerator(
            llm_client=FakeLLM("anything"),
            evidence_verifier=FakeVerifier(verified=True),
        )

        result = generator.generate(_insight(evidence=[]))

        assert result.narrative is None