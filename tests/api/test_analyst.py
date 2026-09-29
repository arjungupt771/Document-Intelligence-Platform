import uuid

from fastapi.testclient import TestClient
from app.documents.models import DocumentType, DocumentStatus
from app.storage.models import DocumentORM
from app.main import app
from app.storage.database import get_db
from fastapi import HTTPException
client = TestClient(
    app,
    headers={"Authorization": "Bearer test-secret"},
)


def test_analyze_document_endpoint(monkeypatch):
    from app.api import analyst

    document_id = uuid.uuid4()

    class FakeType:
        value = "financial"

    class FakeSeverity:
        value = "high"

    class FakeInsight:
        id = uuid.uuid4()
        type = FakeType()
        severity = FakeSeverity()
        title = "Line items do not sum to subtotal"
        description = "..."
        narrative = None
        confidence = 0.9
        priority_score = 2.7
        document_ids = [str(document_id)]
        evidence = []

    class FakeReport:
        pass

    fake_report = FakeReport()
    fake_report.document_id = str(document_id)
    fake_report.insights = [FakeInsight()]

    class FakeService:
        def analyze_document(self, doc_id):
            assert doc_id == document_id
            return fake_report

    monkeypatch.setattr(analyst, "build_analyst_service", lambda db: FakeService())

    # class FakeSession:
    #     def get(self, model, requested_document_id):
    #         orm_document = type(
    #             "FakeORMDocument",
    #             (),
    #             {
    #                 "id": requested_document_id,
    #                 "filename": "invoice.pdf",
    #                 "content_type": "application/pdf",
    #                 "size_bytes": 1024,
    #                 "document_type": DocumentType.INVOICE,
    #                 "status": DocumentStatus.UPLOADED,
    #                 "storage_path": "storage/documents/test/original",
    #                 "created_at": None,
    #                 "updated_at": None,
    #                 },
    #         )()
    #         return orm_document


    def fake_db():
        class FakeDB:
            def get(self, model, document_id):
                return type(
                "FakeDocumentORM",
                (),
                {
                    "id": document_id,
                    "filename": "test.pdf",
                    "content_type": "application/pdf",
                    "size_bytes": 1024,
                    "document_type": DocumentType.INVOICE,
                    "status": DocumentStatus.UPLOADED,
                    "storage_path": "storage/documents/test/original",
                    "created_at": None,
                    "updated_at": None,
                },
            )()
            def commit(self):
                pass   
        yield FakeDB()

    app.dependency_overrides[get_db] = fake_db

    try:
        response = client.post(f"/analyst/documents/{document_id}/analyze")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data[0]["title"] == "Line items do not sum to subtotal"
    assert data[0]["severity"] == "high"

def test_compare_documents_rejects_missing_first_document(monkeypatch):
    from app.api import analyst

    document_id_a = uuid.uuid4()
    document_id_b = uuid.uuid4()

    class FakeDB:
        def get(self, model, document_id):
            return None

        def commit(self):
            raise AssertionError("Database commit must not occur")

    def fake_db():
        yield FakeDB()

    class FakeService:
        def compare_documents(self, document_a, document_b):
            raise AssertionError("Comparison service must not be called")

    monkeypatch.setattr(
        analyst,
        "build_analyst_service",
        lambda db: FakeService(),
    )

    app.dependency_overrides[get_db] = fake_db

    try:
        response = client.post(
            "/analyst/compare",
            json={
                "document_id_a": str(document_id_a),
                "document_id_b": str(document_id_b),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"

def test_compare_documents_rejects_missing_second_document(monkeypatch):
    from app.api import analyst

    document_id_a = uuid.uuid4()
    document_id_b = uuid.uuid4()

    class FakeDB:
        def get(self, model, document_id):
            if document_id == document_id_a:
                return type(
                    "FakeDocumentORM",
                    (),
                    {
                        "id": document_id_a,
                        "filename": "invoice-a.pdf",
                        "content_type": "application/pdf",
                        "size_bytes": 1024,
                        "document_type": DocumentType.INVOICE,
                        "status": DocumentStatus.UPLOADED,
                        "storage_path": "storage/documents/test/a/original",
                        "created_at": None,
                        "updated_at": None,
                    },
                )()

            return None

        def commit(self):
            raise AssertionError("Database commit must not occur")

    def fake_db():
        yield FakeDB()

    class FakeService:
        def compare_documents(self, document_a, document_b):
            raise AssertionError("Comparison service must not be called")

    monkeypatch.setattr(
        analyst,
        "build_analyst_service",
        lambda db: FakeService(),
    )

    app.dependency_overrides[get_db] = fake_db

    try:
        response = client.post(
            "/analyst/compare",
            json={
                "document_id_a": str(document_id_a),
                "document_id_b": str(document_id_b),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"