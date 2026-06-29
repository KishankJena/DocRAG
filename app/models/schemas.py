# app/models/schemas.py
# ============================================================
# Pydantic schemas for request/response validation
# These define the shape of data going in and out of our API
# ============================================================

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# --- Upload Schemas ---

class UploadResponse(BaseModel):
    """Returned after a PDF is successfully uploaded and processed."""
    message: str
    document_id: str           # Unique ID for this document in ChromaDB
    filename: str
    total_chunks: int          # How many text chunks were created
    processing_time_seconds: float


class DocumentInfo(BaseModel):
    """Info about a single uploaded document."""
    document_id: str
    filename: str
    total_chunks: int
    uploaded_at: str           # ISO datetime string


class ListDocumentsResponse(BaseModel):
    """Returned when listing all uploaded documents."""
    total_documents: int
    documents: List[DocumentInfo]


# --- Chat / QA Schemas ---

class QuestionRequest(BaseModel):
    """The user's question + which document(s) to search."""
    question: str = Field(..., min_length=3, description="The question to ask about the document")
    document_id: Optional[str] = Field(
        default=None,
        description="Optional: Limit search to a specific document. If None, searches all documents."
    )
    top_k: Optional[int] = Field(
        default=4,
        ge=1,
        le=10,
        description="How many relevant chunks to retrieve (1-10)"
    )


class SourceChunk(BaseModel):
    """A single relevant text chunk returned alongside the answer."""
    content: str               # The actual text of the chunk
    document_id: str
    filename: str
    page_number: Optional[int] = None
    similarity_score: float    # Higher = more relevant (0 to 1)
    chunk_index: int           # Position of this chunk in the original document


class QuestionResponse(BaseModel):
    """The full answer + supporting source chunks."""
    question: str
    answer: str
    source_chunks: List[SourceChunk]
    model_used: str
    total_chunks_searched: int
    response_time_seconds: float


# --- Delete Schemas ---

class DeleteResponse(BaseModel):
    """Returned after deleting a document."""
    message: str
    document_id: str
    chunks_deleted: int


# --- Health Check ---

class HealthResponse(BaseModel):
    """Basic health check response."""
    status: str
    version: str
    total_documents: int
    chroma_db_connected: bool
