"""
Memory Provider Factory
=======================

Factory for creating different memory providers.
"""

from typing import Optional

from ..core import MemoryClient, MemoryConfig, IMemoryProvider


class MemoryProviderFactory:
    """Factory for creating memory providers."""
    
    @staticmethod
    def create_provider(
        provider_type: str,
        config: MemoryConfig,
        logger: Optional[callable] = None
    ) -> IMemoryProvider:
        """
        Create a memory provider based on type.
        
        Args:
            provider_type: Type of provider ("api", "local", etc.)
            config: Memory configuration
            logger: Optional logging function
            
        Returns:
            Memory provider instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        if provider_type == "api":
            return MemoryClient(config, logger)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    @staticmethod
    def get_supported_providers() -> list[str]:
        """
        Get list of supported provider types.
        
        Returns:
            List of supported provider type strings
        """
        return ["api"]
