# app/utils/helpers.py
# ============================================================
# Small helper functions used across the app
# ============================================================

import os
import uuid
import hashlib
from pathlib import Path


def generate_document_id(filename: str) -> str:
    """
    Generate a unique document ID from the filename + a UUID.
    Using a short hash keeps IDs readable but still unique.

    Example: 'report_a1b2c3d4'
    """
    base = Path(filename).stem  # filename without extension
    # Take first 8 chars of a UUID for uniqueness
    unique_suffix = uuid.uuid4().hex[:8]
    # Sanitize the base name (remove spaces/special chars)
    safe_base = "".join(c if c.isalnum() else "_" for c in base)[:20]
    return f"{safe_base}_{unique_suffix}"


def get_file_size_mb(file_path: str) -> float:
    """Return the file size in megabytes."""
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)


def ensure_directory(path: str) -> None:
    """Create a directory if it doesn't already exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def is_valid_pdf(filename: str) -> bool:
    """Check if the file has a .pdf extension."""
    return filename.lower().endswith(".pdf")


def format_source_for_display(content: str, max_length: int = 300) -> str:
    """
    Truncate long source chunks for display purposes.
    Adds '...' if the text was cut short.
    """
    content = content.strip()
    if len(content) <= max_length:
        return content
    return content[:max_length] + "..."
