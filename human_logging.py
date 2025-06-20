"""
Enhanced logging configuration for human-readable logs
Provides colored, structured, and user-friendly logging output
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

# --- Constants ---

# Color codes for terminal output
COLORS = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",  # Reset
    "BOLD": "\033[1m",  # Bold
    "DIM": "\033[2m",  # Dim
}

# Emojis for different log levels
EMOJIS = {
    "DEBUG": "🔍",
    "INFO": "✅",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "🚨",
}

# Icons for various services and components
SERVICE_ICONS = {
    "REDIS": "🔴",
    "CHROMADB": "🟣",
    "OLLAMA": "🤖",
    "DATABASE": "💾",
    "API": "🚀",
    "HEALTH": "🏥",
    "MEMORY": "🧠",
    "CHAT": "💬",
    "TOOLS": "🔧",
    "WATCHDOG": "👀",
    "STARTUP": "🏁",
    "CACHE": "⚡",
    "ERROR": "💥",
    "NETWORK": "🌐",
    "EMBEDDINGS": "🧠",
}

# --- Formatter ---


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors, emojis, and structured output."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Formats a log record with colors, emojis, and contextual icons."""
        level_name = record.levelname
        message = record.getMessage()

        if self.use_colors:
            COLORS.get(level_name, "")
            ___________reset, ___________bold, ___________dim = (
                COLORS["RESET"],
                COLORS["BOLD"],
                COLORS["DIM"],
            )
        else:
            ____________level_color = ____________reset = ____________bold = ____________dim = ""

        EMOJIS.get(level_name, "📝")
        ____________timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")

        # Extract service icon from message (e.g., "[REDIS]")
        for service, icon in SERVICE_ICONS.items():
            if "[{service}]" in message:
                message = message.replace("[{service}]", "").strip()
                break

        # Define format based on log level
        log_formats = {
            "ERROR": "{emoji} {bold}{level_color}{timestamp}{reset} │ {level_color}{bold}{level_name:<8}{reset} │ \
                {service_icon}{bold}{message}{reset}",
            "CRITICAL": "{emoji} {bold}{level_color}{timestamp}{reset} │ {level_color}{bold}{level_name:<8}{reset} │ \
                {service_icon}{bold}{message}{reset}",
            "WARNING": "{emoji} {level_color}{timestamp}{reset} │ {level_color}{level_name:<8}{reset} │ \
                {service_icon}{message}",
            "INFO": "{emoji} {timestamp} │ {level_color}{level_name:<8}{reset} │ {service_icon}{message}",
            "DEBUG": "{emoji} {dim}{timestamp} │ {level_color}{level_name:<8}{reset} │ {service_icon}{message}{reset}",
        }

        return log_formats.get(
            level_name, "{emoji} {timestamp} │ {level_name:<8} │ {service_icon}{message}"
        )


# --- Logger Setup ---

# Singleton logger instance
logger = logging.getLogger(__name__)


class HumanLogger:
    """Manages the setup and configuration of the application logger."""

    @staticmethod
    def setup(level: str = "INFO") -> None:
        """
        Set up human-readable logging for the entire application.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)

        # Clear existing handlers to prevent duplicate logs
        if logger.hasHandlers():
            logger.handlers.clear()

        logger.setLevel(numeric_level)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)

        # Use ColoredFormatter for TTY, otherwise a simple one
        if sys.stdout.isatty():
            formatter = ColoredFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s │ %(levelname)-8s │ %(message)s", datefmt="%H:%M:%S"
            )

        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        logger.info("[STARTUP] 🎨 Enhanced logging initialized at level {level.upper()}")


# --- Convenience Functions ---


def log_service_status(service: str, status: str, details: str = ""):
    """Log service status in a consistent, structured format."""
    status_icons = {
        "starting": "🟡",
        "ready": "✅",
        "degraded": "⚠️",
        "failed": "❌",
        "connecting": "🔗",
        "reconnecting": "🔄",
    }
    status_icons.get(status.lower(), "📝")
    message = "[{service.upper()}] {icon} {status.title()}{' - {details}' if details else ''}"

    log_level = (
        "error"
        if status.lower() == "failed"
        else "warning" if status.lower() == "degraded" else "info"
    )
    getattr(logger, log_level)(message)


def log_api_request(method: str, endpoint: str, status_code: int, response_time_ms: float):
    """Log API requests with color-coded status and timing."""
    if status_code < 400:
        pass
    elif 400 <= status_code < 500:
        pass
    else:
        pass
    logger.info(
        "[API] {status_emoji} {method} {endpoint} → {status_code} ({response_time_ms:.2f}ms)"
    )


def log_chat_interaction(
    user_id: str,
    message_len: int,
    response_len: int,
    tools_used: Optional[list] = None,
    request_id: Optional[str] = None,
):
    """Log key details of a chat interaction."""
    ____________tools_info = " (tools: {', '.join(tools_used)})" if tools_used else ""
    ____________req_id_info = " [ReqID: {request_id}]" if request_id else ""
    logger.info(
        "[CHAT] 💬 User {user_id}: {message_len} chars → {response_len} chars{tools_info}{req_id_info}"
    )


# --- Initialization ---


def init_logging(level: Optional[str] = None):
    """Initialize the enhanced logging system from environment variables or defaults."""
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    HumanLogger.setup(log_level)


# Initialize automatically on import
init_logging()
