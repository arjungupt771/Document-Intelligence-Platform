from datetime import date, datetime
from typing import Any
from datetime import date, datetime

class ValueComparator:


    def _parse_date(self, value: str) -> date | None:
        formats = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        )
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue

        return None
    def compare(
        self,
        expected: Any,
        predicted: Any,
    ) -> bool:
        if expected is None or predicted is None:
            return expected == predicted

        if isinstance(expected, (int, float)) and isinstance(
            predicted, (int, float)
        ):
            return self._compare_numbers(
                expected,
                predicted,
            )

        if isinstance(expected, str) and isinstance(
            predicted, str
        ):
            return self._compare_strings(
                expected,
                predicted,
            )

        if isinstance(expected, (date, datetime)) and isinstance(
            predicted, (date, datetime)
        ):
            return expected == predicted

        if isinstance(expected, list) and isinstance(
            predicted, list
        ):
            return self._compare_lists(
                expected,
                predicted,
            )

        if isinstance(expected, dict) and isinstance(
            predicted, dict
        ):
            return self._compare_dicts(
                expected,
                predicted,
            )

        return expected == predicted

    def _compare_numbers(
        self,
        expected: int | float,
        predicted: int | float,
    ) -> bool:
        tolerance = max(
            1e-6,
            abs(expected) * 0.001,
        )

        return abs(expected - predicted) <= tolerance

    def _compare_strings(
            self,
            expected: str,
            predicted: str,
            ) -> bool:
        expected_clean = expected.strip()
        predicted_clean = predicted.strip()

        if expected_clean.casefold() == predicted_clean.casefold():
            return True

        expected_date = self._parse_date(expected_clean)
        predicted_date = self._parse_date(predicted_clean)

        if expected_date is not None and predicted_date is not None:
            return expected_date == predicted_date

        return False

    def _compare_lists(
        self,
        expected: list[Any],
        predicted: list[Any],
    ) -> bool:
        if len(expected) != len(predicted):
            return False

        return all(
            self.compare(expected_value, predicted_value)
            for expected_value, predicted_value
            in zip(expected, predicted)
        )

    def _compare_dicts(
        self,
        expected: dict[str, Any],
        predicted: dict[str, Any],
    ) -> bool:
        if set(expected) != set(predicted):
            return False

        return all(
            self.compare(
                expected[field],
                predicted[field],
            )
            for field in expected
        )