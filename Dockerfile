# Multi-stage Dockerfile for OpenWebUI Enhanced Memory System
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FORCE_CPU_ONLY=1
ENV TOKENIZERS_PARALLELISM=false
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_DEFAULT_TIMEOUT=1000

# Create application user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 -m -d /home/appuser appuser

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make python3-dev build-essential \
    libffi-dev libssl-dev zlib1g-dev \
    libc6-dev pkg-config sqlite3 libsqlite3-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN python -m pip install --upgrade pip==23.3.1 wheel setuptools

# Install PyTorch first
RUN python -m pip install --timeout=1000 --retries=10 \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other packages
RUN python -m pip install --timeout=1000 --retries=10 -r requirements.txt

# Copy application
COPY . .
RUN chown -R appuser:appuser /app

USER appuser

# Copy common files
COPY human_logging.py error_handler.py config.py ./

# Create necessary directories
RUN mkdir -p /app/storage /app/data /app/config && \
    chown -R appuser:appuser /app

# Backend service stage
FROM base AS backend

# Copy backend application files
COPY main.py startup.py models.py ./
COPY routes/ ./routes/
COPY handlers/ ./handlers/
COPY services/ ./services/
COPY utilities/ ./utilities/
COPY *.py ./
COPY config*.py ./
COPY config/ ./config/

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

CMD ["python", "main.py"]

# Memory API service stage
FROM base AS memory-api

# Copy memory API specific files
COPY integrated_memory_startup.py ./
COPY services/ ./services/
COPY utilities/ ./utilities/
COPY scripts/ ./scripts/
COPY config*.py ./
COPY config/ ./config/

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "integrated_memory_startup.py"]

# Pipeline installer stage (runs once then exits)
FROM base AS installer

# Install additional dependencies for OpenWebUI interaction
RUN pip install --no-cache-dir httpx

# Copy installer scripts and pipelines
COPY scripts/ ./scripts/
COPY pipelines/ ./pipelines/
COPY config*.py ./
COPY config/ ./config/
COPY storage/ ./storage/

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Environment variables for installer
ENV OPENWEBUI_URL=http://open-webui:8080
ENV BACKEND_URL=http://backend:3000
ENV MEMORY_API_URL=http://memory-api:8080

CMD ["python", "scripts/unified_installer.py"]

# Development stage (for local development)
FROM backend AS development

# Install development dependencies
USER root
RUN pip install --no-cache-dir pytest pytest-asyncio black flake8 mypy

# Copy test files
COPY tests/ ./tests/

# Switch back to appuser
USER appuser

# Development command (overridden in docker-compose.dev.yml)
CMD ["python", "-m", "pytest", "tests/", "-v"]
