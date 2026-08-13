# 📄 PDF Chatbot — RAG-Powered Q&A System

A **Retrieval-Augmented Generation (RAG)** application that lets you upload PDF documents and ask natural language questions about them. Built with FastAPI, LangChain, ChromaDB, and OpenAI.

> **Portfolio project** built to demonstrate understanding of RAG pipelines, vector databases, semantic search, and LLM integration.

---

## 🧠 How It Works (RAG Pipeline)

```
PDF Upload → Extract Text → Chunk Text → Generate Embeddings → Store in ChromaDB
                                                                        ↓
User Question → Embed Question → Similarity Search → Retrieve Top-K Chunks
                                                                        ↓
                              LLM (GPT-3.5/4) → Answer + Source Chunks
```

1. **PDF Processing** — Extract text page-by-page using `pypdf`
2. **Chunking** — Split text into overlapping chunks with `RecursiveCharacterTextSplitter`
3. **Embedding** — Convert chunks to 1536-dim vectors with `text-embedding-ada-002`
4. **Storage** — Persist vectors + metadata in ChromaDB
5. **Retrieval** — Cosine similarity search to find the most relevant chunks
6. **Generation** — GPT generates an answer grounded in the retrieved context

---

## ✨ Features

- 📤 **Upload multiple PDFs** — each stored separately in ChromaDB
- 🔍 **Semantic search** — finds contextually relevant passages, not just keyword matches
- 💬 **LLM-powered answers** — answers grounded in your documents (no hallucination from external knowledge)
- 📊 **Similarity scores** — see how relevant each source chunk is (0–100%)
- 📑 **Source citations** — every answer shows the exact passages it came from
- 🗂️ **Multi-document support** — search all docs or a specific one
- 💾 **Persistent storage** — ChromaDB survives server restarts
- 🦙 **Optional Llama support** — swap OpenAI for a local model

---

## 🗂️ Project Structure

```
project/
├── app/
│   ├── main.py                  # FastAPI app, middleware, route registration
│   ├── routes/
│   │   ├── upload.py            # POST /api/v1/upload
│   │   ├── chat.py              # POST /api/v1/chat
│   │   ├── documents.py         # GET/DELETE /api/v1/documents
│   │   └── health.py            # GET /api/v1/health
│   ├── services/
│   │   ├── pdf_service.py       # PDF text extraction + chunking
│   │   ├── vector_store.py      # ChromaDB operations (add/search/delete)
│   │   └── qa_service.py        # LLM Q&A with context injection
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response schemas
│   └── utils/
│       ├── config.py            # Settings from .env (pydantic-settings)
│       ├── logger.py            # Centralized logging setup
│       └── helpers.py           # Utility functions
│
├── frontend/
│   └── index.html               # Single-page chat UI
│
├── tests/
│   ├── test_api.py              # FastAPI endpoint integration tests
│   ├── test_pdf_service.py      # PDF processing unit tests
│   └── test_helpers.py          # Helper function unit tests
│
├── uploads/                     # Saved PDF files
├── chroma_db/                   # Persisted ChromaDB data
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourname/pdf-chatbot.git
cd pdf-chatbot

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000/api/v1
- **Frontend UI**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs

---

## 📡 API Endpoints

### `POST /api/v1/upload`
Upload and process a PDF.

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@your_document.pdf"
```

**Response:**
```json
{
  "message": "Successfully processed 'your_document.pdf'",
  "document_id": "your_document_a1b2c3d4",
  "filename": "your_document.pdf",
  "total_chunks": 47,
  "processing_time_seconds": 3.21
}
```

---

### `POST /api/v1/chat`
Ask a question about uploaded documents.

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main findings?",
    "top_k": 4
  }'
```

**Response:**
```json
{
  "question": "What are the main findings?",
  "answer": "The main findings indicate...",
  "source_chunks": [
    {
      "content": "The study found that...",
      "filename": "your_document.pdf",
      "page_number": 3,
      "similarity_score": 0.87,
      "chunk_index": 12
    }
  ],
  "model_used": "gpt-3.5-turbo",
  "total_chunks_searched": 4,
  "response_time_seconds": 1.45
}
```

---

### `GET /api/v1/documents`
List all uploaded documents.

### `DELETE /api/v1/documents/{document_id}`
Delete a document and its embeddings.

### `GET /api/v1/health`
Health check — confirms API and ChromaDB are running.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Tests use mocks for OpenAI and ChromaDB — no API keys needed to run tests.

```bash
# Run with coverage report
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 🦙 Optional: Using a Local Llama Model

If you want to run this without OpenAI costs, you can use a local model:

1. Download a GGUF model (e.g., from [HuggingFace](https://huggingface.co/TheBloke)):
   ```
   llama-2-7b-chat.Q4_K_M.gguf
   ```

2. Install llama-cpp-python:
   ```bash
   pip install llama-cpp-python
   ```

3. Update `.env`:
   ```
   USE_LOCAL_LLM=true
   LOCAL_MODEL_PATH=./models/llama-2-7b-chat.Q4_K_M.gguf
   ```

The rest of the pipeline (ChromaDB, embeddings) still uses OpenAI unless you also swap the embedding model.

---

## ⚙️ Configuration

All configuration is in `.env`:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | required | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | LLM model name |
| `EMBEDDING_MODEL` | `text-embedding-ada-002` | Embedding model |
| `CHROMA_DB_PATH` | `./chroma_db` | ChromaDB persistence path |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_RESULTS` | `4` | Chunks retrieved per query |
| `MAX_FILE_SIZE_MB` | `50` | Max upload size |
| `USE_LOCAL_LLM` | `false` | Use local Llama instead of OpenAI |

---

## 🔍 Key Concepts Demonstrated

| Concept | Implementation |
|---|---|
| **RAG** | Full pipeline: ingest → embed → retrieve → generate |
| **Vector Database** | ChromaDB with persistent storage |
| **Embeddings** | OpenAI `text-embedding-ada-002` (1536 dimensions) |
| **Semantic Search** | Cosine similarity via ChromaDB |
| **LLM Integration** | LangChain + ChatOpenAI with custom prompt |
| **FastAPI** | Async endpoints, Pydantic schemas, dependency injection |
| **Error Handling** | HTTPException with meaningful messages |
| **Logging** | Structured logs across all services |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI + Uvicorn |
| LLM Orchestration | LangChain |
| Vector Database | ChromaDB (persistent) |
| Embeddings | OpenAI text-embedding-ada-002 |
| LLM | OpenAI GPT-3.5-turbo / GPT-4 |
| PDF Parsing | pypdf |
| Data Validation | Pydantic v2 |
| Testing | pytest + httpx |

---

## 📝 Notes

- **Scanned PDFs** (image-only) won't work — the app extracts text directly. OCR support (e.g., `pytesseract`) would be a future improvement.
- **Large PDFs** take longer to process because each chunk requires an OpenAI embedding API call.
- **ChromaDB** data persists in `./chroma_db/` — delete this folder to reset the vector store.

---

*Built as a portfolio project to demonstrate RAG pipeline implementation from scratch.*
