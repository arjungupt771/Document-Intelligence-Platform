from __future__ import annotations

from dataclasses import dataclass

from app.retrieval.interface import Retriever


@dataclass(frozen=True)
class RetrievalExample:
    query: str
    expected_document_id: str


@dataclass(frozen=True)
class RetrievalEvalReport:
    hit_rate_at_k: float
    mean_reciprocal_rank: float
    total_examples: int


def evaluate_retriever(
    retriever: Retriever,
    examples: list[RetrievalExample],
    top_k: int = 5,
) -> RetrievalEvalReport:
    """
    Runs each labeled (query, expected_document_id) example through the
    retriever and reports:
      - hit_rate@k: fraction of queries where the expected document
        appears anywhere in the top-k results
      - MRR: mean reciprocal rank of the expected document (0 if absent)
    """
    if not examples:
        return RetrievalEvalReport(hit_rate_at_k=0.0, mean_reciprocal_rank=0.0, total_examples=0)

    hits = 0
    reciprocal_ranks = []

    for example in examples:
        result = retriever.retrieve(example.query, top_k=top_k)
        document_ids = [chunk.document_id for chunk in result.chunks]

        if example.expected_document_id in document_ids:
            hits += 1
            rank = document_ids.index(example.expected_document_id) + 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

    return RetrievalEvalReport(
        hit_rate_at_k=hits / len(examples),
        mean_reciprocal_rank=sum(reciprocal_ranks) / len(examples),
        total_examples=len(examples),
    )
