"""Renders a runtime .env from a secrets backend at deploy time.
Supports GitHub Actions secrets (passed as env vars by the workflow) today;
swap `_read_secret` for a Vault/AWS Secrets Manager/GCP Secret Manager call
if you move off GitHub-native secrets later -- nothing else in this script
needs to change.
"""
import os
import sys

REQUIRED_SECRETS = [
    "DATABASE_URL",
    "API_AUTH_KEY",
    "QDRANT_API_KEY",
    "POSTGRES_PASSWORD",
    "LLM_API_KEY",
]


def _read_secret(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"FATAL: required secret {name} is not set in the deploy environment", file=sys.stderr)
        sys.exit(1)
    return value


def main() -> None:
    lines = [f"{name}={_read_secret(name)}" for name in REQUIRED_SECRETS]
    lines.append(f"APP_ENV={os.environ.get('APP_ENV', 'production')}")

    with open(".env", "w") as f:
        f.write("\n".join(lines) + "\n")

    os.chmod(".env", 0o600)  # not world/group readable on the deploy host


if __name__ == "__main__":
    main()