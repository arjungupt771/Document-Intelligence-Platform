from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from app.retrieval.errors import QdrantConnectionError
from app.indexing.config import QdrantSettings
from app.retrieval.qdrant_retriever import QdrantRetriever


@pytest.fixture()
def settings():
    return QdrantSettings(
        url="http://localhost:6333",
        api_key=None,
        collection_name="test_chunks",
        vector_size=4,
        distance="Cosine",
        timeout=30,
    )


def _fake_point(score, **payload):
    return SimpleNamespace(id="p1", score=score, payload=payload)


def _fake_embedding_model():
    model = MagicMock()
    model.embed_one.return_value = [0.1, 0.2, 0.3, 0.4]
    return model


def test_retrieve_returns_ranked_chunks(settings):
    client = MagicMock()
    client.query_points.return_value = SimpleNamespace(
        points=[
            _fake_point(0.9, document_id="doc-1", document_type="invoice", chunk_index=0, page_number=1, text="a"),
            _fake_point(0.7, document_id="doc-2", document_type="invoice", chunk_index=1, page_number=2, text="b"),
        ]
    )
    retriever = QdrantRetriever(client, _fake_embedding_model(), settings)

    result = retriever.retrieve("what is the total due", top_k=5)

    assert len(result.chunks) == 2
    assert result.chunks[0].score >= result.chunks[1].score
    assert result.chunks[0].document_id == "doc-1"


def test_retrieve_applies_metadata_filter(settings):
    client = MagicMock()
    client.query_points.return_value = SimpleNamespace(points=[])

    retriever = QdrantRetriever(client, _fake_embedding_model(), settings)
    retriever.retrieve("query", document_type="contract", document_id="doc-9")

    _, kwargs = client.query_points.call_args
    query_filter = kwargs["query_filter"]
    assert query_filter is not None
    assert len(query_filter.must) == 2

def test_retrieve_scopes_results_to_requested_document(settings):
    client = MagicMock()
    client.query_points.return_value = SimpleNamespace(points=[])

    retriever = QdrantRetriever(
        client,
        _fake_embedding_model(),
        settings,
    )

    retriever.retrieve(
        "total due",
        document_id="doc-authorized",
    )

    _, kwargs = client.query_points.call_args
    query_filter = kwargs["query_filter"]

    assert query_filter is not None
    assert len(query_filter.must) == 1

    condition = query_filter.must[0]

    assert condition.key == "document_id"
    assert condition.match.value == "doc-authorized"

def test_retrieve_passes_score_threshold(settings):
    client = MagicMock()
    client.query_points.return_value = SimpleNamespace(points=[])

    retriever = QdrantRetriever(client, _fake_embedding_model(), settings)
    retriever.retrieve("query", score_threshold=0.5)

    _, kwargs = client.query_points.call_args
    assert kwargs["score_threshold"] == 0.5


def test_empty_query_returns_empty_result_without_calling_qdrant(settings):
    client = MagicMock()
    retriever = QdrantRetriever(client, _fake_embedding_model(), settings)

    result = retriever.retrieve("   ")

    assert result.is_empty
    client.query_points.assert_not_called()


def test_no_results_returns_empty_result(settings):
    client = MagicMock()
    client.query_points.return_value = SimpleNamespace(points=[])
    retriever = QdrantRetriever(client, _fake_embedding_model(), settings)

    result = retriever.retrieve("nonexistent topic")

    assert result.is_empty
    assert result.total_candidates == 0


def test_assembled_context_includes_source_metadata(settings):
    client = MagicMock()
    client.query_points.return_value = SimpleNamespace(
        points=[
            _fake_point(
                0.9,
                document_id="doc-1",
                document_type="invoice",
                chunk_index=0,
                page_number=3,
                text="Total due: $500",
            )
        ]
    )
    retriever = QdrantRetriever(client, _fake_embedding_model(), settings)

    result = retriever.retrieve("total due")
    context = result.assembled_context()

    assert "doc-1" in context
    assert "page=3" in context
    assert "Total due: $500" in context

def test_retrieve_uses_configured_collection():
    client = MagicMock()
    client.query_points.return_value = SimpleNamespace(points=[])

    settings = QdrantSettings(
        url="http://localhost:6333",
        api_key=None,
        collection_name="tenant_specific_chunks",
        vector_size=4,
        distance="Cosine",
        timeout=30,
    )
    retriever = QdrantRetriever(client, _fake_embedding_model(), settings)

    retriever.retrieve("what is the total due")

    _, kwargs = client.query_points.call_args

    assert kwargs["collection_name"] == "tenant_specific_chunks"


def test_retrieve_wraps_qdrant_connection_failure(settings):
    client = MagicMock()
    client.query_points.side_effect = ConnectionError("qdrant is unavailable")

    retriever = QdrantRetriever(
        client=client,
        embedding_model=_fake_embedding_model(),
        settings=settings,
    )

    with pytest.raises(QdrantConnectionError) as exc_info:
        retriever.retrieve("What is the invoice total?")

    assert str(exc_info.value) == "Vector search service is unavailable"
    assert isinstance(exc_info.value.__cause__, ConnectionError)