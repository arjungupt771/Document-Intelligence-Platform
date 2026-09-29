"""Post-deploy smoke test: confirms the deployed API is serving correctly AND
that authentication is actually enforced. Exit code drives the deploy
workflow's rollback decision.

Env:
  SMOKE_TEST_URL      base URL (e.g. https://api.example.com or http://localhost:8000)
  API_AUTH_KEY        valid API key
  METRICS_AUTH_KEY    optional; when set, /metrics scrape auth is verified too

Nothing here calls the LLM or writes data, so it is safe and free to run repeatedly.
"""
import os
import sys
import time

import httpx

# Every one of these must refuse an unauthenticated request.
PROTECTED = [
    ("POST", "/qa/answer", {"json": {"query": "x"}}),
    ("GET", "/documents/", {}),
    ("GET", "/analyst/insights", {}),
    ("GET", "/drift/results", {}),
    ("GET", "/metrics", {}),
]


def check(base_url: str, api_key: str, metrics_key: str | None) -> bool:
    auth = {"Authorization": f"Bearer {api_key}"}
    try:
        live = httpx.get(f"{base_url}/health/live", timeout=5)
        assert live.status_code == 200, f"liveness check failed: {live.status_code}"

        ready = httpx.get(f"{base_url}/health/ready", timeout=10)
        assert ready.status_code == 200, f"readiness check failed: {ready.status_code}"

        # 1. Authentication is enforced everywhere it must be.
        for method, path, kwargs in PROTECTED:
            anon = httpx.request(method, f"{base_url}{path}", timeout=5, **kwargs)
            assert anon.status_code == 401, f"{method} {path} accepted an unauthenticated request ({anon.status_code})"
            bad = httpx.request(
                method, f"{base_url}{path}", headers={"Authorization": "Bearer wrong"}, timeout=5, **kwargs
            )
            assert bad.status_code == 401, f"{method} {path} accepted a wrong key ({bad.status_code})"

        # 2. A valid key works and reaches the database.
        docs = httpx.get(f"{base_url}/documents/", params={"limit": 1}, headers=auth, timeout=10)
        assert docs.status_code == 200, f"authenticated /documents/ failed: {docs.status_code}"

        # 3. A valid key reaches the QA handler. An empty body is rejected by
        #    validation (422) BEFORE any retrieval/LLM call -> no cost, no side effects.
        qa = httpx.post(f"{base_url}/qa/answer", json={}, headers=auth, timeout=10)
        assert qa.status_code == 422, f"authenticated /qa/answer did not reach handler: {qa.status_code}"

        # 4. Metrics: the scrape key works.
        if metrics_key:
            metrics = httpx.get(
                f"{base_url}/metrics", headers={"Authorization": f"Bearer {metrics_key}"}, timeout=10
            )
            assert metrics.status_code == 200, f"metrics scrape with key failed: {metrics.status_code}"

        return True
    except (AssertionError, httpx.HTTPError) as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        return False


def main() -> None:
    base_url = os.environ["SMOKE_TEST_URL"].rstrip("/")
    api_key = os.environ["API_AUTH_KEY"]
    metrics_key = os.environ.get("METRICS_AUTH_KEY") or None

    for _ in range(5):
        if check(base_url, api_key, metrics_key):
            print("Smoke test passed.")
            sys.exit(0)
        time.sleep(5)

    sys.exit(1)


if __name__ == "__main__":
    main()