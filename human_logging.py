"""
Human-readable logging for the FastAPI LLM backend.
Provides structured, colorized logging for better observability.
"""

import logging
import sys
from logging import StreamHandler, Formatter

class ColorizedFormatter(Formatter):
    """Custom formatter to add colors to log levels."""
    
    LOG_COLORS = {
        logging.DEBUG: "\033[90m",    # Grey
        logging.INFO: "\033[92m",     # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",    # Red
        logging.CRITICAL: "\033[95m", # Magenta
    }
    RESET_COLOR = "\033[0m"

    def format(self, record):
        log_color = self.LOG_COLORS.get(record.levelno, "")
        record.levelname = f"{log_color}{record.levelname:8s}{self.RESET_COLOR}"
        record.service = getattr(record, "service", "SYSTEM")
        record.status = getattr(record, "status", "-")
        
        # Format the final message
        log_format = "[%(asctime)s] [%(levelname)s] [%(service)s:%(status)s] - %(message)s"
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

class HumanLogger:
    """Singleton logger for consistent, human-readable output."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HumanLogger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        self.logger = logging.getLogger("HumanLogger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        if not self.logger.handlers:
            handler = StreamHandler(sys.stdout)
            handler.setFormatter(ColorizedFormatter())
            self.logger.addHandler(handler)

    @staticmethod
    def _log(level, service, status, message, *args, **kwargs):
        """Internal log method."""
        logger = HumanLogger().logger
        extra = {'service': service, 'status': status}
        logger.log(level, message, *args, extra=extra, **kwargs)

    @staticmethod
    def log_service_status(service: str, status: str, message: str):
        """Log a generic service status update."""
        level = logging.INFO
        if status in ["error", "failed"]: level = logging.ERROR
        if status == "warning": level = logging.WARNING
        HumanLogger._log(level, service.upper(), status.upper(), message)

    @staticmethod
    def log_redis_status(status: str, message: str):
        """Log Redis-specific status."""
        HumanLogger.log_service_status("REDIS", status, message)

    @staticmethod
    def log_chromadb_status(status: str, message: str):
        """Log ChromaDB-specific status."""
        HumanLogger.log_service_status("CHROMADB", status, message)

    @staticmethod
    def log_info(service: str, message: str):
        """Log an informational message."""
        HumanLogger._log(logging.INFO, service.upper(), "INFO", message)

    @staticmethod
    def log_warning(service: str, message: str):
        """Log a warning message."""
        HumanLogger._log(logging.WARNING, service.upper(), "WARNING", message)

    @staticmethod
    def log_error(service: str, message: str, exc_info=False):
        """Log an error message."""
        HumanLogger._log(logging.ERROR, service.upper(), "ERROR", message, exc_info=exc_info)

# Initialize the logger instance
human_logger = HumanLogger()
