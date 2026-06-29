# app/routes/documents.py
# ============================================================
# Routes: GET /documents, DELETE /documents/{document_id}
# List all uploaded documents and delete specific ones
# ============================================================

import os
from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import ListDocumentsResponse, DocumentInfo, DeleteResponse
from app.services.vector_store import VectorStoreService, get_vector_store_service
from app.utils.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/documents",
    response_model=ListDocumentsResponse,
    summary="List all uploaded documents",
    description="Returns a list of all PDFs that have been uploaded and processed."
)
async def list_documents(
    vector_store: VectorStoreService = Depends(get_vector_store_service),
):
    """
    Retrieve metadata for all documents currently stored in ChromaDB.
    Useful for the frontend to display available documents.
    """
    logger.info("Listing all documents")

    try:
        docs = vector_store.list_documents()
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Could not retrieve documents: {str(e)}")

    # Convert to Pydantic schema
    document_list = [
        DocumentInfo(
            document_id=d["document_id"],
            filename=d["filename"],
            total_chunks=d["total_chunks"],
            uploaded_at=d.get("uploaded_at", ""),
        )
        for d in docs
    ]

    return ListDocumentsResponse(
        total_documents=len(document_list),
        documents=document_list,
    )


@router.delete(
    "/documents/{document_id}",
    response_model=DeleteResponse,
    summary="Delete a document",
    description="Remove a document and all its embeddings from ChromaDB. Also deletes the uploaded PDF file."
)
async def delete_document(
    document_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store_service),
):
    """
    Delete a document from the system:
    1. Check the document exists
    2. Delete all its chunks from ChromaDB
    3. Delete the saved PDF file from uploads/
    """
    logger.info(f"Delete request for document: {document_id}")

    # --- Check document exists ---
    all_docs = vector_store.list_documents()
    doc_ids = [d["document_id"] for d in all_docs]

    if document_id not in doc_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found."
        )

    # --- Delete from ChromaDB ---
    try:
        chunks_deleted = vector_store.delete_document(document_id)
    except Exception as e:
        logger.error(f"Failed to delete from ChromaDB: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document from vector store: {str(e)}"
        )

    # --- Delete the PDF file from uploads/ (if it exists) ---
    pdf_path = os.path.join(settings.upload_dir, f"{document_id}.pdf")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        logger.info(f"Deleted PDF file: {pdf_path}")
    else:
        logger.warning(f"PDF file not found on disk: {pdf_path}")

    logger.info(f"Document '{document_id}' fully deleted ({chunks_deleted} chunks)")

    return DeleteResponse(
        message=f"Document '{document_id}' successfully deleted.",
        document_id=document_id,
        chunks_deleted=chunks_deleted,
    )
