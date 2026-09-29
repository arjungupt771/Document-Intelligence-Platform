from app.analyst.models import SEVERITY_WEIGHT, Insight


class InsightPrioritizer:
    """
    Scores insights by severity x confidence, then drops near-duplicates
    (same type + title on overlapping documents), keeping the
    highest-confidence copy of each.
    """

    def prioritize(self, insights: list[Insight]) -> list[Insight]:
        deduped = self._dedupe(insights)
        for insight in deduped:
            insight.priority_score = round(SEVERITY_WEIGHT[insight.severity] * insight.confidence, 4)
        return sorted(deduped, key=lambda i: i.priority_score, reverse=True)

    @staticmethod
    def _dedupe(insights: list[Insight]) -> list[Insight]:
        best: dict[tuple, Insight] = {}
        for insight in insights:
            key = (insight.type, insight.title, tuple(sorted(insight.document_ids)))
            existing = best.get(key)
            if existing is None or insight.confidence > existing.confidence:
                best[key] = insight
        return list(best.values())