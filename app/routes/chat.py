# app/routes/chat.py
# ============================================================
# Route: POST /chat
# Handles user questions and returns LLM answers with sources
# ============================================================

from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import QuestionRequest, QuestionResponse
from app.services.qa_service import QAService, get_qa_service
from app.services.vector_store import VectorStoreService, get_vector_store_service
from app.utils.logger import get_logger
from app.utils.auth import get_current_user

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/chat",
    response_model=QuestionResponse,
    summary="Ask a question about uploaded PDFs",
    description=(
        "Send a question and get an AI-generated answer based on your uploaded documents. "
        "Returns the answer along with the source chunks and similarity scores."
    )
)
async def ask_question(
    request: QuestionRequest,
    qa_service: QAService = Depends(get_qa_service),
    vector_store: VectorStoreService = Depends(get_vector_store_service),
    current_user: dict = Depends(get_current_user),
):
    """
    RAG Query Pipeline:
    1. Receive question from user
    2. Check that at least one document exists
    3. Retrieve relevant chunks via semantic search
    4. Generate answer using LLM with chunks as context
    5. Return answer + sources with similarity scores
    """
    logger.info(
        f"Chat request: question='{request.question[:60]}...', "
        f"document_id={request.document_id}, top_k={request.top_k}"
    )

    # --- Check if there are any documents to search ---
    if not vector_store.collection_exists():
        raise HTTPException(
            status_code=404,
            detail="No documents have been uploaded yet. Please upload a PDF first."
        )

    # --- Validate document_id if provided ---
    if request.document_id:
        all_docs = vector_store.list_documents()
        doc_ids = [d["document_id"] for d in all_docs]
        if request.document_id not in doc_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{request.document_id}' not found. "
                       f"Available documents: {doc_ids}"
            )

    # --- Run the RAG pipeline ---
    try:
        response = qa_service.answer_question(
            question=request.question,
            document_id=request.document_id,
            top_k=request.top_k or 4,
        )
    except Exception as e:
        logger.error(f"QA pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(e)}"
        )

    return response
