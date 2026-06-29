# tests/test_pdf_service.py
# ============================================================
# Unit tests for PDF text extraction and chunking
# Run with: pytest tests/ -v
# ============================================================

import os
import pytest
from unittest.mock import patch, MagicMock
from langchain.schema import Document

from app.services.pdf_service import chunk_documents, process_pdf


class TestChunkDocuments:
    """Tests for the text chunking logic."""

    def test_basic_chunking(self):
        """Chunking should split text and attach metadata."""
        pages = [("This is a test document with enough text to be meaningful. " * 20, 1)]
        chunks = chunk_documents(pages, document_id="test_doc", filename="test.pdf")

        assert len(chunks) > 0
        assert all(isinstance(c, Document) for c in chunks)

    def test_metadata_attached(self):
        """Each chunk should have document_id, filename, page_number, chunk_index."""
        pages = [("Sample text content for testing. " * 30, 1)]
        chunks = chunk_documents(pages, document_id="doc_123", filename="sample.pdf")

        for chunk in chunks:
            assert chunk.metadata["document_id"] == "doc_123"
            assert chunk.metadata["filename"] == "sample.pdf"
            assert "page_number" in chunk.metadata
            assert "chunk_index" in chunk.metadata

    def test_chunk_indices_are_sequential(self):
        """Chunk indices should start at 0 and be sequential."""
        pages = [("Some text content that needs chunking. " * 30, 1)]
        chunks = chunk_documents(pages, document_id="doc_abc", filename="file.pdf")

        indices = [c.metadata["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_short_text_filtered_out(self):
        """Very short chunks (< 50 chars) should be skipped."""
        # Only very short text — should produce 0 chunks
        pages = [("Hi", 1), ("OK", 2)]
        chunks = chunk_documents(pages, document_id="doc_x", filename="x.pdf")
        assert len(chunks) == 0

    def test_multiple_pages(self):
        """Chunks from multiple pages should all have correct page metadata."""
        pages = [
            ("Content from page one with lots of text. " * 20, 1),
            ("Content from page two with different text. " * 20, 2),
        ]
        chunks = chunk_documents(pages, document_id="multi_doc", filename="multi.pdf")

        page_numbers = set(c.metadata["page_number"] for c in chunks)
        # Both pages should appear in the chunks
        assert 1 in page_numbers
        assert 2 in page_numbers

    def test_empty_pages_returns_empty(self):
        """No pages → no chunks."""
        chunks = chunk_documents([], document_id="empty", filename="empty.pdf")
        assert chunks == []


class TestProcessPdf:
    """Tests for the full PDF processing pipeline."""

    @patch("app.services.pdf_service.extract_text_from_pdf")
    def test_process_pdf_calls_chunker(self, mock_extract):
        """process_pdf should call extract and then chunk."""
        mock_extract.return_value = [("Sample text content here. " * 30, 1)]

        chunks = process_pdf(
            file_path="/fake/path.pdf",
            document_id="doc_001",
            filename="test.pdf"
        )

        mock_extract.assert_called_once_with("/fake/path.pdf")
        assert len(chunks) > 0

    @patch("app.services.pdf_service.extract_text_from_pdf")
    def test_empty_pdf_raises_error(self, mock_extract):
        """A PDF with no extractable text should raise ValueError."""
        mock_extract.return_value = []  # Simulate scanned/image PDF

        with pytest.raises(ValueError, match="Could not extract any text"):
            process_pdf(
                file_path="/fake/empty.pdf",
                document_id="doc_002",
                filename="empty.pdf"
            )
