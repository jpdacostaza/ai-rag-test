FROM python:3.11-slim-bookworm

# Add a build argument to force cache invalidation
ARG CACHEBUST=1

# Set environment variables to force CPU-only mode
ENV CUDA_VISIBLE_DEVICES=""
ENV PYTORCH_CUDA_ALLOC_CONF=""
ENV FORCE_CPU_ONLY=1
ENV TOKENIZERS_PARALLELISM=false
ENV HUGGINGFACE_HUB_CACHE="/opt/cache/huggingface"
ENV SENTENCE_TRANSFORMERS_HOME="/opt/internal_cache/sentence_transformers"
ENV TRANSFORMERS_CACHE="/opt/cache/transformers"
ENV TORCH_HOME="/opt/cache/torch"
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1
ENV NUMBA_DISABLE_CUDA=1

# Create llama user for Linux compatibility with home directory
RUN groupadd -r llama && useradd -r -g llama -u 1000 -m -d /home/llama llama

WORKDIR /opt/backend

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl sqlite3 libsqlite3-0 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt

# Install CPU-only PyTorch first to prevent CUDA versions
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install remaining requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make startup script executable
RUN chmod +x scripts/startup.sh

# Create storage and cache directories with proper permissions
RUN mkdir -p ./storage && \
    mkdir -p /opt/internal_cache/sentence_transformers && \
    mkdir -p /opt/cache/chroma/onnx_models && \
    chown -R llama:llama /opt/backend && \
    chown -R llama:llama /opt/internal_cache && \
    chown -R llama:llama /opt/cache && \
    chown -R llama:llama /home/llama && \
    chmod -R 755 /opt/backend && \
    chmod -R 755 /opt/internal_cache && \
    chmod -R 777 /opt/cache && \
    chmod -R 755 /home/llama

# Switch to llama user
USER llama

EXPOSE 8001

# Use the startup script for backend initialization
CMD ["/opt/backend/scripts/startup.sh"]
