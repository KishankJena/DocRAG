# tests/test_helpers.py
# ============================================================
# Unit tests for utility helper functions
# ============================================================

import pytest
from app.utils.helpers import (
    generate_document_id,
    is_valid_pdf,
    format_source_for_display,
)


class TestGenerateDocumentId:
    def test_returns_string(self):
        result = generate_document_id("my_document.pdf")
        assert isinstance(result, str)

    def test_includes_filename_base(self):
        result = generate_document_id("annual_report.pdf")
        assert "annual_report" in result

    def test_ids_are_unique(self):
        """Calling with the same filename should give different IDs each time."""
        id1 = generate_document_id("same.pdf")
        id2 = generate_document_id("same.pdf")
        assert id1 != id2

    def test_handles_special_characters(self):
        """Filenames with spaces and special chars should be sanitized."""
        result = generate_document_id("My Report (2024).pdf")
        # Should not contain spaces or parentheses
        assert " " not in result
        assert "(" not in result
        assert ")" not in result


class TestIsValidPdf:
    def test_pdf_extension_valid(self):
        assert is_valid_pdf("document.pdf") is True

    def test_uppercase_pdf_valid(self):
        assert is_valid_pdf("REPORT.PDF") is True

    def test_txt_invalid(self):
        assert is_valid_pdf("document.txt") is False

    def test_docx_invalid(self):
        assert is_valid_pdf("report.docx") is False

    def test_no_extension_invalid(self):
        assert is_valid_pdf("filename") is False


class TestFormatSourceForDisplay:
    def test_short_text_unchanged(self):
        text = "Short text"
        result = format_source_for_display(text, max_length=300)
        assert result == text

    def test_long_text_truncated(self):
        text = "A" * 500
        result = format_source_for_display(text, max_length=300)
        assert len(result) <= 303  # 300 + "..."
        assert result.endswith("...")

    def test_exact_limit_not_truncated(self):
        text = "A" * 300
        result = format_source_for_display(text, max_length=300)
        assert not result.endswith("...")
