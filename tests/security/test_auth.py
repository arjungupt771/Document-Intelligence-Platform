from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.security.auth import require_api_auth


def test_authentication_requires_configuration(monkeypatch):
    monkeypatch.delenv("API_AUTH_KEY", raising=False)

    try:
        require_api_auth(None)
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail == "API authentication is not configured"
    else:
        raise AssertionError("Expected authentication configuration failure")


def test_authentication_requires_credentials(monkeypatch):
    monkeypatch.setenv("API_AUTH_KEY", "test-secret")

    try:
        require_api_auth(None)
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Authentication required"
        assert exc.headers["WWW-Authenticate"] == "Bearer"
    else:
        raise AssertionError("Expected authentication failure")


def test_authentication_rejects_invalid_credentials(monkeypatch):
    monkeypatch.setenv("API_AUTH_KEY", "test-secret")

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="wrong-secret",
    )

    try:
        require_api_auth(credentials)
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid authentication credentials"
    else:
        raise AssertionError("Expected authentication failure")


def test_authentication_accepts_valid_credentials(monkeypatch):
    monkeypatch.setenv("API_AUTH_KEY", "test-secret")

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="test-secret",
    )

    assert require_api_auth(credentials) is None


def test_authentication_error_does_not_expose_api_key(monkeypatch):
    secret = "super-secret-api-key"
    monkeypatch.setenv("API_AUTH_KEY", secret)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="wrong-secret",
    )

    try:
        require_api_auth(credentials)
    except HTTPException as exc:
        assert exc.status_code == 401
        assert secret not in str(exc.detail)
        assert secret not in str(exc.headers)
    else:
        raise AssertionError("Expected authentication failure")