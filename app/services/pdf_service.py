# app/services/pdf_service.py
# ============================================================
# Handles PDF text extraction and splitting into chunks.
#
# RAG Step 1 & 2:
#   - Load PDF → Extract raw text (per page)
#   - Split text → Overlapping chunks for better retrieval
# ============================================================

import os
from typing import List, Tuple
from pypdf import PdfReader
from langchain.text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document

from app.utils.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


def extract_text_from_pdf(file_path: str) -> List[Tuple[str, int]]:
    """
    Extract text from each page of a PDF.

    Returns:
        List of (page_text, page_number) tuples.
        Page numbers are 1-indexed for human readability.
    """
    logger.info(f"Extracting text from PDF: {file_path}")

    reader = PdfReader(file_path)
    pages = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()

        # Skip pages with no text (e.g., image-only pages)
        if not text or not text.strip():
            logger.debug(f"  Page {page_num}: no extractable text, skipping")
            continue

        pages.append((text.strip(), page_num))
        logger.debug(f"  Page {page_num}: extracted {len(text)} characters")

    logger.info(f"Extracted text from {len(pages)} pages out of {len(reader.pages)} total")
    return pages


def chunk_documents(
    pages: List[Tuple[str, int]],
    document_id: str,
    filename: str
) -> List[Document]:
    """
    Split page texts into smaller chunks for embedding.

    We use RecursiveCharacterTextSplitter which tries to split on:
    paragraphs → sentences → words → characters
    This keeps semantically related text together as much as possible.

    Each chunk becomes a LangChain Document with metadata attached.
    That metadata is stored in ChromaDB alongside the embedding.

    Args:
        pages: Output from extract_text_from_pdf()
        document_id: Unique ID for this document
        filename: Original filename (stored as metadata)

    Returns:
        List of LangChain Document objects, ready for embedding.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        # Try to split at these separators in order
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    all_chunks: List[Document] = []
    chunk_index = 0

    for page_text, page_number in pages:
        # Split one page's text into chunks
        page_chunks = splitter.split_text(page_text)

        for chunk_text in page_chunks:
            # Skip very short chunks (e.g., page numbers, headers)
            if len(chunk_text.strip()) < 50:
                continue

            doc = Document(
                page_content=chunk_text,
                metadata={
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                }
            )
            all_chunks.append(doc)
            chunk_index += 1

    logger.info(f"Created {len(all_chunks)} chunks from {len(pages)} pages")
    return all_chunks


def process_pdf(file_path: str, document_id: str, filename: str) -> List[Document]:
    """
    Full pipeline: PDF file → List of LangChain Documents.

    This is the main entry point called by the upload route.
    """
    # Step 1: Extract text page by page
    pages = extract_text_from_pdf(file_path)

    if not pages:
        raise ValueError(
            f"Could not extract any text from '{filename}'. "
            "The PDF may be scanned/image-based and requires OCR."
        )

    # Step 2: Split into overlapping chunks
    chunks = chunk_documents(pages, document_id, filename)

    if not chunks:
        raise ValueError(f"No valid text chunks created from '{filename}'.")

    return chunks
