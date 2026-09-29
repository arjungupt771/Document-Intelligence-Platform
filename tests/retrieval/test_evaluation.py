from unittest.mock import MagicMock

from app.retrieval.evaluation import RetrievalExample, evaluate_retriever
from app.retrieval.models import RetrievalResult, RetrievedChunk


def _result(document_ids: list[str]) -> RetrievalResult:
    chunks = [
        RetrievedChunk(document_id=doc_id, document_type="invoice", chunk_index=0, page_number=1, text="", score=1.0)
        for doc_id in document_ids
    ]
    return RetrievalResult(query="q", chunks=chunks, total_candidates=len(chunks))


def test_hit_rate_and_mrr():
    retriever = MagicMock()
    retriever.retrieve.side_effect = [
        _result(["doc-1", "doc-2"]),  # expected doc-1, found at rank 1
        _result(["doc-3", "doc-4"]),  # expected doc-5, missing entirely
    ]

    examples = [
        RetrievalExample(query="q1", expected_document_id="doc-1"),
        RetrievalExample(query="q2", expected_document_id="doc-5"),
    ]

    report = evaluate_retriever(retriever, examples, top_k=2)

    assert report.total_examples == 2
    assert report.hit_rate_at_k == 0.5
    assert report.mean_reciprocal_rank == 0.5  # (1.0 + 0.0) / 2


def test_reciprocal_rank_accounts_for_position():
    retriever = MagicMock()
    retriever.retrieve.return_value = _result(["doc-9", "doc-1", "doc-2"])  # expected at rank 2

    report = evaluate_retriever(retriever, [RetrievalExample(query="q", expected_document_id="doc-1")])

    assert report.hit_rate_at_k == 1.0
    assert report.mean_reciprocal_rank == 0.5  # 1 / rank(2)


def test_empty_examples_returns_zeroed_report():
    report = evaluate_retriever(MagicMock(), [])
    assert report.total_examples == 0
    assert report.hit_rate_at_k == 0.0
    assert report.mean_reciprocal_rank == 0.0
