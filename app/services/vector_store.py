# app/services/vector_store.py
# ============================================================
# Manages the ChromaDB vector store.
#
# RAG Steps 3, 4, 5, 7:
#   - Generate embeddings (OpenAI)
#   - Store embeddings in ChromaDB (with persistence)
#   - Retrieve relevant chunks via similarity search
# ============================================================

import os
from typing import List, Optional, Dict, Any
from datetime import datetime

import chromadb
from langchain_chroma import Chroma
# from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain.schema import Document

from app.utils.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


# --- Embedding Model ---
# This is initialized once and reused across requests
# def get_embeddings() -> OpenAIEmbeddings:
#     """
#     Create the OpenAI embeddings model.
#     text-embedding-ada-002 is cheap, fast, and works well for RAG.
#     """
#     return OpenAIEmbeddings(
#         model=settings.embedding_model,
#         openai_api_key=settings.openai_api_key,
#     )

def get_embeddings():
    return OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url,
    )


# --- ChromaDB Client ---
def get_chroma_client() -> chromadb.PersistentClient:
    """
    Create a persistent ChromaDB client.
    Data is saved to disk at settings.chroma_db_path,
    so it survives server restarts.
    """
    os.makedirs(settings.chroma_db_path, exist_ok=True)
    return chromadb.PersistentClient(path=settings.chroma_db_path)


