import os
from dataclasses import dataclass

@dataclass(frozen=True)
class APIAuthSettings:
    api_key: str | None
    metrics_key: str | None

    @classmethod
    def from_env(cls) -> "APIAuthSettings":
        return cls(
            api_key=os.getenv("API_AUTH_KEY") or None,
            metrics_key=os.getenv("METRICS_AUTH_KEY") or None,
        )