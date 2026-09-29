from app.qa.models import AnswerRequest


class StructuredFieldResolver:
    FIELD_KEYWORDS = {
        "invoice_number": (
            "invoice number",
            "invoice id",
            "invoice no",
        ),
        "total_amount": (
            "total",
            "total amount",
            "invoice total",
            "amount",
        ),
        "vendor": (
            "vendor",
            "supplier",
        ),
        "due_date": (
            "due date",
        ),
        "invoice_date": (
            "invoice date",
            "date of invoice",
        ),
    }

    def resolve(self, request: AnswerRequest) -> str | None:
        query = request.query.lower()

        for field, keywords in self.FIELD_KEYWORDS.items():
            if any(keyword in query for keyword in keywords):
                return field

        return None