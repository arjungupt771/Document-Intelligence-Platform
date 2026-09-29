import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d %B %Y",
    "%d %b %Y",
)

_AMOUNT_PATTERN = re.compile(r"[-+]?[\d,]+\.?\d*")

_CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
}

_KNOWN_CURRENCY_CODES = {"USD", "EUR", "GBP", "JPY", "INR", "CAD", "AUD"}


def normalize_date(raw: Optional[str]) -> Optional[date]:
    """Best-effort parse of a free-text date into a `date`, or None."""
    if not raw:
        return None

    cleaned = raw.strip().rstrip(".,")
    for date_format in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, date_format).date()
        except ValueError:
            continue
    return None


def normalize_amount(raw: Optional[str]) -> Optional[Decimal]:
    """Best-effort parse of a free-text amount (e.g. '$1,234.50') into a Decimal."""
    if not raw:
        return None

    match = _AMOUNT_PATTERN.search(raw)
    if not match:
        return None

    cleaned = match.group(0).replace(",", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def normalize_currency(text: Optional[str]) -> Optional[str]:
    """Best-effort detection of an ISO currency code from a symbol or code in the text."""
    if not text:
        return None

    for code in _KNOWN_CURRENCY_CODES:
        if re.search(rf"\b{code}\b", text):
            return code

    for symbol, code in _CURRENCY_SYMBOLS.items():
        if symbol in text:
            return code

    return None