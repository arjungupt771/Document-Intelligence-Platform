from fastapi.testclient import TestClient
import os
from app.main import app


client = TestClient(app)


def test_metrics_requires_authentication():
    response = client.get("/metrics")

    assert response.status_code == 401


def test_metrics_summary_requires_authentication():
    response = client.get("/metrics/summary")

    assert response.status_code == 401


def test_metrics_accepts_valid_authentication():
    response = client.get(
        "/metrics",
        headers={
    "Authorization": f"Bearer {os.environ['METRICS_AUTH_KEY']}",
},
    )

    assert response.status_code == 200


def test_metrics_summary_accepts_valid_authentication():
    response = client.get(
        "/metrics/summary",
        headers={
    "Authorization": f"Bearer {os.environ['METRICS_AUTH_KEY']}",
},
    )

    assert response.status_code == 200


def test_health_liveness_remains_public():
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}