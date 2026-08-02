# app/main.py
# ============================================================
# FastAPI Application Entry Point
#
# This is where the app is created, middleware is added,
# and all routes are registered.
# ============================================================

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import upload, chat, documents, health, auth
from app.utils.config import get_settings
from app.utils.logger import get_logger
from app.utils.helpers import ensure_directory

settings = get_settings()
logger = get_logger(__name__)


# ============================================================
# Lifespan: startup/shutdown logic
# This runs when the app starts up and shuts down
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Called once when the FastAPI app starts.
    Great place to initialize resources.
    """
    logger.info("=" * 50)
    logger.info("PDF Chatbot API starting up...")
    logger.info(f"  Model: {settings.llm_model}")
    logger.info(f"  Embeddings: {settings.embedding_model}")
    logger.info(f"  ChromaDB path: {settings.chroma_db_path}")
    logger.info(f"  Debug mode: {settings.debug}")

    # Ensure required directories exist
    ensure_directory(settings.upload_dir)
    ensure_directory(settings.chroma_db_path)
    logger.info(f"  Upload dir ready: {settings.upload_dir}")
    logger.info(f"  ChromaDB dir ready: {settings.chroma_db_path}")

    logger.info("Startup complete. Ready to handle requests.")
    logger.info("=" * 50)

    yield  # App runs here

    # Shutdown
    logger.info("PDF Chatbot API shutting down...")


# ============================================================
# Create FastAPI App
# ============================================================
app = FastAPI(
    title="PDF Chatbot API",
    description=(
        "A RAG-based PDF Question Answering API. "
        "Upload PDFs, then ask questions and get answers with source citations."
    ),
    version="1.0.0",
    lifespan=lifespan,
    # Swagger UI will be at /docs, ReDoc at /redoc
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================
# CORS Middleware
# Allows the frontend (running on a different port) to call the API
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Register Routes
# All endpoints are prefixed with /api/v1
# ============================================================
API_PREFIX = "/api/v1"

app.include_router(health.router, prefix=API_PREFIX, tags=["Health"])
app.include_router(upload.router, prefix=API_PREFIX, tags=["Documents"])
app.include_router(documents.router, prefix=API_PREFIX, tags=["Documents"])
app.include_router(chat.router, prefix=API_PREFIX, tags=["Chat"])
app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["Authentication"])


# ============================================================
# Serve Frontend
# If a frontend/index.html exists, serve the whole frontend dir
# ============================================================
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(os.path.join(frontend_dir, "index.html")):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"Frontend served from: {frontend_dir}")


# ============================================================
# Root redirect (if no frontend)
# ============================================================
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "PDF Chatbot API is running!",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
