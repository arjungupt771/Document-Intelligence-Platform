from abc import ABC, abstractmethod

from app.qa.context import GroundingContextLike
from app.qa.verification import VerificationResult


class EvidenceVerifier(ABC):
    @abstractmethod
    def verify(
        self,
        answer: str,
        context: GroundingContextLike,
    ) -> VerificationResult:
        raise NotImplementedError