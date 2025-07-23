#!/bin/bash
# Auto-start script for AI RAG Backend with ARM64 optimizations
# This script handles automatic startup on boot for Orange Pi 5 Plus

BACKEND_DIR="/opt/backend"  # Change this to your actual backend directory path
LOG_FILE="/var/log/ai-rag-backend.log"
USER="pi"  # Change this to your username

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    log_message "ERROR: Backend directory not found at $BACKEND_DIR"
    log_message "Please update BACKEND_DIR in this script to match your installation path"
    exit 1
fi

# Change to backend directory
cd "$BACKEND_DIR" || exit 1

# Wait for system to be ready (network, docker, etc.)
log_message "Waiting for system to be ready..."
sleep 30

# Check if Docker is running
if ! systemctl is-active --quiet docker; then
    log_message "Starting Docker service..."
    systemctl start docker
    sleep 10
fi

# Run the ARM64 startup script
log_message "Starting AI RAG Backend with ARM64 optimizations..."
if [ -f "./start-arm64.sh" ]; then
    chmod +x "./start-arm64.sh"
    su "$USER" -c "./start-arm64.sh" >> "$LOG_FILE" 2>&1
    log_message "ARM64 startup script completed"
else
    log_message "WARNING: start-arm64.sh not found, using standard startup"
    su "$USER" -c "docker-compose -f docker-compose.yml -f docker-compose.arm64.yml up -d" >> "$LOG_FILE" 2>&1
fi

log_message "AI RAG Backend startup process finished"
