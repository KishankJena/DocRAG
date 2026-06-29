"""
app.models package

Re-export schemas module under app.models.schemas
"""

from . import schemas  # noqa: F401

__all__ = ["schemas"]
