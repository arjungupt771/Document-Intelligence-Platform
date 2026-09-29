class CrossDocumentGroundingValidator:
    def validate(self, context) -> bool:
        return len(context.document_ids) >= 2