# UniPath LK

Local RAG assistant for **UGC Sri Lanka university admission** questions, grounded in the official 2025/26 Student Handbook.

> **Disclaimer:** This is an educational portfolio project. It is not official UGC advice. Always verify with [UGC Sri Lanka](https://www.ugc.ac.lk/).

## Features

- PDF ingestion with PyMuPDF
- Token-aware chunking (~400 tokens) with section and `doc_type` metadata
- Hybrid retrieval: **Chroma (dense)** + **BM25 (keyword)** merged with **RRF**
- Local LLM via **Ollama** (`llama3.2` + `nomic-embed-text`)
- Golden Q&A evaluation harness

## Architecture
