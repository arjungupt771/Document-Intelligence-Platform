from dotenv import load_dotenv

load_dotenv()

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends
from app.security.auth import require_api_auth, require_metrics_auth
from app.api.analyst import router as analyst_router
from app.api.documents import router as documents_router
from app.api.drift import router as drift_router
from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.api.qa import router as qa_router
from app.observability.logging import configure_logging
from app.observability.middleware import RequestTracingMiddleware
from app.observability.request_limits import RequestBodyLimitMiddleware
from app.security.secrets import validate_secrets
from app.qa.config import validate_llm_config
from app.security.rate_limit import RateLimitMiddleware


validate_secrets()
validate_llm_config()

async def database_exception_handler(request, exc: SQLAlchemyError):
    print(f"DATABASE ERROR: {exc!r}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Database operation failed"},
    )


configure_logging()

app = FastAPI(title="Document Intelligence Platform")
app.add_exception_handler(SQLAlchemyError, database_exception_handler)

app.add_middleware(RequestTracingMiddleware)
app.add_middleware(RequestBodyLimitMiddleware)
app.add_middleware(RateLimitMiddleware)


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


# Added LAST so it is the OUTERMOST middleware: 401/413/429 responses then also
# carry CORS headers, and the browser shows the real error instead of a
# generic "Failed to fetch". Explicit origins only -- never "*" with credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["Retry-After"],
    max_age=600,
)

app.include_router(
    documents_router,
    dependencies=[Depends(require_api_auth)],
)

app.include_router(
    qa_router,
    dependencies=[Depends(require_api_auth)],
)

app.include_router(
    analyst_router,
    dependencies=[Depends(require_api_auth)],
)
app.include_router(health_router)

app.include_router(
    metrics_router,
    dependencies=[Depends(require_metrics_auth)],
)

app.include_router(
    drift_router,
    dependencies=[Depends(require_api_auth)],
)