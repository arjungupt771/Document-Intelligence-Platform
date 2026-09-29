import pytest

from app.security.ssrf_guard import SSRFValidationError, validate_allowlisted_https_url

ALLOWED = ["api.groq.com"]


def test_allows_groq():
    validate_allowlisted_https_url("https://api.groq.com/openai/v1", ALLOWED)


@pytest.mark.parametrize(
    "url",
    [
        "http://api.groq.com/openai/v1",            # not https
        "https://api.groq.com.evil.example/v1",     # lookalike host
        "https://user:pw@api.groq.com/v1",          # embedded credentials
        "https://127.0.0.1/v1",                     # IP literal
        "https://169.254.169.254/latest/meta-data", # cloud metadata
        "https://localhost/v1",
        "https:///v1",                              # no hostname
    ],
)
def test_rejects_unsafe_urls(url):
    with pytest.raises(SSRFValidationError):
        validate_allowlisted_https_url(url, ALLOWED)