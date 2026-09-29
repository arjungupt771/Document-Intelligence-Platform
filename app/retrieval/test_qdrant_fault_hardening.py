from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from qdrant_client.http.exceptions import UnexpectedResponse

from app.indexing.config import QdrantSettings
from app.indexing.indexer import DocumentIndexer
from app.retrieval.errors import QdrantConnectionError, QdrantWriteError
from app.retrieval.qdrant_retriever import QdrantRetriever


@pytest.fixture()
def settings():
    return QdrantSettings(
        url="http://localhost:6333", api_key=None, collection_name="test_chunks",
        vector_size=4, distance="Cosine", timeout=30,
    )


def _fake_embedding_model():
    model = MagicMock()
    model.embed_one.return_value = [0.1, 0.2, 0.3, 0.4]
    model.embed.return_value = [[0.1, 0.2, 0.3, 0.4]]
    return model


@pytest.mark.parametrize(
    "exc",
    [
        httpx.ConnectError("refused"),
        httpx.ConnectTimeout("timed out"),
        httpx.ReadTimeout("timed out"),
        TimeoutError("timed out"),
    ],
)
def test_retrieve_wraps_connectivity_exceptions(settings, exc):
    client = MagicMock()
    client.query_points.side_effect = exc
    retriever = QdrantRetriever(client, _fake_embedding_model(), settings)

    with pytest.raises(QdrantConnectionError):
        retriever.retrieve("what is the total due")


def test_retrieve_wraps_5xx_as_connection_error(settings):
    client = MagicMock()
    client.query_points.side_effect = UnexpectedResponse(
        status_code=503, reason_phrase="Service Unavailable", content=b"", headers={}
    )
    retriever = QdrantRetriever(client, _fake_embedding_model(), settings)

    with pytest.raises(QdrantConnectionError):
        retriever.retrieve("what is the total due")


def test_retrieve_does_not_mask_4xx_client_errors(settings):
    client = MagicMock()
    client.query_points.side_effect = UnexpectedResponse(
        status_code=400, reason_phrase="Bad Request", content=b"", headers={}
    )
    retriever = QdrantRetriever(client, _fake_embedding_model(), settings)

    with pytest.raises(UnexpectedResponse):
        retriever.retrieve("what is the total due")


def test_indexer_wraps_upsert_connectivity_failure(settings, monkeypatch):
    client = MagicMock()
    client.upsert.side_effect = httpx.ConnectError("refused")
    indexer = DocumentIndexer(client, _fake_embedding_model(), settings)
    document = SimpleNamespace(document_id="doc-1", source_filename="a.pdf")

    from app.indexing.chunking import Chunk
    import app.indexing.indexer as indexer_module

    monkeypatch.setattr(
        indexer_module,
        "chunk_document",
        lambda doc, cfg: [Chunk(text="hello", chunk_index=0, page_number=1)],
    )

    with pytest.raises(QdrantWriteError):
        indexer.index_document(document, document_type="invoice")


def test_indexer_wraps_delete_connectivity_failure(settings):
    client = MagicMock()
    client.delete.side_effect = httpx.ReadTimeout("timed out")
    indexer = DocumentIndexer(client, _fake_embedding_model(), settings)

    with pytest.raises(QdrantWriteError):
        indexer.delete_document("doc-1")