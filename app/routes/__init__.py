"""
app.routes package

This package exposes route modules as simple imports used by `app.main`.
"""

from . import upload, chat, documents, health  # noqa: F401

__all__ = ["upload", "chat", "documents", "health"]
