from dataclasses import dataclass, field


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    unsupported_claims: list[str] = field(default_factory=list)
    reason: str | None = None