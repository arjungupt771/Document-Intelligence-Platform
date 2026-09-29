import pytest

from app.qa.verifier import EvidenceVerifier
from app.qa.verification import VerificationResult


class TestVerifier(EvidenceVerifier):
    def verify(self, answer, context):
        return VerificationResult(
            verified=True,
            reason="Test verification passed.",
        )


def test_evidence_verifier_is_abstract():
    with pytest.raises(TypeError):
        EvidenceVerifier()


def test_evidence_verifier_can_be_implemented():
    verifier = TestVerifier()

    result = verifier.verify(
        answer="The invoice total is 12000.",
        context=None,
    )

    assert result.verified is True
    assert result.reason == "Test verification passed."