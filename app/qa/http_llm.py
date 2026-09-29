import httpx

from app.qa.llm import LLMClient


class HTTPClientLLM(LLMClient):
    def __init__(
        self,
        base_url: str,
        endpoint: str = "/generate",
        timeout: float = 30.0,
        transport=None,
    ):
        self._base_url = base_url.rstrip("/")
        self._endpoint = endpoint
        self._client = httpx.Client(
            timeout=timeout,
            transport=transport,
        )

    def generate(self, prompt: str) -> str:
        response = self._client.post(
            f"{self._base_url}{self._endpoint}",
            json={"prompt": prompt},
        )

        response.raise_for_status()

        data = response.json()

        return data["answer"]