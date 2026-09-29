"""One-off / scheduled script to (re-)establish a drift baseline for one document type."""
import sys

from app.documents.models import DocumentType
from app.drift.factory import build_drift_service
from app.storage.database import session_scope


def main(document_type_value: str) -> None:
    document_type = DocumentType(document_type_value)
    with session_scope() as session:
        service = build_drift_service(session)
        snapshot_id = service.establish_baseline(document_type)

    if snapshot_id is None:
        print(f"No completed extractions found for {document_type.value}; baseline not established.")
    else:
        print(f"Baseline {snapshot_id} established for {document_type.value}.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "invoice")