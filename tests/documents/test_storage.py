from io import BytesIO
from uuid import uuid4

from app.documents.storage import DocumentStorage, FileSizeLimitExceeded


def test_document_is_stored(tmp_path):
    storage = DocumentStorage(tmp_path)

    document_id = uuid4()
    content = b"test document content"

    stream = BytesIO(content)

    size = storage.write_stream(
        document_id=document_id,
        stream=stream,
        max_size=1024,
    )

    path = storage.finalize(document_id)

    assert size == len(content)
    assert path.exists()
    assert path.read_bytes() == content


def test_oversized_document_is_deleted(tmp_path):
    storage = DocumentStorage(tmp_path)

    document_id = uuid4()
    content = b"x" * 2048

    stream = BytesIO(content)

    try:
        storage.write_stream(
            document_id=document_id,
            stream=stream,
            max_size=1024,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected oversized upload to fail")

    document_dir = tmp_path / str(document_id)

    assert not document_dir.exists()

def test_oversized_document_raises_size_limit_error(tmp_path):
    storage = DocumentStorage(tmp_path)
    document_id = uuid4()
    content = b"x" * 2048

    try:
        storage.write_stream(
            document_id=document_id,
            stream=BytesIO(content),
            max_size=1024,
        )
    except FileSizeLimitExceeded as exc:
        assert str(exc) == "File size exceeds maximum allowed size"
    else:
        raise AssertionError("Expected FileSizeLimitExceeded")

def test_document_path_stays_inside_storage_root(tmp_path):
    storage = DocumentStorage(tmp_path)

    document_id = uuid4()
    path = storage.create_temp_path(document_id)

    assert path.parent.parent == tmp_path.resolve()
    assert path.parent.is_relative_to(tmp_path.resolve())


def test_document_storage_rejects_path_escape(tmp_path):
    storage = DocumentStorage(tmp_path)

    class FakeDocumentId:
        def __str__(self):
            return "../../outside"

    try:
        storage.create_temp_path(FakeDocumentId())
    except ValueError as exc:
        assert str(exc) == "document storage path escapes storage root."
    else:
        raise AssertionError("Expected storage path escape to be rejected")