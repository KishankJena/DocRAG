# 📚 PDF Chatbot RAG Pipeline

A full-stack, local-first **Retrieval-Augmented Generation (RAG)** application built with **FastAPI**, **LangChain**, **ChromaDB**, and **Ollama**. 

This system allows authenticated users to upload PDF documents, automatically chunk and embed their contents into a vector database, and ask questions with answers strictly grounded in the document context and backed by source citations.

---

## 🌟 Key Features

* **🔒 Multi-Tenant Data Isolation:** Enforces JWT-based authentication (`AuthN`) and metadata-level vector filtering (`owner_id`) in ChromaDB (`AuthZ`), ensuring zero cross-tenant data leakage.
* **🤖 100% Local Inference:** Utilizes local Ollama models for both text embeddings (`nomic-embed-text`) and answer generation (`llama3.2` / `qwen2.5`), requiring zero external cloud API keys.
* **📄 Smart PDF Ingestion:** Page-by-page text extraction, custom character chunking with overlap preservation, and automatic document metadata tagging.
* **🎯 Grounded Responses & Citations:** Every answer returns source citations, page numbers, and vector similarity match percentages.
* **🎨 Modular Frontend UI:** Modern, dark technical interface written in native modular ES6 JavaScript, HTML5, and CSS3, served natively via FastAPI.

---

## 🏗️ System Architecture

```text
[ User Interface (ES6 JS / HTML / CSS) ]
                   │
                   ▼ (HTTP / JWT Bearer)
[ FastAPI Backend Application ]
   ├── Authentication Router (/api/v1/auth)
   ├── PDF Processing Pipeline (/api/v1/upload)
   └── RAG QA Pipeline (/api/v1/chat)
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
[ ChromaDB Vector Store ]   [ Local Ollama Engine ]
 ├── Metadata Filter        ├── Embeddings: nomic-embed-text
 └── (owner_id, doc_id)     └── LLM: llama3.2 / qwen2.5
