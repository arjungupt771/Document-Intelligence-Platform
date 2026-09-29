from __future__ import annotations

import statistics
from typing import Optional

from app.documents.models import DocumentType
from app.drift.models import BaselineSnapshot
from app.drift.psi import bin_numeric, proportions, quantile_edges
from app.storage.repository import DocumentRepository, ExtractionRepository

NUMERIC_FIELDS_BY_TYPE: dict[DocumentType, list[str]] = {
    DocumentType.INVOICE: ["total", "subtotal", "tax"],
    DocumentType.PURCHASE_ORDER: ["total"],
}
MIN_VALUES_FOR_BINNING = 5


class BaselineSnapshotBuilder:
    """
    Builds a BaselineSnapshot from the current corpus. Meant to run once
    to establish the initial baseline, then again only on a deliberate
    re-baselining decision -- a baseline that updates itself continuously
    could never detect drift against it.
    """

    def __init__(self, document_repository: DocumentRepository, extraction_repository: ExtractionRepository):
        self._documents = document_repository
        self._extractions = extraction_repository

    def build(self, document_type: DocumentType) -> Optional[BaselineSnapshot]:
        rows = self._extractions.list_completed_by_document_type(document_type)
        if not rows:
            return None

        # Document-type mix is corpus-wide (invoice vs PO vs contract vs
        # unknown), not scoped to `document_type` -- every per-type
        # snapshot stores the same corpus-wide figure so it's always
        # available alongside whichever type's baseline is being checked.
        type_counts = self._documents.count_by_document_type()

        schema_keys: set[str] = set()
        presence_counts: dict[str, int] = {}
        confidences: list[float] = []
        numeric_values: dict[str, list[float]] = {
            name: [] for name in NUMERIC_FIELDS_BY_TYPE.get(document_type, [])
        }

        for row in rows:
            data = row.data or {}
            schema_keys.update(data.keys())
            for key, value in data.items():
                if value not in (None, "", []):
                    presence_counts[key] = presence_counts.get(key, 0) + 1
            if row.confidence is not None:
                confidences.append(row.confidence)
            for field_name in numeric_values:
                value = data.get(field_name)
                if value is None:
                    continue
                try:
                    numeric_values[field_name].append(float(value))
                except (TypeError, ValueError):
                    continue

        presence_rates = {key: count / len(rows) for key, count in presence_counts.items()}

        numeric_field_bins = {}
        for field_name, values in numeric_values.items():
            if len(values) < MIN_VALUES_FOR_BINNING:
                continue
            edges = quantile_edges(values, n_bins=5)
            counts = bin_numeric(values, edges)
            numeric_field_bins[field_name] = {"edges": edges, "distribution": proportions(counts)}

        return BaselineSnapshot(
            document_type_distribution=proportions(type_counts),
            field_presence_rates=presence_rates,
            numeric_field_bins=numeric_field_bins,
            schema_keys=sorted(schema_keys),
            mean_extraction_confidence=statistics.mean(confidences) if confidences else None,
            sample_size=len(rows),
        )