# --- Main Vector Store Class ---
class VectorStoreService:
    """
    Wraps ChromaDB + OpenAI embeddings into a simple interface.

    What it does:
    - add_documents()  → embed chunks and save to ChromaDB
    - similarity_search() → find most relevant chunks for a query
    - delete_document() → remove all chunks for a document
    - list_documents()  → list all uploaded documents
    """

    def __init__(self):
        self.embeddings = get_embeddings()
        self.chroma_client = get_chroma_client()
        # All documents share one ChromaDB collection
        self.collection_name = "pdf_documents"
        logger.info(f"VectorStoreService initialized. DB path: {settings.chroma_db_path}")

    def _get_vector_store(self) -> Chroma:
        """
        Get (or create) the LangChain Chroma wrapper.
        We re-create this object on each call to ensure a fresh connection.
        """
        return Chroma(
            client=self.chroma_client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )

    # def add_documents(self, chunks: List[Document], document_id: str) -> int:
    def add_documents(self, chunks: List[Document], document_id: str, owner_id: str) -> int:
        """
        Embed chunks and store them in ChromaDB.

        Each chunk gets:
          - A vector embedding (1536-dim for ada-002)
          - The original text content
          - Metadata (document_id, filename, page_number, chunk_index)

        Args:
            chunks: List of LangChain Documents from pdf_service
            document_id: Used to generate unique IDs per chunk

        Returns:
            Number of chunks successfully stored
        """
        for chunk in chunks:
            chunk.metadata["owner_id"] = owner_id
        logger.info(f"Embedding and storing {len(chunks)} chunks for document '{document_id}'")

        vector_store = self._get_vector_store()

        # Generate unique IDs for each chunk
        # Format: documentId_chunkIndex (e.g., report_a1b2_0, report_a1b2_1)
        ids = [
            f"{document_id}_{chunk.metadata['chunk_index']}"
            for chunk in chunks
        ]

        # Add uploaded_at timestamp to all chunks
        timestamp = datetime.now().isoformat()
        for chunk in chunks:
            chunk.metadata["uploaded_at"] = timestamp

        # This call generates embeddings via OpenAI API and stores in ChromaDB
        vector_store.add_documents(documents=chunks, ids=ids)

        logger.info(f"Successfully stored {len(chunks)} chunks")
        return len(chunks)

    def similarity_search(
        self, query: str, top_k: int = 3, document_id: Optional[str] = None, owner_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find the most semantically similar chunks for a query.

        This is the core of RAG retrieval:
        1. Embed the query using the same model
        2. Find chunks whose embeddings are closest (cosine similarity)
        3. Return chunks + their similarity scores

        Args:
            query: The user's question
            top_k: Number of results to return
            document_id: If set, only search within this document

        Returns:
            List of dicts with 'content', 'metadata', 'similarity_score'
        """
        # Build metadata filter for ChromaDB
        where_filter = {}
        if owner_id:
            where_filter["owner_id"] = {"$eq": owner_id}
        if document_id:
            where_filter["document_id"] = {"$eq": document_id}

        results = vector_store.similarity_search_with_relevance_scores(
            query=query, k=top_k, filter=where_filter if where_filter else None
        )
        logger.info(f"Searching for: '{query[:80]}...' | top_k={top_k}")

        vector_store = self._get_vector_store()

        # Build the filter if searching a specific document
        where_filter = None
        if document_id:
            where_filter = {"document_id": {"$eq": document_id}}
            logger.debug(f"Filtering by document_id: {document_id}")

        # similarity_search_with_relevance_scores returns (Document, score) tuples
        # Scores are cosine similarity: 1.0 = perfect match, 0.0 = unrelated
        results = vector_store.similarity_search_with_relevance_scores(
            query=query,
            k=top_k,
            filter=where_filter,
        )

        # Format results for our API response
        formatted = []
        for doc, score in results:
            formatted.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": round(float(score), 4),
            })

        logger.info(f"Found {len(formatted)} relevant chunks")
        return formatted

    def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks belonging to a specific document.

        ChromaDB stores each chunk with the document_id in its metadata,
        so we can filter and delete by it.

        Returns:
            Number of chunks deleted
        """
        logger.info(f"Deleting all chunks for document: {document_id}")

        collection = self.chroma_client.get_collection(self.collection_name)

        # First, find all chunk IDs for this document
        results = collection.get(
            where={"document_id": {"$eq": document_id}},
            include=[]  # We only need IDs, not content
        )

        chunk_ids = results.get("ids", [])

        if not chunk_ids:
            logger.warning(f"No chunks found for document_id: {document_id}")
            return 0

        # Delete all found chunks
        collection.delete(ids=chunk_ids)
        logger.info(f"Deleted {len(chunk_ids)} chunks for document: {document_id}")
        return len(chunk_ids)

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all unique documents currently in the vector store.

        We query all metadata and deduplicate by document_id.
        This gives us a summary of what's been uploaded.

        Returns:
            List of document info dicts
        """
        logger.info("Listing all documents in vector store")

        try:
            collection = self.chroma_client.get_collection(self.collection_name)
        except Exception:
            # Collection doesn't exist yet (no documents uploaded)
            return []

        # Get all metadata (no need for embeddings or content)
        results = collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", [])

        # Deduplicate: keep one entry per document_id
        seen = {}
        for meta in metadatas:
            doc_id = meta.get("document_id")
            if doc_id and doc_id not in seen:
                seen[doc_id] = {
                    "document_id": doc_id,
                    "filename": meta.get("filename", "unknown"),
                    "uploaded_at": meta.get("uploaded_at", ""),
                }

        # Count chunks per document
        chunk_counts: Dict[str, int] = {}
        for meta in metadatas:
            doc_id = meta.get("document_id")
            if doc_id:
                chunk_counts[doc_id] = chunk_counts.get(doc_id, 0) + 1

        # Add chunk count to each document entry
        documents = []
        for doc_id, info in seen.items():
            info["total_chunks"] = chunk_counts.get(doc_id, 0)
            documents.append(info)

        logger.info(f"Found {len(documents)} unique documents")
        return documents

    def get_total_documents(self) -> int:
        """Quick count of unique documents. Used for health check."""
        return len(self.list_documents())

    def collection_exists(self) -> bool:
        """Check if the ChromaDB collection has been created yet."""
        try:
            self.chroma_client.get_collection(self.collection_name)
            return True
        except Exception:
            return False


# --- Singleton ---
# We create one shared instance to reuse the same DB connection
_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    """
    Returns a singleton VectorStoreService instance.
    FastAPI routes use this via dependency injection.
    """
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service
