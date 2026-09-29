import re

from collections import Counter
from decimal import Decimal

from app.qa.context import GroundingContextLike
from app.qa.verifier import EvidenceVerifier
from app.qa.verification import VerificationResult


class DeterministicEvidenceVerifier(EvidenceVerifier):

    SEMANTIC_EQUIVALENTS = {
        "invoice total": "total amount",
        "total amount of the invoice": "total amount",
        "supplier": "vendor",
        "payment due date": "due date",
        "invoice id": "invoice number",
    }

    VERIFIER_STOP_WORDS = {
        "a",
        "an",
        "the",
        "of",
        "to",
        "and",
        "or",
        "is",
        "are",
        "was",
        "were",
        "this",
        "that",
        "which",
        "for",
        "on",
        "in",
    }

    NUMBER_WORDS = {
        "zero": "0",
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
    }

    @classmethod
    def _normalize_claim_tokens(cls, text: str) -> set[str]:
        tokens = cls._content_tokens(text)
        normalized = set()

        for token in tokens:
            token = cls.NUMBER_WORDS.get(token, token)

            if token.endswith("s") and len(token) > 3:
                token = token[:-1]

            normalized.add(token)

        return normalized

    @staticmethod
    def _normalize_numbers(numbers: list[str]) -> list[str]:
        normalized = []

        for number in numbers:
            value = Decimal(number)

            if value == value.to_integral_value():
                normalized.append(
                    str(value.quantize(Decimal("1")))
                )
            else:
                normalized.append(
                    format(value.normalize(), "f")
                )

        return normalized

    @classmethod
    def _content_tokens(cls, text: str) -> set[str]:
        return {
            token
            for token in text.split()
            if token not in cls.VERIFIER_STOP_WORDS
        }

    @staticmethod
    def _has_condition(text: str) -> bool:
        condition_markers = {
            "if",
            "unless",
            "when",
            "provided",
            "provided that",
            "only if",
        }

        return any(
            marker in text
            for marker in condition_markers
        )

    @staticmethod
    def _extract_temporal_qualifier(
        text: str,
    ) -> str | None:
        temporal_patterns = {
            "before": (
                r"\bbefore\b"
                r"|\bprior to\b"
                r"|\bearlier than\b"
            ),
            "after": (
                r"\bafter\b"
                r"|\blater than\b"
            ),
            "on": r"\bon\b",
        }

        for qualifier, pattern in temporal_patterns.items():
            if re.search(pattern, text):
                return qualifier

        return None

    @staticmethod
    def _extract_temporal_date(
        text: str,
    ) -> tuple[int, int, int] | None:
        match = re.search(
            r"\b(\d{1,2})\s+"
            r"(January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+"
            r"(\d{4})\b",
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        day = int(match.group(1))
        month_name = match.group(2).lower()
        year = int(match.group(3))

        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        return day, months[month_name], year

    @classmethod
    def _has_conflicting_temporal_qualifier(
        cls,
        claim: str,
        evidence: str,
    ) -> bool:
        claim_qualifier = cls._extract_temporal_qualifier(
            claim
        )

        evidence_qualifier = cls._extract_temporal_qualifier(
            evidence
        )

        if (
            claim_qualifier is not None
            and evidence_qualifier is not None
            and claim_qualifier != evidence_qualifier
        ):
            return True

        return False

    @classmethod
    def _has_conflicting_temporal_value(
        cls,
        claim: str,
        evidence: str,
    ) -> bool:
        claim_date = cls._extract_temporal_date(claim)
        evidence_date = cls._extract_temporal_date(evidence)

        if (
            claim_date is not None
            and evidence_date is not None
            and claim_date != evidence_date
        ):
            return True

        return False

    @staticmethod
    def _has_negation(text: str) -> bool:
        tokens = text.split()

        negation_terms = {
            "not",
            "no",
            "never",
            "neither",
            "without",
        }

        return any(
            token in negation_terms
            for token in tokens
        )

    @staticmethod
    def _remove_negation_terms(text: str) -> str:
        negation_terms = {
            "not",
            "no",
            "never",
            "neither",
            "without",
        }

        return " ".join(
            token
            for token in text.split()
            if token not in negation_terms
        )

    @staticmethod
    def _extract_numbers(text: str) -> list[str]:
        return re.findall(
            r"\d+(?:\.\d+)?",
            text,
        )

    def verify(
        self,
        answer: str,
        context: GroundingContextLike,
    ) -> VerificationResult:

        if not answer.strip():
            return VerificationResult(
                verified=False,
                reason="The generated answer is empty.",
            )

        if context.is_empty:
            return VerificationResult(
                verified=False,
                reason="No evidence is available for verification.",
            )

        evidence = self._normalize(
            context.as_text()
        )

        claims = self._extract_claims(answer)

        unsupported_claims = []

        for claim in claims:
            normalized_claim = self._normalize(claim)

            if not normalized_claim:
                continue

            if not self._claim_supported(
                normalized_claim,
                evidence,
            ):
                unsupported_claims.append(claim)

        if unsupported_claims:
            return VerificationResult(
                verified=False,
                unsupported_claims=unsupported_claims,
                reason=(
                    "The answer contains claims that are not directly "
                    "supported by the retrieved evidence."
                ),
            )

        return VerificationResult(
            verified=True,
            reason=(
                "All answer claims are directly supported by "
                "the retrieved evidence."
            ),
        )

    @staticmethod
    def _extract_claims(answer: str) -> list[str]:
        sentences = [
            sentence.strip()
            for sentence in re.split(
                r"(?<!\d)[.!?]+|[.!?]+(?!\d)",
                answer,
            )
            if sentence.strip()
        ]

        claims = []

        for sentence in sentences:
            parts = re.split(
                r"\s+and\s+",
                sentence,
                maxsplit=1,
            )

            if len(parts) == 2:
                left, right = parts

                if left.strip() and right.strip():
                    claims.extend(
                        [
                            left.strip(),
                            right.strip(),
                        ]
                    )
                    continue

            claims.append(sentence)

        return claims

    @classmethod
    def _normalize(cls, text: str) -> str:
        text = text.lower()

        text = re.sub(
            r"(?<=\d),(?=\d)",
            "",
            text,
        )

        text = re.sub(
            r"[^a-z0-9\s.]",
            " ",
            text,
        )

        text = re.sub(
            r"\.(?!\d)|(?<!\d)\.",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @classmethod
    def _normalize_phrases(cls, text: str) -> str:
        normalized = text

        for source, target in cls.SEMANTIC_EQUIVALENTS.items():
            normalized = normalized.replace(
                source,
                target,
            )

        return normalized

    @staticmethod
    def _split_evidence_sentences(
        evidence: str,
    ) -> list[str]:
        return [
            sentence.strip()
            for sentence in re.split(
                r"(?<!\d)[.!?]+|[.!?]+(?!\d)",
                evidence,
            )
            if sentence.strip()
        ]

    @classmethod
    def _claim_has_evidence_anchors(
        cls,
        claim: str,
        evidence: str,
    ) -> bool:
        claim_tokens = cls._normalize_claim_tokens(
            claim
        )

        evidence_tokens = cls._normalize_claim_tokens(
            evidence
        )

        ignored_explanatory_tokens = {
            "applied",
            "corresponds",
            "given",
            "shows",
            "indicates",
            "means",
            "represents",
        }

        important_tokens = {
            token
            for token in claim_tokens
            if token not in ignored_explanatory_tokens
        }

        matched_tokens = (
            important_tokens.intersection(
                evidence_tokens
            )
        )

        return len(matched_tokens) >= 3

    @classmethod
    def _claim_supported(
        cls,
        claim: str,
        evidence: str,
    ) -> bool:

        claim_tokens = claim.split()

        if not claim_tokens:
            return False

        claim_numbers = cls._extract_numbers(claim)

        normalized_claim_numbers = cls._normalize_numbers(
            claim_numbers
        )

        claim_negated = cls._has_negation(claim)

        evidence_sentences = (
            cls._split_evidence_sentences(evidence)
        )

        claim_without_negation = (
            cls._remove_negation_terms(claim)
        )

        claim_without_negation_tokens = set(
            claim_without_negation.split()
        )

        # ---------------------------------------------------------
        # 1. Direct sentence-level evidence matching
        # ---------------------------------------------------------
        for evidence_sentence in evidence_sentences:

            # A conditional evidence statement cannot support an
            # unconditional claim.
            if (
                cls._has_condition(evidence_sentence)
                and not cls._has_condition(claim)
            ):
                continue

            # Temporal conflicts must be checked against the same
            # evidence sentence.
            if cls._has_conflicting_temporal_qualifier(
                claim,
                evidence_sentence,
            ):
                continue

            if cls._has_conflicting_temporal_value(
                claim,
                evidence_sentence,
            ):
                continue

            evidence_tokens = evidence_sentence.split()

            evidence_negated = cls._has_negation(
                evidence_sentence
            )

            normalized_evidence_numbers = (
                cls._normalize_numbers(
                    cls._extract_numbers(
                        evidence_sentence
                    )
                )
            )

            if not Counter(
                normalized_claim_numbers
            ) <= Counter(
                normalized_evidence_numbers
            ):
                continue

            if claim_negated != evidence_negated:
                continue

            if claim in evidence_sentence:
                return True

            if set(claim_tokens).issubset(
                set(evidence_tokens)
            ):
                return True

            semantic_claim = cls._normalize_phrases(
                claim
            )

            semantic_evidence = (
                cls._normalize_phrases(
                    evidence_sentence
                )
            )

            if semantic_claim in semantic_evidence:
                return True

            semantic_claim_tokens = semantic_claim.split()

            semantic_evidence_tokens = (
                semantic_evidence.split()
            )

            if set(semantic_claim_tokens).issubset(
                set(semantic_evidence_tokens)
            ):
                return True

        # ---------------------------------------------------------
        # 2. Explicit negation conflict detection
        # ---------------------------------------------------------
        for evidence_sentence in evidence_sentences:

            evidence_negated = cls._has_negation(
                evidence_sentence
            )

            if claim_negated == evidence_negated:
                continue

            evidence_without_negation = (
                cls._remove_negation_terms(
                    evidence_sentence
                )
            )

            evidence_without_negation_tokens = set(
                evidence_without_negation.split()
            )

            if (
                claim_without_negation_tokens
                and claim_without_negation_tokens.issubset(
                    evidence_without_negation_tokens
                )
                and cls._extract_numbers(claim)
                == cls._extract_numbers(evidence_sentence)
            ):
                return False

        # ---------------------------------------------------------
        # 3. Build SAFE combined evidence
        #
        # Only evidence sentences that do not conflict with the
        # claim are allowed into the combined-evidence fallback.
        #
        # This prevents an unrelated "before/after", date, or
        # condition statement from contaminating the verification.
        # ---------------------------------------------------------
        safe_evidence_sentences = []

        for evidence_sentence in evidence_sentences:

            # Do not allow a conditional sentence to support an
            # unconditional claim.
            if (
                cls._has_condition(evidence_sentence)
                and not cls._has_condition(claim)
            ):
                continue

            # Do not include temporally conflicting evidence.
            if cls._has_conflicting_temporal_qualifier(
                claim,
                evidence_sentence,
            ):
                continue

            if cls._has_conflicting_temporal_value(
                claim,
                evidence_sentence,
            ):
                continue

            safe_evidence_sentences.append(
                evidence_sentence
            )

        safe_evidence = " ".join(
            safe_evidence_sentences
        )

        # ---------------------------------------------------------
        # 4. Combined-evidence fallback
        # ---------------------------------------------------------
        if not claim_negated and safe_evidence:

            if claim in safe_evidence:
                return True

            normalized_safe_evidence_numbers = (
                cls._normalize_numbers(
                    cls._extract_numbers(
                        safe_evidence
                    )
                )
            )

            if Counter(
                normalized_claim_numbers
            ) <= Counter(
                normalized_safe_evidence_numbers
            ):
                if cls._claim_has_evidence_anchors(
                    claim,
                    safe_evidence,
                ):
                    return True

            semantic_claim = cls._normalize_phrases(
                claim
            )

            semantic_safe_evidence = (
                cls._normalize_phrases(
                    safe_evidence
                )
            )

            if semantic_claim in semantic_safe_evidence:
                return True

            semantic_claim_tokens = semantic_claim.split()

            semantic_safe_evidence_tokens = (
                semantic_safe_evidence.split()
            )

            if set(semantic_claim_tokens).issubset(
                set(semantic_safe_evidence_tokens)
            ):
                return True

        return False