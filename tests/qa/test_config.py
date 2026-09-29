from app.qa.config import LLMSettings
import pytest


def test_llm_settings_use_defaults(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    for name in (
        "LLM_URL",
        "LLM_ENDPOINT",
        "LLM_MODEL",
        "LLM_TIMEOUT",
        "LLM_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = LLMSettings.from_env()

    assert settings.url == "https://api.groq.com/openai/v1"
    assert settings.endpoint == "/chat/completions"
    assert settings.model == "openai/gpt-oss-120b"
    assert settings.timeout == 30.0
    assert settings.api_key is None


def test_llm_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LLM_URL", "https://llm.example.com")
    monkeypatch.setenv("LLM_ENDPOINT", "/v1/generate")
    monkeypatch.setenv("LLM_MODEL", "document-model")
    monkeypatch.setenv("LLM_TIMEOUT", "45.5")
    monkeypatch.setenv("LLM_API_KEY", "secret-key")

    settings = LLMSettings.from_env()

    assert settings.url == "https://llm.example.com"
    assert settings.endpoint == "/v1/generate"
    assert settings.model == "document-model"
    assert settings.timeout == 45.5
    assert settings.api_key == "secret-key"


def test_llm_settings_are_immutable():
    settings = LLMSettings.from_env()

    try:
        settings.url = "http://changed"
        assert False, "LLMSettings should be immutable"
    except AttributeError:
        pass

def test_llm_settings_reject_empty_url(monkeypatch):
    monkeypatch.setenv("LLM_URL", "")

    with pytest.raises(ValueError, match="LLM_URL"):
        LLMSettings.from_env()


def test_llm_settings_reject_empty_endpoint(monkeypatch):
    monkeypatch.setenv("LLM_ENDPOINT", "")

    with pytest.raises(ValueError, match="LLM_ENDPOINT"):
        LLMSettings.from_env()


def test_llm_settings_reject_empty_model(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "")

    with pytest.raises(ValueError, match="LLM_MODEL"):
        LLMSettings.from_env()


def test_llm_settings_reject_non_positive_timeout(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT", "0")

    with pytest.raises(ValueError, match="LLM_TIMEOUT"):
        LLMSettings.from_env()


def test_llm_settings_reject_negative_timeout(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT", "-1")

    with pytest.raises(ValueError, match="LLM_TIMEOUT"):
        LLMSettings.from_env()

# ---- production / startup validation ----

import pytest as _pytest
from app.qa.config import validate_llm_config


@_pytest.fixture
def production_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LLM_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.delenv("LLM_ALLOWED_HOSTS", raising=False)


def test_production_accepts_groq(production_env):
    validate_llm_config()


def test_production_requires_api_key(production_env, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY")
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        validate_llm_config()


def test_production_rejects_plain_http(production_env, monkeypatch):
    monkeypatch.setenv("LLM_URL", "http://api.groq.com/openai/v1")
    with pytest.raises(ValueError, match="LLM_URL"):
        validate_llm_config()


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example.com/v1",
        "https://169.254.169.254/latest",
        "https://localhost/v1",
        "https://10.0.0.5/v1",
    ],
)
def test_production_rejects_non_allowlisted_hosts(production_env, monkeypatch, url):
    monkeypatch.setenv("LLM_URL", url)
    with pytest.raises(ValueError, match="LLM_URL"):
        validate_llm_config()


def test_production_allows_extra_host_only_when_listed(production_env, monkeypatch):
    monkeypatch.setenv("LLM_URL", "https://llm.example.com/v1")
    monkeypatch.setenv("LLM_ALLOWED_HOSTS", "api.groq.com,llm.example.com")
    validate_llm_config()


def test_endpoint_must_start_with_slash(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LLM_ENDPOINT", "chat/completions")
    with pytest.raises(ValueError, match="LLM_ENDPOINT"):
        LLMSettings.from_env()


def test_timeout_must_be_numeric(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LLM_TIMEOUT", "abc")
    with pytest.raises(ValueError, match="LLM_TIMEOUT"):
        LLMSettings.from_env()


def test_repr_does_not_leak_api_key(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LLM_API_KEY", "super-secret-value")
    assert "super-secret-value" not in repr(LLMSettings.from_env())