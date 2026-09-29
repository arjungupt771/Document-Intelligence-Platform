import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def _development_env(monkeypatch):
    """app.main calls load_dotenv(); a developer's .env (APP_ENV=production)
    must not change how unit tests validate config. Tests that need
    production behaviour set APP_ENV themselves."""
    monkeypatch.setenv("API_AUTH_KEY", "test-secret")


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-secret"}


@pytest.fixture
def authenticated_client():
    return TestClient(
        app,
        headers={"Authorization": "Bearer test-secret"},
    )