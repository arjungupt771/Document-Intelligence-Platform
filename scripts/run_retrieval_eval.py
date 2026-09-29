"""
Run offline retrieval evaluation and publish the result as gauges.
Intended to run on a schedule (cron / CI job) against a maintained set of
labeled (query, expected_document_id) examples -- not on every request.
"""
from app.indexing.collections import get_qdrant_client
from app.indexing.config import QdrantSettings
from app.indexing.embeddings import get_embedding_model
from app.observability.metrics import RETRIEVAL_QUALITY_HIT_RATE, RETRIEVAL_QUALITY_MRR
from app.retrieval.evaluation import RetrievalExample, evaluate_retriever
from app.retrieval.qdrant_retriever import QdrantRetriever

# Replace with your maintained labeled set (a fixture file, a DB table, etc).
EXAMPLES = [
    RetrievalExample(query="What is the payment due date?", expected_document_id="<uuid>"),
]


def main() -> None:
    settings = QdrantSettings.from_env()
    retriever = QdrantRetriever(
        client=get_qdrant_client(settings), embedding_model=get_embedding_model(), settings=settings
    )
    report = evaluate_retriever(retriever, EXAMPLES, top_k=5)

    RETRIEVAL_QUALITY_HIT_RATE.set(report.hit_rate_at_k)
    RETRIEVAL_QUALITY_MRR.set(report.mean_reciprocal_rank)
    print(f"hit_rate@k={report.hit_rate_at_k:.3f} mrr={report.mean_reciprocal_rank:.3f} n={report.total_examples}")


if __name__ == "__main__":
    main()