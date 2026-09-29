from __future__ import annotations

from prometheus_client import Counter, Histogram

# --- Document processing (14.4) ---------------------------------------
DOCUMENT_PROCESSED_TOTAL = Counter(
    "document_processed_total",
    "Documents that finished the classify+extract pipeline, by outcome",
    ["document_type", "status"],  # status: completed | unclassified | unsupported
)
DOCUMENT_PROCESSING_DURATION = Histogram(
    "document_processing_duration_seconds",
    "Time to classify + extract one document",
    ["document_type"],
)

# --- Extraction (14.5) ---------------------------------------------------
EXTRACTION_RESULT_TOTAL = Counter(
    "extraction_result_total",
    "Extraction attempts by outcome",
    ["document_type", "status"],  # status: completed | failed
)
EXTRACTION_CONFIDENCE = Histogram(
    "extraction_confidence",
    "Confidence score distribution of completed extractions",
    ["document_type"],
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

# --- Retrieval (14.6, 14.10) -------------------------------------------
RETRIEVAL_LATENCY = Histogram("retrieval_latency_seconds", "Time spent in Retriever.retrieve")
RETRIEVAL_RESULT_TOTAL = Counter(
    "retrieval_result_total", "Retrieval calls by whether they returned any chunks", ["result"]  # hit | empty
)
from prometheus_client import Gauge  # noqa: E402 -- grouped with the metric it belongs to, for readability

RETRIEVAL_QUALITY_HIT_RATE = Gauge("retrieval_quality_hit_rate", "Most recent offline retrieval eval hit_rate@k")
RETRIEVAL_QUALITY_MRR = Gauge("retrieval_quality_mrr", "Most recent offline retrieval eval MRR")

# --- QA / LLM (14.7, 14.8, 14.11) ---------------------------------------
QA_LATENCY = Histogram("qa_latency_seconds", "Time spent in QAService.answer", ["query_type"])
LLM_LATENCY = Histogram("llm_latency_seconds", "Time spent waiting on the LLM provider")
LLM_TOKENS_TOTAL = Counter("llm_tokens_estimated_total", "Estimated prompt+completion tokens sent to the LLM")
VERIFICATION_RESULT_TOTAL = Counter(
    "verification_result_total", "Grounding verification outcomes", ["surface", "verified"]  # surface: qa | insight
)

# --- Errors (14.9) --------------------------------------------------------
LLM_ERROR_TOTAL = Counter("llm_error_total", "LLM client errors by type", ["error_type"])
ERROR_TOTAL = Counter("error_total", "Unhandled exceptions by component", ["component", "exception_type"])


def estimate_tokens(text: str) -> int:
    """~4 chars/token approximation -- good enough for cost/usage tracking without pulling in a tokenizer."""
    return max(1, len(text) // 4)