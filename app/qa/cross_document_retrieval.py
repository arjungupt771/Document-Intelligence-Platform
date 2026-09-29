from app.qa.cross_document import CrossDocumentContext
from app.qa.models import AnswerSource


class CrossDocumentRetrievalAdapter:
    def from_retrieval_result(self, result) -> CrossDocumentContext:
        sources = [
            AnswerSource(
                document_id=chunk.document_id,
                document_type=chunk.document_type,
                text=chunk.text,
                page_number=chunk.page_number,
                score=chunk.score,
            )
            for chunk in result.chunks
        ]

        return CrossDocumentContext(
            query=result.query,
            sources=sources,
        )