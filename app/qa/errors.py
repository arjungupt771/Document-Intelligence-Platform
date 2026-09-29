class LLMError(Exception):
    """Base exception for LLM provider failures."""


class LLMConnectionError(LLMError):
    """Raised when the LLM provider cannot be reached."""


class LLMTimeoutError(LLMError):
    """Raised when the LLM provider exceeds the configured timeout."""


class LLMResponseError(LLMError):
    """Raised when the LLM provider returns an invalid response."""