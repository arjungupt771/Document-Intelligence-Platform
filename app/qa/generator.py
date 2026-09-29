from abc import ABC, abstractmethod

from app.qa.context import GroundingContextLike
from app.qa.models import AnswerResponse


class AnswerGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        context: GroundingContextLike,
    ) -> AnswerResponse:
        raise NotImplementedError