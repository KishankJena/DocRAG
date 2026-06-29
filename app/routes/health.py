# app/routes/health.py
# ============================================================
# Route: GET /health
# Simple health check to verify the API is running
# ============================================================

from fastapi import APIRouter, Depends

from app.models.schemas import HealthResponse
from app.services.vector_store import VectorStoreService, get_vector_store_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

APP_VERSION = "1.0.0"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check that the API and ChromaDB are running correctly."
)
async def health_check(
    vector_store: VectorStoreService = Depends(get_vector_store_service),
):
    """
    Quick sanity check endpoint.
    Useful for deployment health checks and debugging.
    """
    chroma_ok = False
    total_docs = 0

    try:
        total_docs = vector_store.get_total_documents()
        chroma_ok = True
    except Exception as e:
        logger.warning(f"ChromaDB health check failed: {e}")

    return HealthResponse(
        status="ok" if chroma_ok else "degraded",
        version=APP_VERSION,
        total_documents=total_docs,
        chroma_db_connected=chroma_ok,
    )
