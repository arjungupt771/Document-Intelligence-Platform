from app.routing.models import QueryType


class QueryClassifier:
    CROSS_DOCUMENT_KEYWORDS = (
        "compare", "comparison", "difference between", "differences between",
        "across", "between invoices", "between documents",
    )

    STRUCTURED_KEYWORDS = (
        "invoice number", "invoice id", "total", "amount", "vendor",
        "supplier", "status", "date", "due date",
    )

    SEMANTIC_KEYWORDS = (
        "what does", "what is the policy", "explain", "describe", "clause",
        "terms", "termination", "obligations", "payment terms",
        "according to the document",
        # generic phrasing that should still route to semantic search:
        "what is this", "what is it", "about", "summarize", "summary",
        "overview", "tell me about",
    )

    def classify(self, query: str, has_document_id: bool = False) -> QueryType:
        normalized_query = query.strip().casefold()

        if not normalized_query:
            return QueryType.UNKNOWN

        if self._contains_keyword(normalized_query, self.CROSS_DOCUMENT_KEYWORDS):
            return QueryType.CROSS_DOCUMENT

        if self._contains_keyword(normalized_query, self.STRUCTURED_KEYWORDS):
            return QueryType.STRUCTURED

        if self._contains_keyword(normalized_query, self.SEMANTIC_KEYWORDS):
            return QueryType.SEMANTIC

        # A question scoped to a specific document that matched none of the
        # above is still almost certainly asking about that document's
        # content -- fall back to semantic search rather than refusing it.
        if has_document_id:
            return QueryType.SEMANTIC

        return QueryType.UNKNOWN

    @staticmethod
    def _contains_keyword(query: str, keywords: tuple[str, ...]) -> bool:
        return any(keyword in query for keyword in keywords)