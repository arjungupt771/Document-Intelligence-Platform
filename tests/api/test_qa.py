from fastapi.testclient import TestClient

from app.main import app
from app.storage.database import get_db


client = TestClient(
    app,
    headers={"Authorization": "Bearer test-secret"},
)

def test_qa_answer_endpoint(monkeypatch):
    from app.api import qa

    class FakeResult:
        query = "What are the payment terms?"
        answer = "Payment is due within 30 days."
        grounded = True
        verified = True
        unsupported_claims = []
        verification_reason = "Answer is supported."
        sources = []

    class FakeService:
        def answer(
            self,
            request,
            top_k=5,
            document_type=None,
            document_id=None,
            score_threshold=None,
        ):
            assert request.query == "What are the payment terms?"
            assert top_k == 5
            return FakeResult()

    monkeypatch.setattr(
        qa,
        "build_qa_service",
        lambda db: FakeService(),
    )

    def fake_db():
        yield object()

    app.dependency_overrides[get_db] = fake_db

    try:
        response = client.post(
            "/qa/answer",
            json={
                "query": "What are the payment terms?"
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "What are the payment terms?"
    assert data["answer"] == "Payment is due within 30 days."
    assert data["grounded"] is True
    assert data["verified"] is True
    assert data["unsupported_claims"] == []
    assert data["verification_reason"] == "Answer is supported."
    assert data["sources"] == []

def test_qa_rejects_missing_document(monkeypatch):
    from app.api import qa

    document_id = "00000000-0000-0000-0000-000000000001"

    class FakeDB:
        def get(self, model, requested_document_id):
            return None

    def fake_db():
        yield FakeDB()

    class FakeService:
        def answer(self, *args, **kwargs):
            raise AssertionError("QA service must not be called")

    monkeypatch.setattr(
        qa,
        "build_qa_service",
        lambda db: FakeService(),
    )

    app.dependency_overrides[get_db] = fake_db

    try:
        response = client.post(
            "/qa/answer",
            json={
                "query": "What are the payment terms?",
                "document_id": document_id,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"

def test_qa_answer_returns_503_when_llm_is_unavailable(monkeypatch):
    from app.api import qa
    from app.qa.errors import LLMConnectionError, LLMResponseError, LLMTimeoutError

    for error in (LLMTimeoutError, LLMConnectionError, LLMResponseError):

        class FailingService:
            def answer(self, request, **kwargs):
                raise error("provider detail that must not leak")

        monkeypatch.setattr(qa, "build_qa_service", lambda db: FailingService())

        def fake_db():
            yield object()

        app.dependency_overrides[get_db] = fake_db
        try:
            response = client.post("/qa/answer", json={"query": "What is the total?"})
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 503
        assert "provider detail" not in response.text