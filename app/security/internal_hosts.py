
import os


def is_trusted_internal_host(hostname: str | None) -> bool:
    if not hostname:
        return False
    raw = os.getenv("INTERNAL_SERVICE_HOSTS", "")
    trusted = {h.strip().lower() for h in raw.split(",") if h.strip()}
    return hostname.lower() in trusted