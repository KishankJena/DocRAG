# tests/test_api.py
# ============================================================
# Integration tests for FastAPI endpoints
# Uses httpx TestClient to simulate HTTP requests
#
# Run with: pytest tests/ -v
# Note: These tests mock ChromaDB and OpenAI — no real API calls
# ============================================================

import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# --- Fixtures ---

@pytest.fixture
def mock_vector_store():
    """A mock VectorStoreService that doesn't touch ChromaDB."""
    mock = MagicMock()
    mock.add_documents.return_value = 10
    mock.list_documents.return_value = [
        {
            "document_id": "test_doc_abc123",
            "filename": "test.pdf",
            "total_chunks": 10,
            "uploaded_at": "2024-01-01T00:00:00",
        }
    ]
    mock.get_total_documents.return_value = 1
    mock.collection_exists.return_value = True
    mock.delete_document.return_value = 10
    mock.similarity_search.return_value = [
        {
            "content": "This is a relevant chunk of text from the document.",
            "metadata": {
                "document_id": "test_doc_abc123",
                "filename": "test.pdf",
                "page_number": 1,
                "chunk_index": 0,
            },
            "similarity_score": 0.87,
        }
    ]
    return mock


@pytest.fixture
def mock_qa_service():
    """A mock QAService that returns a canned answer."""
    from app.models.schemas import QuestionResponse, SourceChunk
    mock = MagicMock()
    mock.answer_question.return_value = QuestionResponse(
        question="What is RAG?",
        answer="RAG stands for Retrieval Augmented Generation.",
        source_chunks=[
            SourceChunk(
                content="RAG is a technique that combines retrieval with generation.",
                document_id="test_doc_abc123",
                filename="test.pdf",
                page_number=1,
                similarity_score=0.87,
                chunk_index=0,
            )
        ],
        model_used="gpt-3.5-turbo",
        total_chunks_searched=1,
        response_time_seconds=0.5,
    )
    return mock


@pytest.fixture
def client(mock_vector_store, mock_qa_service):
    """Create a test client with mocked services."""
    from app.main import app
    from app.services.vector_store import get_vector_store_service
    from app.services.qa_service import get_qa_service

    app.dependency_overrides[get_vector_store_service] = lambda: mock_vector_store
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# --- Health Check Tests ---

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        res = client.get("/api/v1/health")
        assert res.status_code == 200

    def test_health_has_required_fields(self, client):
        res = client.get("/api/v1/health")
        data = res.json()
        assert "status" in data
        assert "version" in data
        assert "total_documents" in data
        assert "chroma_db_connected" in data


# --- Upload Tests ---

class TestUploadEndpoint:
    @patch("app.routes.upload.process_pdf")
    @patch("app.routes.upload.get_file_size_mb")
    def test_upload_valid_pdf(self, mock_size, mock_process, client):
        """A valid PDF upload should return 200 with document info."""
        from langchain.schema import Document
        mock_size.return_value = 1.5
        mock_process.return_value = [
            Document(
                page_content="Test content",
                metadata={"document_id": "doc_x", "filename": "test.pdf", "page_number": 1, "chunk_index": 0}
            )
        ]

        fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
        res = client.post(
            "/api/v1/upload",
            files={"file": ("test.pdf", fake_pdf, "application/pdf")}
        )

        assert res.status_code == 200
        data = res.json()
        assert "document_id" in data
        assert "total_chunks" in data
        assert data["filename"] == "test.pdf"

    def test_upload_non_pdf_rejected(self, client):
        """Non-PDF files should be rejected with 400."""
        fake_txt = io.BytesIO(b"This is a text file")
        res = client.post(
            "/api/v1/upload",
            files={"file": ("document.txt", fake_txt, "text/plain")}
        )
        assert res.status_code == 400
        assert "PDF" in res.json()["detail"]


# --- Documents Tests ---

class TestDocumentsEndpoint:
    def test_list_documents_returns_200(self, client):
        res = client.get("/api/v1/documents")
        assert res.status_code == 200

    def test_list_documents_structure(self, client):
        res = client.get("/api/v1/documents")
        data = res.json()
        assert "total_documents" in data
        assert "documents" in data
        assert isinstance(data["documents"], list)

    def test_delete_existing_document(self, client):
        res = client.delete("/api/v1/documents/test_doc_abc123")
        assert res.status_code == 200
        data = res.json()
        assert "chunks_deleted" in data

    def test_delete_nonexistent_document(self, client):
        res = client.delete("/api/v1/documents/does_not_exist")
        assert res.status_code == 404


# --- Chat Tests ---

class TestChatEndpoint:
    def test_ask_question_returns_200(self, client):
        res = client.post(
            "/api/v1/chat",
            json={"question": "What is this document about?"}
        )
        assert res.status_code == 200

    def test_answer_has_required_fields(self, client):
        res = client.post(
            "/api/v1/chat",
            json={"question": "What is RAG?"}
        )
        data = res.json()
        assert "question" in data
        assert "answer" in data
        assert "source_chunks" in data
        assert "model_used" in data
        assert "response_time_seconds" in data

    def test_source_chunks_have_scores(self, client):
        res = client.post(
            "/api/v1/chat",
            json={"question": "Tell me about retrieval", "top_k": 3}
        )
        data = res.json()
        for chunk in data["source_chunks"]:
            assert "similarity_score" in chunk
            assert 0.0 <= chunk["similarity_score"] <= 1.0

    def test_short_question_rejected(self, client):
        """Question must be at least 3 characters."""
        res = client.post(
            "/api/v1/chat",
            json={"question": "Hi"}
        )
        assert res.status_code == 422

    def test_empty_question_rejected(self, client):
        res = client.post(
            "/api/v1/chat",
            json={"question": ""}
        )
        assert res.status_code == 422
