# app/routes/upload.py
# ============================================================
# Route: POST /upload
# Handles PDF uploads, text extraction, chunking, and embedding
# ============================================================

import os
import time
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.models.schemas import UploadResponse
from app.services.pdf_service import process_pdf
from app.services.vector_store import VectorStoreService, get_vector_store_service
from app.utils.auth import get_current_user
from app.utils.config import get_settings
from app.utils.logger import get_logger
from app.utils.helpers import generate_document_id, get_file_size_mb, ensure_directory, is_valid_pdf

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload a PDF document",
    description="Upload a PDF file to extract, chunk, embed, and store in ChromaDB for future Q&A."
)
async def upload_pdf(
    file: UploadFile = File(..., description="A PDF file to upload"),
    current_user: dict = Depends(get_current_user),
    vector_store: VectorStoreService = Depends(get_vector_store_service),
):
    """
    Full upload pipeline:
    1. Validate file (is it a PDF? is it under size limit?)
    2. Save to uploads/ directory
    3. Extract text from PDF pages
    4. Split into overlapping chunks
    5. Generate embeddings and store in ChromaDB
    6. Return success response with chunk count
    """
    start_time = time.time()
    logger.info(f"Upload request received: {file.filename}")

    # --- Validation: File type ---
    if not is_valid_pdf(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only PDF files are accepted. Got: {file.filename}"
        )

    # --- Create upload directory if needed ---
    ensure_directory(settings.upload_dir)

    # --- Save uploaded file to disk ---
    # We save to disk first, then read it with pypdf
    document_id = generate_document_id(file.filename)
    save_path = os.path.join(settings.upload_dir, f"{document_id}.pdf")

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # --- Validation: File size ---
    file_size_mb = get_file_size_mb(save_path)
    if file_size_mb > settings.max_file_size_mb:
        os.remove(save_path)  # Clean up
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {file_size_mb}MB. Maximum allowed: {settings.max_file_size_mb}MB"
        )

    logger.info(f"Saved '{file.filename}' as '{document_id}.pdf' ({file_size_mb}MB)")

    # --- Process PDF: Extract + Chunk ---
    try:
        chunks = process_pdf(
            file_path=save_path,
            document_id=document_id,
            filename=file.filename,
        )
    except ValueError as e:
        # PDF had no extractable text (e.g., scanned image)
        os.remove(save_path)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        os.remove(save_path)
        logger.error(f"PDF processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

    # --- Embed + Store in ChromaDB ---
    try:
        total_chunks = vector_store.add_documents(chunks, document_id)
    except Exception as e:
        os.remove(save_path)
        logger.error(f"Embedding/storage failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store embeddings: {str(e)}"
        )

    elapsed = round(time.time() - start_time, 2)
    logger.info(
        f"Upload complete: '{file.filename}' → {total_chunks} chunks in {elapsed}s"
    )

    return UploadResponse(
        message=f"Successfully processed '{file.filename}'",
        document_id=document_id,
        filename=file.filename,
        total_chunks=total_chunks,
        processing_time_seconds=elapsed,
    )
