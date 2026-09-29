from __future__ import annotations

from sqlalchemy.orm import Session




from app.qa.factory import build_qa_service


class FakeQdrantClient:
    pass


class FakeEmbeddingModel:
    pass


def test_build_qa_service(monkeypatch):
    from app.qa import factory

    monkeypatch.setattr(
        factory,
        "get_qdrant_client",
        lambda settings: FakeQdrantClient(),
    )

    monkeypatch.setattr(
        factory,
        "get_embedding_model",
        lambda: FakeEmbeddingModel(),
    )

    monkeypatch.setenv("LLM_API_KEY", "test-api-key")

    service = build_qa_service(session=object())

    assert service is not None
    assert service._router is not None
    assert service._retriever is not None
    assert service._answer_generator is not None
    assert service._structured_service is not None