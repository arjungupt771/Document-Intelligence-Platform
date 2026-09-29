from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from qdrant_client.http.exceptions import UnexpectedResponse
from sqlalchemy.orm import Session

from app.qa.factory import build_qa_service
from app.qa.models import AnswerRequest
from app.retrieval.errors import QdrantConnectionError
from app.storage.database import get_db
from app.security.authorization import require_document_access
from app.qa.errors import LLMError

router = APIRouter(prefix="/qa", tags=["qa"])


class QARequest(BaseModel):
    query: str
    document_id: str | None = None
    document_type: str | None = None
    top_k: int = 5
    score_threshold: float | None = None


class QAResponse(BaseModel):
    query: str
    answer: str
    grounded: bool
    verified: bool
    unsupported_claims: list[str]
    verification_reason: str | None
    sources: list[dict]


@router.post("/answer", response_model=QAResponse)
def answer_question(request: QARequest, db: Session = Depends(get_db)):
    if request.document_id is not None:
        require_document_access(document_id=request.document_id, db=db)

    service = build_qa_service(db)

    try:
        result = service.answer(
            AnswerRequest(query=request.query),
            top_k=request.top_k,
            document_type=request.document_type,
            document_id=request.document_id,
            score_threshold=request.score_threshold,
        )
    except ValueError as exc:
        # e.g. unclassifiable query, no extraction found for this document yet
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
            detail = "The language model  service is temporarily unavailable.",
        ) from exc
    
    except QdrantConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except UnexpectedResponse as exc:
        # Most commonly: collection doesn't exist yet -- run /documents/{id}/process
        # at least once so ensure_collection() has a chance to create it.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store returned an unexpected error. Has any document been processed yet?",
        ) from exc

    return QAResponse(
        query=result.query,
        answer=result.answer,
        grounded=result.grounded,
        verified=result.verified,
        unsupported_claims=result.unsupported_claims,
        verification_reason=result.verification_reason,
        sources=[
            {
                "document_id": source.document_id,
                "document_type": source.document_type,
                "text": source.text,
                "page_number": source.page_number,
                "score": source.score,
            }
            for source in result.sources
        ],
    )