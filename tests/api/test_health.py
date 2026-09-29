from fastapi.testclient import TestClient

import app.api.health as health_api
from app.main import app
from app.observability.health import ComponentHealth
from app.storage.database import get_db


client = TestClient(app)


def test_liveness():
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_when_all_dependencies_are_healthy(monkeypatch):
    class FakeSession:
        pass

    def override_get_db():
        yield FakeSession()

    monkeypatch.setattr(
        health_api,
        "check_database",
        lambda db: ComponentHealth(
            name="database",
            healthy=True,
            latency_ms=10.0,
        ),
    )
    monkeypatch.setattr(
        health_api,
        "check_qdrant",
        lambda: ComponentHealth(
            name="qdrant",
            healthy=True,
            latency_ms=20.0,
        ),
    )

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ready"
    assert len(body["checks"]) == 2
    assert all(check["healthy"] is True for check in body["checks"])


def test_readiness_returns_503_when_database_is_unhealthy(monkeypatch):
    class FakeSession:
        pass

    def override_get_db():
        yield FakeSession()

    monkeypatch.setattr(
        health_api,
        "check_database",
        lambda db: ComponentHealth(
            name="database",
            healthy=False,
            detail="Database health check failed",
            latency_ms=10.0,
        ),
    )
    monkeypatch.setattr(
        health_api,
        "check_qdrant",
        lambda: ComponentHealth(
            name="qdrant",
            healthy=True,
            latency_ms=20.0,
        ),
    )

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503

    body = response.json()

    assert body["status"] == "not_ready"
    assert body["checks"][0]["healthy"] is False


def test_readiness_returns_503_when_qdrant_is_unhealthy(monkeypatch):
    class FakeSession:
        pass

    def override_get_db():
        yield FakeSession()

    monkeypatch.setattr(
        health_api,
        "check_database",
        lambda db: ComponentHealth(
            name="database",
            healthy=True,
            latency_ms=10.0,
        ),
    )
    monkeypatch.setattr(
        health_api,
        "check_qdrant",
        lambda: ComponentHealth(
            name="qdrant",
            healthy=False,
            detail="Qdrant health check failed",
            latency_ms=10.0,
        ),
    )

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503

    body = response.json()

    assert body["status"] == "not_ready"
    assert body["checks"][1]["healthy"] is False


def test_readiness_returns_degraded_when_dependency_is_slow(monkeypatch):
    class FakeSession:
        pass

    def override_get_db():
        yield FakeSession()

    monkeypatch.setattr(
        health_api,
        "check_database",
        lambda db: ComponentHealth(
            name="database",
            healthy=True,
            latency_ms=1500.0,
        ),
    )
    monkeypatch.setattr(
        health_api,
        "check_qdrant",
        lambda: ComponentHealth(
            name="qdrant",
            healthy=True,
            latency_ms=20.0,
        ),
    )

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "degraded"
