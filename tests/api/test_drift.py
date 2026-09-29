from fastapi.testclient import TestClient

from app.main import app
from app.storage.database import get_db

client = TestClient(
    app,
    headers={"Authorization": "Bearer test-secret"},
)
class FakeDB:
    def commit(self):
        pass

def test_establish_baseline_endpoint(monkeypatch):
    from app.api import drift

    class FakeService:
        def establish_baseline(self, document_type):
            assert document_type.value == "invoice"
            return "snapshot-1"

    monkeypatch.setattr(drift, "build_drift_service", lambda db: FakeService())

    def fake_db():
        yield FakeDB()

    app.dependency_overrides[get_db] = fake_db
    try:
        response = client.post("/drift/baseline", json={"document_type": "invoice"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"snapshot_id": "snapshot-1", "established": True}


def test_check_drift_endpoint(monkeypatch):
    from app.api import drift
    from app.drift.models import DriftDimension, DriftResult, DriftSeverity

    class FakeService:
        def check_drift(self, document_type, current_hit_rate=None, current_mrr=None):
            return [
                DriftResult(
                    dimension=DriftDimension.NUMERIC_VALUE,
                    key="total",
                    score=0.4,
                    severity=DriftSeverity.SIGNIFICANT,
                    baseline_summary={},
                    current_summary={},
                )
            ]

    monkeypatch.setattr(drift, "build_drift_service", lambda db: FakeService())

    def fake_db():
        yield FakeDB()

    app.dependency_overrides[get_db] = fake_db
    try:
        response = client.post("/drift/check", json={"document_type": "invoice"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data[0]["key"] == "total"
    assert data[0]["severity"] == "significant"