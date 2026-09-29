"""Single source of truth for which underlying exceptions count as a
Qdrant connectivity/availability fault. Import this tuple everywhere
Qdrant is called, so retriever and indexer never disagree on what's
retryable/wrappable."""
import httpx
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

QDRANT_CONNECTIVITY_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
    ResponseHandlingException,
)


def is_qdrant_server_fault(exc: UnexpectedResponse) -> bool:
    """5xx from Qdrant itself is a service-availability fault, not a client bug.
    4xx (bad request, e.g. malformed filter) should NOT be swallowed as
    'unavailable' -- that would hide real bugs behind a generic 503."""
    return exc.status_code >= 500