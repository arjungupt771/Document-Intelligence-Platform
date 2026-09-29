from unittest.mock import MagicMock

import pytest

from app.indexing.config import ChunkingSettings, QdrantSettings
from app.indexing.indexer import DocumentIndexer, _point_id
from app.parsing.models import BlockType, DocumentMetadata, Page, ParsedDocument, Provenance, TextBlock


def _page(page_number: int, text: str) -> Page:
    provenance = Provenance(source_parser="test", page_number=page_number, block_index=0)
    return Page(
        page_number=page_number,
        width=None,
        height=None,
        text_blocks=[TextBlock(text=text, block_type=BlockType.TEXT, provenance=provenance)],
    )


def _document(pages_text: list[str], document_id: str = "doc-abc") -> ParsedDocument:
    return ParsedDocument(
        document_id=document_id,
        source_filename="invoice.pdf",
        parser_name="test",
        metadata=DocumentMetadata(),
        pages=[_page(i + 1, text) for i, text in enumerate(pages_text)],
    )


@pytest.fixture()
def settings():
    return QdrantSettings(
        url="http://localhost:6333",
        api_key=None,
        collection_name="test_chunks",
        vector_size=4,
        distance="Cosine",
    )


@pytest.fixture()
def fake_embedding_model():
    model = MagicMock()
    model.embed.side_effect = lambda texts: [[0.1, 0.2, 0.3, 0.4] for _ in texts]
    return model


def test_index_document_upserts_one_point_per_chunk(settings, fake_embedding_model):
    client = MagicMock()
    indexer = DocumentIndexer(client, fake_embedding_model, settings, ChunkingSettings())

    count = indexer.index_document(_document(["hello world"]), document_type="invoice")

    assert count == 1
    client.upsert.assert_called_once()
    _, kwargs = client.upsert.call_args
    assert kwargs["collection_name"] == "test_chunks"
    assert len(kwargs["points"]) == 1
    assert kwargs["points"][0].payload["document_id"] == "doc-abc"
    assert kwargs["points"][0].payload["document_type"] == "invoice"


def test_point_id_is_deterministic():
    assert _point_id("doc-abc", 0) == _point_id("doc-abc", 0)
    assert _point_id("doc-abc", 0) != _point_id("doc-abc", 1)
    assert _point_id("doc-abc", 0) != _point_id("doc-xyz", 0)


def test_index_document_with_no_text_does_not_call_upsert(settings, fake_embedding_model):
    client = MagicMock()
    indexer = DocumentIndexer(client, fake_embedding_model, settings)

    count = indexer.index_document(_document([""]), document_type="invoice")

    assert count == 0
    client.upsert.assert_not_called()


def test_delete_document_filters_by_document_id(settings, fake_embedding_model):
    client = MagicMock()
    indexer = DocumentIndexer(client, fake_embedding_model, settings)

    indexer.delete_document("doc-abc")

    client.delete.assert_called_once()
    _, kwargs = client.delete.call_args
    assert kwargs["collection_name"] == "test_chunks"


def test_reindex_deletes_then_indexes(settings, fake_embedding_model):
    client = MagicMock()
    indexer = DocumentIndexer(client, fake_embedding_model, settings)

    indexer.reindex_document(_document(["hello world"]), document_type="invoice")

    assert client.delete.called
    assert client.upsert.called


def test_repeated_index_call_reuses_same_point_ids(settings, fake_embedding_model):
    """Idempotent upsert: indexing the same document twice must not grow the collection."""
    client = MagicMock()
    indexer = DocumentIndexer(client, fake_embedding_model, settings)

    indexer.index_document(_document(["hello world"]), document_type="invoice")
    indexer.index_document(_document(["hello world"]), document_type="invoice")

    first_ids = [p.id for p in client.upsert.call_args_list[0].kwargs["points"]]
    second_ids = [p.id for p in client.upsert.call_args_list[1].kwargs["points"]]
    assert first_ids == second_ids

def test_index_document_does_not_store_arbitrary_extra_metadata(
    settings,
    fake_embedding_model,
):
    client = MagicMock()
    indexer = DocumentIndexer(client, fake_embedding_model, settings)

    indexer.index_document(
        _document(["hello world"]),
        document_type="invoice",
        extra_metadata={
            "email": "user@example.com",
            "internal_path": "/srv/private/document.pdf",
            "secret": "should-not-be-stored",
        },
    )

    _, kwargs = client.upsert.call_args
    payload = kwargs["points"][0].payload

    assert "email" not in payload
    assert "internal_path" not in payload
    assert "secret" not in payload

    assert payload["document_id"] == "doc-abc"
    assert payload["document_type"] == "invoice"
    assert payload["source_filename"] == "invoice.pdf"
    assert payload["text"] == "hello world"


def test_index_document_uses_configured_collection(
    fake_embedding_model,
):
    client = MagicMock()
    settings = QdrantSettings(
        url="http://localhost:6333",
        api_key=None,
        collection_name="tenant_specific_chunks",
        vector_size=4,
        distance="Cosine",
    )
    indexer = DocumentIndexer(client, fake_embedding_model, settings)

    indexer.index_document(
        _document(["hello world"]),
        document_type="invoice",
    )

    _, kwargs = client.upsert.call_args

    assert kwargs["collection_name"] == "tenant_specific_chunks"

def test_delete_document_uses_configured_collection(
    fake_embedding_model,
):
    client = MagicMock()
    settings = QdrantSettings(
        url="http://localhost:6333",
        api_key=None,
        collection_name="tenant_specific_chunks",
        vector_size=4,
        distance="Cosine",
    )
    indexer = DocumentIndexer(client, fake_embedding_model, settings)

    indexer.delete_document("doc-abc")

    _, kwargs = client.delete.call_args

    assert kwargs["collection_name"] == "tenant_specific_chunks"