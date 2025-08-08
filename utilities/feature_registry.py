"""
Feature Registry for Optional Dependencies
=========================================

Centralized tracking of optional feature availability with explicit logging
and health check capabilities. Replaces silent fallbacks with transparent
dependency management.

Usage:
    from utilities.feature_registry import feature_registry, check_feature
    
    if check_feature('pdf_processing'):
        # Use PDF processing
    
    # Get all feature status
    status = feature_registry.get_all_features()
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class FeatureStatus(Enum):
    AVAILABLE = "available"
    DISABLED = "disabled"
    ERROR = "error"

@dataclass
class FeatureInfo:
    """Information about a feature's availability."""
    name: str
    status: FeatureStatus
    error: Optional[str] = None
    description: str = ""

class FeatureRegistry:
    """Registry for tracking optional feature availability."""
    
    def __init__(self):
        self._features: Dict[str, FeatureInfo] = {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def register_feature(self, name: str, available: bool, 
                        error: Optional[str] = None, 
                        description: str = "") -> None:
        """Register a feature's availability status."""
        status = FeatureStatus.AVAILABLE if available else FeatureStatus.DISABLED
        if error and not available:
            status = FeatureStatus.ERROR
            
        self._features[name] = FeatureInfo(
            name=name,
            status=status,
            error=error,
            description=description
        )
        
        # Log feature status
        if available:
            self._logger.info(f"[OK] Feature '{name}' available: {description}")
        else:
            self._logger.warning(f"[WARN] Feature '{name}' disabled: {error or 'Not available'}")
    
    def is_available(self, name: str) -> bool:
        """Check if a feature is available."""
        feature = self._features.get(name)
        return feature is not None and feature.status == FeatureStatus.AVAILABLE
    
    def get_feature_info(self, name: str) -> Optional[FeatureInfo]:
        """Get detailed information about a feature."""
        return self._features.get(name)
    
    def get_all_features(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered features."""
        return {
            name: {
                "status": info.status.value,
                "error": info.error,
                "description": info.description
            }
            for name, info in self._features.items()
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for monitoring."""
        total = len(self._features)
        available = sum(1 for f in self._features.values() if f.status == FeatureStatus.AVAILABLE)
        disabled = sum(1 for f in self._features.values() if f.status == FeatureStatus.DISABLED)
        errors = sum(1 for f in self._features.values() if f.status == FeatureStatus.ERROR)
        
        return {
            "total_features": total,
            "available": available,
            "disabled": disabled,
            "errors": errors,
            "health_percentage": (available / total * 100) if total > 0 else 100
        }

# Global feature registry instance
feature_registry = FeatureRegistry()

def check_feature(name: str) -> bool:
    """Convenience function to check if a feature is available."""
    return feature_registry.is_available(name)

def register_import_attempt(feature_name: str, import_func, description: str = ""):
    """Helper to register an import attempt with proper logging."""
    try:
        import_func()
        feature_registry.register_feature(feature_name, True, description=description)
        return True
    except ImportError as e:
        feature_registry.register_feature(feature_name, False, str(e), description)
        return False
    except Exception as e:
        feature_registry.register_feature(feature_name, False, f"Unexpected error: {e}", description)
        return False
