from sqlalchemy.orm import Session

from app.drift.embedding_sampler import ChunkEmbeddingSampler
from app.drift.service import DriftMonitoringService
from app.indexing.collections import get_qdrant_client
from app.indexing.config import QdrantSettings
from app.storage.repository import (
    BaselineSnapshotRepository,
    DocumentRepository,
    DriftAlertRepository,
    DriftResultRepository,
    ExtractionRepository,
)


def build_drift_service(session: Session) -> DriftMonitoringService:
    qdrant_settings = QdrantSettings.from_env()
    sampler = ChunkEmbeddingSampler(client=get_qdrant_client(qdrant_settings), settings=qdrant_settings)

    return DriftMonitoringService(
        document_repository=DocumentRepository(session),
        extraction_repository=ExtractionRepository(session),
        baseline_repository=BaselineSnapshotRepository(session),
        drift_result_repository=DriftResultRepository(session),
        drift_alert_repository=DriftAlertRepository(session),
        embedding_sampler=sampler,
    )