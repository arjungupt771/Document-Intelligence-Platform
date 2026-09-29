from fastapi.testclient import TestClient

from app.main import app
from app.observability.request_limits import MAX_REQUEST_BODY_SIZE

client = TestClient(app)


def test_assigns_request_id_header():
    response = client.get("/health/live")
    assert "X-Request-ID" in response.headers


def test_request_within_body_limit_is_accepted():
    response = client.post(
        "/health/live",
        content=b"x" * 1024,
        headers={"Content-Length": "1024"},
    )

    assert response.status_code in {200, 405}


def test_request_exceeding_body_limit_is_rejected():
    oversized = MAX_REQUEST_BODY_SIZE + 1

    response = client.post(
        "/health/live",
        content=b"x",
        headers={"Content-Length": str(oversized)},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Request body is too large"}


def test_invalid_content_length_is_rejected():
    response = client.post(
        "/health/live",
        content=b"x",
        headers={"Content-Length": "not-a-number"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Content-Length header"}

def test_propagates_inbound_request_id():
    response = client.get("/health/live", headers={"X-Request-ID": "fixed-id"})
    assert response.headers["X-Request-ID"] == "fixed-id"