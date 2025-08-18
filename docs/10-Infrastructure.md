# Infrastructure

Docker Compose
- Orchestrates Redis, Chroma, Ollama, backend (FastAPI), memory API, pipelines, OpenWebUI, function installer, API Gateway, Watchtower
- Health checks and environment wiring per service

Dockerfiles
- `Dockerfile.*`: per-service images with dependencies

Scripts (`scripts/`)
- Model management, pipeline setup, memory configuration, function installer, cleanup utilities

Notes
- Validate environment variable naming consistency across services
- Consider enabling uvicorn/access logs in dev builds
