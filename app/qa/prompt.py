from app.qa.context import GroundingContextLike


class GroundedPromptBuilder:
    SYSTEM_INSTRUCTIONS = """You are a document question-answering assistant.

Answer the user's question using only the provided evidence.

Rules:
1. Do not invent or infer document facts that are not present in the evidence.
2. If the evidence does not contain enough information to answer the question, say so.
3. Treat the evidence as the source of truth for document-specific information.
4. Keep the answer concise and directly address the user's question.
"""

    def build(self, context: GroundingContextLike) -> str:
        evidence = (
            context.as_text()
            if not context.is_empty
            else " No evidence was retrieved for this question."
        )

        return (
            f"{self.SYSTEM_INSTRUCTIONS}\n"
            f"User question:\n"
            f"{context.query}\n\n"
            f"Evidence:\n"
            f"{evidence}"
        )