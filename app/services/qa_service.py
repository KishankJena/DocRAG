# app/services/qa_service.py
# ============================================================
# Question Answering Service using LangChain + LLM
#
# RAG Steps 8, 9, 10:
#   - Take retrieved chunks as context
#   - Send to LLM with a prompt
#   - Return answer + sources
# ============================================================

import time
from typing import List, Optional, Dict, Any

# from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma

from app.services.vector_store import get_vector_store_service, get_embeddings
from app.models.schemas import QuestionResponse, SourceChunk
from app.utils.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


# ============================================================
# Custom RAG Prompt
# This is important — the default LangChain prompt is fine,
# but a custom one gives us more control over tone and format.
# ============================================================
RAG_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions based on the provided document context.

Use ONLY the information from the context below to answer the question.
If the context doesn't contain enough information to answer, say:
"I don't have enough information in the provided documents to answer this question."

Do NOT make up information or use knowledge outside of the provided context.

Context:
{context}

Question: {question}

Answer:"""

RAG_PROMPT = PromptTemplate(
    template=RAG_PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)


# def get_llm():
#     """
#     Initialize the LLM.
#     If USE_LOCAL_LLM is true, we try to load a local Llama model.
#     Otherwise, we use OpenAI's chat models.
#     """
#     if settings.use_local_llm:
#         return _get_local_llm()
#     return _get_openai_llm()
def get_llm():
    logger.info(f"Using Ollama model: {settings.llm_model}")

    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=0.1,
    )


# def _get_openai_llm():
#     """OpenAI ChatGPT via LangChain."""
#     logger.info(f"Using OpenAI LLM: {settings.openai_model}")
#     return ChatOpenAI(
#         model=settings.openai_model,
#         openai_api_key=settings.openai_api_key,
#         temperature=0.1,   # Low temperature = more factual, less creative
#         max_tokens=1024,
#     )


# def _get_local_llm():
    """
    Optional: Local Llama model via llama-cpp-python.
    Only works if you have:
    1. A GGUF model file downloaded
    2. llama-cpp-python installed

    To try this:
    - Set USE_LOCAL_LLM=true in .env
    - Set LOCAL_MODEL_PATH to your .gguf file
    - pip install llama-cpp-python
    """
    try:
        from langchain_community.llms import LlamaCpp
        logger.info(f"Using local Llama model: {settings.local_model_path}")
        return LlamaCpp(
            model_path=settings.local_model_path,
            temperature=0.1,
            max_tokens=1024,
            n_ctx=4096,        # Context window size
            verbose=False,
        )
    except ImportError:
        raise ImportError(
            "llama-cpp-python is not installed. "
            "Run: pip install llama-cpp-python"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load local model: {e}")


class QAService:
    """
    Orchestrates the full RAG pipeline for answering questions.

    Flow:
    1. User sends a question
    2. We retrieve relevant chunks via vector similarity search
    3. We pass chunks as context to the LLM
    4. LLM generates an answer grounded in those chunks
    5. We return the answer + the source chunks (with scores)
    """

    def __init__(self):
        self.vector_store_service = get_vector_store_service()
        self.embeddings = get_embeddings()
        logger.info("QAService initialized")

    def answer_question(
        self,
        question: str,
        document_id: Optional[str] = None,
        top_k: int = 4,
    ) -> QuestionResponse:
        """
        Main entry point: take a question, return an answer with sources.

        Args:
            question: The user's natural language question
            document_id: Limit search to one document (optional)
            top_k: Number of chunks to retrieve

        Returns:
            QuestionResponse with answer, sources, and metadata
        """
        start_time = time.time()
        logger.info(f"Answering question: '{question[:80]}'")

        # --- Step 1: Retrieve relevant chunks ---
        raw_results = self.vector_store_service.similarity_search(
            query=question,
            top_k=top_k,
            document_id=document_id,
        )

        if not raw_results:
            # No relevant chunks found — return a graceful response
            return QuestionResponse(
                question=question,
                answer="I couldn't find any relevant information in the uploaded documents to answer this question.",
                source_chunks=[],
                # model_used=settings.openai_model if not settings.use_local_llm else "local-llama",
                model_used=settings.llm_model,
                total_chunks_searched=0,
                response_time_seconds=round(time.time() - start_time, 2),
            )

        # --- Step 2: Build context string from retrieved chunks ---
        # We concatenate the chunks with separators so the LLM sees them clearly
        context_parts = []
        for i, result in enumerate(raw_results, start=1):
            filename = result["metadata"].get("filename", "unknown")
            page = result["metadata"].get("page_number", "?")
            context_parts.append(
                f"[Source {i} — {filename}, page {page}]\n{result['content']}"
            )
        context = "\n\n---\n\n".join(context_parts)

        # --- Step 3: Generate answer with LLM ---
        llm = get_llm()
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)

        logger.info("Sending context + question to LLM...")
        llm_response = llm.invoke(prompt)

        # Extract the text from the LLM response object
        if hasattr(llm_response, "content"):
            answer = llm_response.content   # ChatOpenAI returns an AIMessage
        else:
            answer = str(llm_response)      # LlamaCpp returns a string

        # --- Step 4: Format source chunks for the response ---
        source_chunks = []
        for result in raw_results:
            meta = result["metadata"]
            source_chunks.append(SourceChunk(
                content=result["content"],
                document_id=meta.get("document_id", ""),
                filename=meta.get("filename", "unknown"),
                page_number=meta.get("page_number"),
                similarity_score=result["similarity_score"],
                chunk_index=meta.get("chunk_index", 0),
            ))

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Answer generated in {elapsed}s")

        return QuestionResponse(
            question=question,
            answer=answer.strip(),
            source_chunks=source_chunks,
            # model_used=settings.openai_model if not settings.use_local_llm else "local-llama",
            model_used=settings.llm_model,
            total_chunks_searched=len(raw_results),
            response_time_seconds=elapsed,
        )


# --- Singleton ---
_qa_service: Optional[QAService] = None


def get_qa_service() -> QAService:
    """Returns a singleton QAService instance."""
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService()
    return _qa_service
