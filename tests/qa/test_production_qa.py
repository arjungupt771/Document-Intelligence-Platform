from app.qa.factory import build_qa_service
from app.qa.models import AnswerRequest
from app.retrieval.models import RetrievedChunk, RetrievalResult


class FakeRetriever:
    def retrieve(
        self,
        query,
        top_k=5,
        document_type=None,
        document_id=None,
        score_threshold=None,
    ):
        return RetrievalResult(
            query=query,
            chunks=[
                RetrievedChunk(
                    document_id="doc-1",
                    document_type="invoice",
                    chunk_index=0,
                    page_number=1,
                    text="The invoice total is ₹12,000.",
                    score=0.95,
                )
            ],
            total_candidates=1,
        )


class FakeLLMClient:
    def generate(self, prompt):
        assert "What are the payment terms?" in prompt
        assert "The invoice total is ₹12,000." in prompt

        return "The invoice total is ₹12,000."


def test_production_qa_factory_builds_working_service(monkeypatch):
    from app.qa import factory

    monkeypatch.setattr(
        factory,
        "get_qdrant_client",
        lambda settings: object(),
    )

    monkeypatch.setattr(
        factory,
        "get_embedding_model",
        lambda: object(),
    )

    monkeypatch.setattr(
        factory,
        "QdrantRetriever",
        lambda client, embedding_model, settings: FakeRetriever(),
    )

    monkeypatch.setattr(
        factory,
        "GroqLLMClient",
        lambda settings: FakeLLMClient(),
        )

    monkeypatch.setenv("LLM_API_KEY", "test-api-key")

    service = build_qa_service(session=object())

    response = service.answer(
        AnswerRequest(
            query="What are the payment terms?"
        )
    )

    assert response.answer == "The invoice total is ₹12,000."
    assert response.grounded is True
    assert len(response.sources) == 1
    assert response.sources[0].document_id == "doc-1"
    assert response.sources[0].text == "The invoice total is ₹12,000."