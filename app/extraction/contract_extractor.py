import re
from typing import Optional

from app.extraction.base import ExtractionResult, Extractor
from app.extraction.normalization import normalize_date
from app.extraction.schemas import ContractSchema
from app.parsing.models import ParsedDocument

_FIELD_PATTERNS: dict[str, re.Pattern] = {
    "effective_date": re.compile(
        r"effective\s*date\s*[:\-]?\s*([A-Za-z0-9,\s/\-]+?)(?=[.,;\n]|$)", re.IGNORECASE
    ),
    "termination_date": re.compile(
        r"termination\s*date\s*[:\-]?\s*([A-Za-z0-9,\s/\-]+?)(?=[.,;\n]|$)", re.IGNORECASE
    ),
    "payment_terms": re.compile(
        r"payment\s*terms\s*[:\-]?\s*(.+?)(?=\n\s*\n|\n[A-Z][a-z]+\s*[:\-]|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    "renewal_terms": re.compile(
        r"renewal\s*terms\s*[:\-]?\s*(.+?)(?=\n\s*\n|\n[A-Z][a-z]+\s*[:\-]|$)",
        re.IGNORECASE | re.DOTALL,
    ),
}

_PARTIES_PATTERN = re.compile(
    r"(?:entered into|made)\s*(?:by and)?\s*between\s+(.+?)\s+and\s+(.+?)(?=[.,;\n]|$)",
    re.IGNORECASE,
)

_OBLIGATION_PATTERN = re.compile(r"([^.\n]*\bshall\b[^.\n]*\.)", re.IGNORECASE)

_CLAUSE_PATTERN = re.compile(r"(?:^|\n)\s*(\d+(?:\.\d+)?)[\.\)]\s+(.+?)(?=\n\s*\d+(?:\.\d+)?[\.\)]\s|\Z)", re.DOTALL)


class ContractExtractor(Extractor[ContractSchema]):
    """
    Baseline extractor for contracts. Dates and named terms are pulled
    with targeted regexes; parties are inferred from "between X and Y"
    phrasing; obligations and clauses use structural heuristics
    ("shall" sentences, numbered clauses) since contracts vary far more
    in layout than invoices/POs.
    """

    def extract(self, document: ParsedDocument) -> ExtractionResult[ContractSchema]:
        text = document.text

        raw_fields: dict[str, Optional[str]] = {
            field_name: self._first_match(pattern, text)
            for field_name, pattern in _FIELD_PATTERNS.items()
        }

        schema = ContractSchema(
            parties=self._extract_parties(text),
            effective_date=normalize_date(raw_fields["effective_date"]),
            termination_date=normalize_date(raw_fields["termination_date"]),
            payment_terms=self._clean(raw_fields["payment_terms"]),
            renewal_terms=self._clean(raw_fields["renewal_terms"]),
            obligations=self._extract_obligations(text),
            clauses=self._extract_clauses(text),
        )

        field_confidence = self._field_confidence(schema)
        overall_confidence = sum(field_confidence.values()) / len(field_confidence)

        return ExtractionResult(
            data=schema,
            confidence=overall_confidence,
            field_confidence=field_confidence,
        )

    @staticmethod
    def _first_match(pattern: re.Pattern, text: str) -> Optional[str]:
        match = pattern.search(text)
        return match.group(1).strip() if match else None

    @staticmethod
    def _clean(raw: Optional[str]) -> Optional[str]:
        if not raw:
            return None
        return re.sub(r"\s+", " ", raw).strip() or None

    @staticmethod
    def _extract_parties(text: str) -> list[str]:
        match = _PARTIES_PATTERN.search(text)
        if not match:
            return []
        return [party.strip().rstrip(".,;") for party in match.groups() if party.strip()]

    @staticmethod
    def _extract_obligations(text: str) -> list[str]:
        return [match.strip() for match in _OBLIGATION_PATTERN.findall(text)]

    @staticmethod
    def _extract_clauses(text: str) -> list[str]:
        clauses = []
        for _, body in _CLAUSE_PATTERN.findall(text):
            cleaned = re.sub(r"\s+", " ", body).strip()
            if cleaned:
                clauses.append(cleaned)
        return clauses

    @staticmethod
    def _field_confidence(schema: ContractSchema) -> dict[str, float]:
        return {
            "parties": 1.0 if schema.parties else 0.0,
            "effective_date": 1.0 if schema.effective_date else 0.0,
            "termination_date": 1.0 if schema.termination_date else 0.0,
            "payment_terms": 1.0 if schema.payment_terms else 0.0,
            "renewal_terms": 1.0 if schema.renewal_terms else 0.0,
            "obligations": 1.0 if schema.obligations else 0.0,
            "clauses": 1.0 if schema.clauses else 0.0,
        }