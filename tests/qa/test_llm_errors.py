from app.qa.errors import (
    LLMConnectionError,
    LLMError,
    LLMResponseError,
    LLMTimeoutError,
)


def test_llm_errors_share_common_base():
    assert issubclass(LLMConnectionError, LLMError)
    assert issubclass(LLMTimeoutError, LLMError)
    assert issubclass(LLMResponseError, LLMError)


def test_llm_errors_can_be_created_with_messages():
    assert str(LLMConnectionError("connection failed")) == "connection failed"
    assert str(LLMTimeoutError("request timed out")) == "request timed out"
    assert str(LLMResponseError("invalid response")) == "invalid response"