import json

from app.qa.context import GroundingContext
from app.qa.models import AnswerSource


class StructuredEvidenceAdapter:
    def from_extraction(
            self,
            query: str,
            extraction,
            field: str | None = None,
            ) -> GroundingContext:
        data = extraction.data or {}

        if field is not None:
            value = data.get(field)
            evidence_text = (
                f"Field: {field}\n"
                f"Value: {value}"
                )
            
        else:
            evidence_text = json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            )

        source = AnswerSource(
            document_id=str(extraction.document_id),
            document_type=extraction.document_type.value,
            text=evidence_text,
            page_number=None,
            score=None,
            )

        return GroundingContext(
            query=query,
            sources=[source],
            )