from app.routing.classifier import QueryClassifier
from app.routing.models import QueryRequest, QueryRoute, QueryType


class QueryRouter:
    def __init__(self, classifier: QueryClassifier | None = None):
        self.classifier = classifier or QueryClassifier()

    def route(self, request: QueryRequest, has_document_id: bool = False) -> QueryRoute:
        query_type = self.classifier.classify(request.query, has_document_id=has_document_id)
        return QueryRoute(query=request.query, query_type=query_type)

    @staticmethod
    def requires_clarification(route: QueryRoute) -> bool:
        return route.query_type == QueryType.UNKNOWN