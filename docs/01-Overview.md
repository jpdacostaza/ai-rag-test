# Overview

This project provides an OpenAI-compatible FastAPI backend powering OpenWebUI with:
- Chat completions (non-streaming and streaming)
- Memory-enabled RAG (Redis + ChromaDB)
- A lightweight API Gateway (aiohttp) with load-balancing and security
- Document ingestion and semantic search endpoints
- Rich observability: Prometheus metrics and unified structured logging

Key goals
- Simple, reliable OpenAI-style API for frontends
- Built-in memory and document context
- Secure, resilient microservice proxy via a gateway
- Easy local bring-up via Docker Compose

Core user flows
- Send a chat completion request to `/v1/chat/completions` and receive a response or stream tokens.
- Upload documents to `/upload/document` and query them via semantic search.
- Query or store user memories via `/api/memory` endpoints.

What this project is not
- A full-featured production gateway security solution out of the box (demo JWT handling is included; harden for prod).
- A monolith: services are modular and containerized.
