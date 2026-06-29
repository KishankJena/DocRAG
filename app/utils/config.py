# app/utils/config.py
# ============================================================
# Application configuration using pydantic-settings
# All settings are loaded from environment variables / .env file
# ============================================================

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """
    Central config object. pydantic-settings automatically reads
    values from the .env file or actual environment variables.
    """

    # # --- OpenAI ---
    # openai_api_key: str = Field(..., description="Your OpenAI API key")
    # openai_model: str = Field(default="gpt-3.5-turbo", description="LLM model to use")
    # embedding_model: str = Field(default="text-embedding-ada-002", description="Embedding model")

    # --- ChromaDB ---
    chroma_db_path: str = Field(default="./chroma_db", description="Persistence path for ChromaDB")

    # --- File Upload ---
    upload_dir: str = Field(default="./uploads", description="Where uploaded PDFs are saved")
    max_file_size_mb: int = Field(default=50, description="Max upload size in MB")

    # --- Text Chunking ---
    chunk_size: int = Field(default=1000, description="Characters per chunk")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")

    # --- Retrieval ---
    top_k_results: int = Field(default=4, description="Number of chunks to retrieve per query")

    # # --- Optional Local LLM (Llama) ---
    # use_local_llm: bool = Field(default=False, description="Use local Llama model instead of OpenAI")
    # local_model_path: str = Field(default="", description="Path to local GGUF model file")



    # --- Ollama ---
    ollama_base_url: str = Field(default="http://localhost:11434")
    llm_model: str = Field(default="llama3.2:3b")
    embedding_model: str = Field(default="nomic-embed-text")
    
    
    # --- App ---
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # This allows extra fields in .env without throwing errors
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    lru_cache means we only read from .env once — good for performance.
    """
    return Settings()
