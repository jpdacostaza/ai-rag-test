"""
Enhanced logging configuration for human-readable logs
Provides colored, structured, and user-friendly logging output
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and emojis for better readability"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m',     # Reset
        'BOLD': '\033[1m',      # Bold
        'DIM': '\033[2m',       # Dim
    }
    
    # Emojis for log levels
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨',
    }
    
    # Service icons
    SERVICE_ICONS = {
        'REDIS': '🔴',
        'CHROMADB': '🟣',
        'OLLAMA': '🤖',
        'DATABASE': '💾',
        'API': '🚀',
        'HEALTH': '🏥',
        'MEMORY': '🧠',
        'CHAT': '💬',
        'TOOLS': '🔧',
        'WATCHDOG': '👀',
        'STARTUP': '🏁',
        'CACHE': '⚡',
        'ERROR': '💥',
        'NETWORK': '🌐',
    }
    
    def format(self, record):
        # Get color and emoji for log level
        level_color = self.COLORS.get(record.levelname, '')
        emoji = self.EMOJIS.get(record.levelname, '📝')
        reset = self.COLORS['RESET']
        bold = self.COLORS['BOLD']
        dim = self.COLORS['DIM']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Extract service name from message if present
        service_icon = ''
        message = record.getMessage()
        
        # Look for service indicators in brackets like [REDIS], [CHROMADB], etc.
        for service, icon in self.SERVICE_ICONS.items():
            if f'[{service}]' in message:
                service_icon = f'{icon} '
                # Remove the bracket notation from message for cleaner output
                message = message.replace(f'[{service}] ', '')
                break
        
        # Format the log level name
        level_name = f"{level_color}{bold}{record.levelname:<8}{reset}"
        
        # Create the formatted message
        if record.levelname in ['ERROR', 'CRITICAL']:
            # For errors, make them more prominent
            formatted_message = f"{emoji} {bold}{level_color}{timestamp}{reset} │ {level_name} │ {service_icon}{bold}{message}{reset}"
        elif record.levelname == 'WARNING':
            # For warnings, use a softer approach
            formatted_message = f"{emoji} {level_color}{timestamp}{reset} │ {level_name} │ {service_icon}{message}"
        elif record.levelname == 'INFO':
            # For info, clean and simple
            formatted_message = f"{emoji} {timestamp} │ {level_name} │ {service_icon}{message}"
        else:  # DEBUG
            # For debug, make it dimmer
            formatted_message = f"{emoji} {dim}{timestamp} │ {level_name} │ {service_icon}{message}{reset}"
        
        return formatted_message

class HumanLogger:
    """Enhanced logger setup for human-readable output"""
    
    @staticmethod
    def setup(level: str = "INFO", enable_colors: bool = True) -> logging.Logger:
        """
        Set up human-readable logging
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_colors: Whether to use colored output
        """
        
        # Convert string level to logging constant
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        
        # Create root logger
        logger = logging.getLogger()
        logger.setLevel(numeric_level)
        
        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        # Use colored formatter if colors are enabled and we're in a terminal
        if enable_colors and sys.stdout.isatty():
            formatter = ColoredFormatter()
        else:
            # Fallback to simple format for non-terminal environments
            formatter = logging.Formatter(
                '%(asctime)s │ %(levelname)-8s │ %(message)s',
                datefmt='%H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    @staticmethod
    def log_startup_banner():
        """Log a nice startup banner"""
        logger = logging.getLogger()
        logger.info("🚀 FastAPI LLM Backend Starting...")
        logger.info("🔧 Initializing services...")
    
    @staticmethod
    def log_service_status(service: str, status: str, details: str = ""):
        """Log service status in a consistent format"""
        logger = logging.getLogger()
        status_icons = {
            'starting': '🟡',
            'ready': '✅',
            'degraded': '⚠️',
            'failed': '❌',
            'connecting': '🔗',
            'reconnecting': '🔄'
        }
        
        icon = status_icons.get(status.lower(), '📝')
        message = f"[{service.upper()}] {icon} {status.title()}"
        if details:
            message += f" - {details}"
        
        if status.lower() in ['failed', 'error']:
            logger.error(message)
        elif status.lower() in ['degraded', 'warning']:
            logger.warning(message)
        else:
            logger.info(message)
    
    @staticmethod
    def log_health_check(service: str, healthy: bool, response_time: Optional[float] = None):
        """Log health check results"""
        logger = logging.getLogger()
        status = "✅ Healthy" if healthy else "❌ Unhealthy"
        timing = f" ({response_time:.2f}ms)" if response_time else ""
        logger.info(f"[HEALTH] {service}: {status}{timing}")

# Convenience functions for common log patterns
def log_redis_status(status: str, details: str = ""):
    """Log Redis-specific status"""
    HumanLogger.log_service_status("REDIS", status, details)

def log_chromadb_status(status: str, details: str = ""):
    """Log ChromaDB-specific status"""
    HumanLogger.log_service_status("CHROMADB", status, details)

def log_api_request(method: str, endpoint: str, status_code: int, response_time: float):
    """Log API requests in a readable format"""
    logger = logging.getLogger()
    status_emoji = "✅" if status_code < 400 else "❌" if status_code >= 500 else "⚠️"
    logger.info(f"[API] {status_emoji} {method} {endpoint} → {status_code} ({response_time:.2f}ms)")

def log_chat_interaction(user_id: str, message_length: int, response_length: int, tools_used: Optional[list] = None):
    """Log chat interactions"""
    logger = logging.getLogger()
    tools_info = f" (tools: {', '.join(tools_used)})" if tools_used else ""
    logger.info(f"[CHAT] 💬 User {user_id}: {message_length} chars → {response_length} chars{tools_info}")

def log_error_with_context(error: Exception, context: str = ""):
    """Log errors with helpful context"""
    logger = logging.getLogger()
    error_msg = f"[ERROR] 💥 {type(error).__name__}: {str(error)}"
    if context:
        error_msg += f" (Context: {context})"
    logger.error(error_msg)

# Initialize logging when module is imported
def init_logging(level: Optional[str] = None, enable_colors: bool = True):
    """Initialize the enhanced logging system"""
    # Get log level from environment or use default
    log_level = level or os.getenv('LOG_LEVEL', 'INFO')
    
    # Setup the logger
    HumanLogger.setup(log_level, enable_colors)
    
    # Log the initialization
    logger = logging.getLogger()
    logger.info("🎨 Enhanced logging initialized")
    logger.debug(f"🔧 Log level set to: {log_level}")
