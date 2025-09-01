"""
AI Refinement module for Product Vision.

This module provides unified access to AI-powered refinement services.
Automatically switches between Mock and Real AI based on environment configuration.
"""

from typing import Dict, Any
import logging

# Import service container for unified vision service
from .....services import get_service_container

# Legacy mock imports for backward compatibility
from .mock_refiner import (
    MockVisionRefineService,
    SingleFieldMockRefiner
)

logger = logging.getLogger(__name__)


def get_vision_service():
    """
    Get unified vision service from service container.
    
    Environment-aware factory that provides:
    - Mock service in development
    - Real AI service in production (with credentials)
    - Automatic fallback on failures
    
    Returns:
        UnifiedVisionService instance
    """
    try:
        container = get_service_container()
        service = container.get_vision_refine_service()
        logger.info(f"Vision service loaded: {service.service_type} (real_ai={service.is_using_real_ai})")
        return service
    except Exception as e:
        logger.error(f"Failed to get vision service from container: {e}")
        # Fallback to mock service
        logger.info("Falling back to MockVisionRefineService")
        return MockVisionRefineService()


# Main service interface - now uses unified service
VisionRefineService = get_vision_service


class UnifiedVisionRefineAdapter:
    """
    Adapter class for backward compatibility with existing wizard code.
    
    Provides the same interface as MockVisionRefineService but uses
    the unified service container underneath.
    """
    
    def __init__(self):
        self._service = get_vision_service()
    
    def refine(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Refine product vision data using unified service."""
        return self._service.refine(payload)
    
    @property
    def is_using_real_ai(self) -> bool:
        """Check if using real AI service."""
        return getattr(self._service, 'is_using_real_ai', False)
    
    @property
    def service_type(self) -> str:
        """Get service type name."""
        return getattr(self._service, 'service_type', 'MockVisionRefineService')


# Backward compatibility exports
__all__ = [
    'VisionRefineService',
    'UnifiedVisionRefineAdapter', 
    'get_vision_service',
    # Legacy exports
    'MockVisionRefineService',
    'SingleFieldMockRefiner'
]