"""Run once per deploy, before traffic is routed to new API replicas.
Idempotent: safe to run on every deploy even if the collection already exists."""
from app.indexing.collections import ensure_collection, get_qdrant_client
from app.indexing.config import QdrantSettings


def main() -> None:
    settings = QdrantSettings.from_env()
    client = get_qdrant_client(settings)
    ensure_collection(client, settings)
    print(f"Qdrant collection '{settings.collection_name}' is ready.")


if __name__ == "__main__":
    main()