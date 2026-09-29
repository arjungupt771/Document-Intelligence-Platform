from app.qa.verification import VerificationResult


def test_verified_result():
    result = VerificationResult(
        verified=True,
        reason="All answer claims are supported by the provided evidence.",
    )

    assert result.verified is True
    assert result.unsupported_claims == []
    assert result.reason == (
        "All answer claims are supported by the provided evidence."
    )


def test_unverified_result_with_unsupported_claims():
    result = VerificationResult(
        verified=False,
        unsupported_claims=[
            "The invoice was issued on 15 March 2026."
        ],
        reason="The answer contains claims not present in the retrieved evidence.",
    )

    assert result.verified is False
    assert result.unsupported_claims == [
        "The invoice was issued on 15 March 2026."
    ]
    assert result.reason == (
        "The answer contains claims not present in the retrieved evidence."
    )


def test_verification_result_defaults():
    result = VerificationResult(
        verified=True,
    )

    assert result.verified is True
    assert result.unsupported_claims == []
    assert result.reason is None