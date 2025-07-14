"""
DEPRECATED: This module has been replaced by core.logging_config
This file provides backward compatibility by redirecting to the unified logging system.
"""

import warnings
from core.logging_config import get_logger, setup_logging

# Issue deprecation warning
warnings.warn(
    "utilities.structured_logging is deprecated. Use core.logging_config instead.",
    DeprecationWarning,
    stacklevel=2
)

# Backward compatibility functions
def get_structured_logger(name):
    """DEPRECATED: Use core.logging_config.get_logger instead"""
    return get_logger(name)

def log_function_call(*args, **kwargs):
    """DEPRECATED: Use standard logger.info instead"""
    pass

def log_performance(*args, **kwargs):
    """DEPRECATED: Use standard logger.info instead"""
    pass

def set_correlation_id(*args, **kwargs):
    """DEPRECATED: Use standard logging context instead"""
    pass

# Initialize unified logging on import
setup_logging()
