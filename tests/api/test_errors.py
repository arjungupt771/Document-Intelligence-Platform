from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.main import app


def test_database_error_response_does_not_expose_details(monkeypatch):
    async def failing_handler(request: Request):
        raise SQLAlchemyError(
            "postgresql://secret-user:secret-password@db.internal:5432/documents"
        )

    app.add_api_route("/test-database-error", failing_handler, methods=["GET"])

    client = TestClient(
    app,
    raise_server_exceptions=False,
    headers={"Authorization": "Bearer test-secret"},
)

    try:
        response = client.get("/test-database-error")
    finally:
        app.router.routes.pop()

    assert response.status_code == 500
    assert response.json() == {"detail": "Database operation failed"}

    body = response.text
    assert "secret-user" not in body
    assert "secret-password" not in body
    assert "db.internal" not in body
    assert "postgresql://" not in body
