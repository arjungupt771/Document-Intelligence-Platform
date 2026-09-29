"""Best-effort detection of prompt-injection patterns in retrieved context.

This is a defense-in-depth layer, not a guarantee. It flags/strips
suspicious instruction-like content pulled from *document* text before
it's interpolated into the LLM prompt, and it never trusts document
content as instructions in the prompt template itself (see prompt.py:
document content must be clearly delimited from system instructions).
"""
import re
from dataclasses import dataclass

_SUSPICIOUS_PATTERNS = [
    re.compile(r"ignore (all |the )?(previous|prior|above) instructions", re.I),
    re.compile(r"disregard (all |the )?(previous|prior|above)", re.I),
    re.compile(r"you are now", re.I),
    re.compile(r"system prompt", re.I),
    re.compile(r"reveal (your|the) (system prompt|instructions)", re.I),
    re.compile(r"act as (an? )?(unrestricted|jailbroken)", re.I),
    re.compile(r"\bDAN\b"),
]


@dataclass(frozen=True)
class InjectionScanResult:
    flagged: bool
    matched_patterns: tuple[str, ...]


def scan(text: str) -> InjectionScanResult:
    matches = tuple(p.pattern for p in _SUSPICIOUS_PATTERNS if p.search(text))
    return InjectionScanResult(flagged=bool(matches), matched_patterns=matches)


def sanitize_context_chunk(text: str) -> str:
    """
    Wrap retrieved document text so the LLM prompt structure makes clear
    it is DATA, not instructions -- even if the scan above misses a novel
    phrasing. Use this when building context in qa/context.py.
    """
    return (
        "<document_excerpt>\n"
        + text.replace("</document_excerpt>", "")  # prevent closing-tag injection
        + "\n</document_excerpt>"
    )