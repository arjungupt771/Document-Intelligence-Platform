import uuid
from unittest.mock import MagicMock

from app.routing.structured import StructuredQueryService


def test_get_document_delegates_to_document_repository():
    documents = MagicMock()
    extractions = MagicMock()

    document_id = uuid.uuid4()
    expected = MagicMock()

    documents.get.return_value = expected

    service = StructuredQueryService(documents, extractions)

    result = service.get_document(document_id)

    assert result is expected
    documents.get.assert_called_once_with(document_id)


def test_get_latest_extraction_delegates_to_extraction_repository():
    documents = MagicMock()
    extractions = MagicMock()

    document_id = uuid.uuid4()
    expected = MagicMock()

    extractions.get_latest_for_document.return_value = expected

    service = StructuredQueryService(documents, extractions)

    result = service.get_latest_extraction(document_id)

    assert result is expected
    extractions.get_latest_for_document.assert_called_once_with(document_id)