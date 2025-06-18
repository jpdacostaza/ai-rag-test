FROM python:3.11-slim-bookworm

# Add a build argument to force cache invalidation
ARG CACHEBUST=1

# Create llama user for Linux compatibility with home directory
RUN groupadd -r llama && useradd -r -g llama -u 1000 -m -d /home/llama llama

WORKDIR /opt/backend

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl sqlite3 libsqlite3-0 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make startup script executable
RUN chmod +x startup.sh

# Create storage directory and set proper permissions
RUN mkdir -p ./storage && \
    mkdir -p /opt/internal_cache/sentence_transformers && \
    chown -R llama:llama /opt/backend && \
    chown -R llama:llama /opt/internal_cache && \
    chown -R llama:llama /home/llama && \
    chmod -R 755 /opt/backend && \
    chmod -R 755 /opt/internal_cache && \
    chmod -R 755 /home/llama

# Make startup scripts executable
RUN chmod +x /opt/backend/startup.sh && \
    chmod +x /opt/backend/smart-startup.sh

# Switch to llama user
USER llama

EXPOSE 8001

# Use the smart startup script for enhanced setup and monitoring
CMD ["./smart-startup.sh"]
