"""Validates that a URL is safe to have the server fetch, before any
outbound request is made from user-influenced input. Use this on any
FUTURE feature that accepts a URL from a client (webhook URLs, "fetch
document from link", etc). Do not use this for operator-configured URLs
(LLM_URL, QDRANT_URL) -- those are already validated at startup in
their own settings classes and trusted as deployment configuration.
"""
import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"https"}

_BLOCKED_HOSTNAMES = {"localhost", "metadata.google.internal", "169.254.169.254"}


class SSRFValidationError(ValueError):
    pass


def validate_allowlisted_https_url(url: str, allowed_hosts) -> None:
    """Raises SSRFValidationError unless `url` is HTTPS, has no embedded
    credentials, is not an IP literal / blocked hostname, and its hostname
    is exactly one of `allowed_hosts`. Performs no DNS lookup (the
    allowlist is the control), so it is safe to call at startup."""
    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise SSRFValidationError("URL must use https")

    if parsed.username is not None or parsed.password is not None:
        raise SSRFValidationError("URL must not contain embedded credentials")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise SSRFValidationError("URL must include a hostname")

    if hostname in _BLOCKED_HOSTNAMES:
        raise SSRFValidationError("URL host is not allowed")

    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass  # not an IP literal -> fine
    else:
        raise SSRFValidationError("URL host must be a DNS name, not an IP address")

    allowed = {h.strip().lower() for h in allowed_hosts if h and h.strip()}
    if hostname not in allowed:
        raise SSRFValidationError(f"URL host '{hostname}' is not in the allowed host list")

def validate_outbound_url(url: str) -> None:
    """Raises SSRFValidationError if the URL could be used to reach
    internal infrastructure (loopback, link-local/cloud metadata,
    private RFC1918 ranges) instead of a legitimate external resource."""
    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise SSRFValidationError(f"URL scheme must be one of {ALLOWED_SCHEMES}")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("URL must include a hostname")

    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise SSRFValidationError("URL host is not allowed")

    try:
        resolved_ips = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
    except socket.gaierror as exc:
        raise SSRFValidationError("URL host could not be resolved") from exc

    for ip_str in resolved_ips:
        ip = ipaddress.ip_address(ip_str)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        ):
            raise SSRFValidationError(
                "URL resolves to a private, loopback, or link-local address"
            )


def safe_get(url: str, **kwargs):
    """Convenience wrapper: validates, then fetches, with redirects
    disabled by default (a validated URL that 302s to an internal IP
    is the classic SSRF-via-redirect bypass)."""
    import httpx

    validate_outbound_url(url)
    kwargs.setdefault("follow_redirects", False)
    kwargs.setdefault("timeout", 10)
    return httpx.get(url, **kwargs)