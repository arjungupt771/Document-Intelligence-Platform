import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security.audit_log import log_security_event
from app.security.config import APIAuthSettings


bearer_scheme = HTTPBearer(auto_error=False)


def _require_bearer_auth(
    credentials: HTTPAuthorizationCredentials | None,
    expected_key: str | None,
    missing_config_detail: str,
) -> None:
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=missing_config_detail,
        )

    if credentials is None:
        log_security_event(
            "auth.failure",
            outcome="denied",
            detail="missing credentials",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not secrets.compare_digest(credentials.credentials, expected_key):
        log_security_event(
            "auth.failure",
            outcome="denied",
            detail="invalid token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_api_auth(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> None:
    settings = APIAuthSettings.from_env()

    _require_bearer_auth(
        credentials,
        settings.api_key,
        "API authentication is not configured",
    )


def require_metrics_auth(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> None:
    settings = APIAuthSettings.from_env()

    _require_bearer_auth(
        credentials,
        settings.metrics_key,
        "Metrics authentication is not configured",
    )