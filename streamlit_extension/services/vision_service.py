"""
🤖 Vision Refine Service

Unified service for AI-powered product vision refinement.
Provides seamless switching between Mock and Real AI services based on environment.
"""

from typing import Protocol, Dict, Any, Union
import os
import logging
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


class VisionRefineProtocol(Protocol):
    """Protocol for vision refine services."""
    def refine(self, payload: Dict[str, Any]) -> Union[Dict[str, Any], 'ProductVisionDTO']: ...


class UnifiedVisionService:
    """
    Service that normalizes Mock and Real AI services for unified interface.
    
    Features:
    - Environment-based service selection (dev=mock, prod=real)
    - Automatic fallback to mock on AI failures
    - Consistent Dict[str, Any] return interface
    - Graceful error handling with logging
    """
    
    def __init__(self, use_real: bool = False, strict: bool = False):
        """
        Initialize vision service.
        
        Args:
            use_real: If True, use real AI service (requires credentials)
        """
        self._strict = bool(strict)
        self._use_real = use_real and self._has_credentials()
        self._is_real = self._use_real  # Initialize before _create_service
        self._service = self._create_service()
        
        logger.info(f"UnifiedVisionService initialized: {'Real AI' if self._is_real else 'Mock'}")
    
    def refine(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine product vision data.
        
        Unified interface that always returns Dict[str, Any] regardless of underlying service.
        
        Args:
            payload: Product vision data dict
            
        Returns:
            Dict with refined product vision data
            
        Raises:
            ValueError: If payload validation fails
        """
        try:
            result = self._service.refine(payload)
            
            # Convert ProductVisionDTO to Dict if needed
            if hasattr(result, 'dict'):
                return result.dict()
            elif isinstance(result, dict):
                return result
            else:
                # Fallback: convert any object to dict
                return {
                    'vision_statement': getattr(result, 'vision_statement', ''),
                    'problem_statement': getattr(result, 'problem_statement', ''),
                    'target_audience': getattr(result, 'target_audience', ''),
                    'value_proposition': getattr(result, 'value_proposition', ''),
                    'constraints': getattr(result, 'constraints', [])
                }
                
        except Exception as e:
            logger.error(f"Vision refinement failed with {type(self._service).__name__}: {e}")
            if self._is_real and self._strict:
                # Strict mode: do not fallback
                raise
            if self._is_real:
                # Non-strict: fallback to mock
                logger.info("Falling back to mock service due to AI failure")
                return self._fallback_to_mock(payload)
            # If already mock, re-raise
            raise
    
    def _create_service(self):
        """Create appropriate service based on configuration."""
        if self._is_real:
            try:
                from src.ia.product_vision_refiner import RealGPTRefiner
                return RealGPTRefiner()
            except ImportError as e:
                logger.warning(f"Failed to import Real AI service: {e}. Using mock.")
                self._is_real = False
                
        # Use mock service
        from src.ia.product_vision_refiner import FakeClaudeRefiner
        return FakeClaudeRefiner()
    
    def _has_credentials(self) -> bool:
        """Check if AI credentials are available."""
        return bool(os.getenv("OPENAI_API_KEY"))
    
    def _fallback_to_mock(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to mock service when real AI fails."""
        try:
            from src.ia.product_vision_refiner import FakeClaudeRefiner
            mock_service = FakeClaudeRefiner()
            result = mock_service.refine(payload)
            return result.dict() if hasattr(result, 'dict') else result
        except Exception as fallback_error:
            logger.error(f"Mock fallback also failed: {fallback_error}")
            # Return original payload as last resort
            return payload
    
    @property
    def is_using_real_ai(self) -> bool:
        """Check if service is using real AI."""
        return self._is_real
    
    @property 
    def service_type(self) -> str:
        """Get current service type name."""
        return type(self._service).__name__


def create_vision_service(strict: bool | None = None) -> UnifiedVisionService:
    """
    Factory function to create VisionService based on environment.
    
    Environment Logic:
    - Production + API Key → Real AI
    - Development OR No API Key → Mock
    
    Environment Variables:
    - TDD_ENVIRONMENT: "production" or "development"
    - OPENAI_API_KEY: Required for real AI
    
    Returns:
        UnifiedVisionService configured for current environment
    """
    environment = os.getenv("TDD_ENVIRONMENT", "development").lower()
    has_credentials = bool(os.getenv("OPENAI_API_KEY"))
    strict_mode = (
        (str(strict).lower() in ("true", "1", "yes", "on")) if strict is not None
        else os.getenv("TDD_REQUIRE_REAL_AI", "false").lower() in ("true", "1", "yes", "on")
    )

    if strict_mode and not has_credentials:
        raise RuntimeError("OPENAI_API_KEY required when TDD_REQUIRE_REAL_AI is enabled")

    use_real = strict_mode or (environment == "production" and has_credentials)

    logger.info(
        f"Creating vision service: env={environment}, has_creds={has_credentials}, use_real={use_real}, strict={strict_mode}"
    )
    
    return UnifiedVisionService(use_real=use_real, strict=strict_mode)


# Convenience functions for backward compatibility
def get_mock_vision_service() -> UnifiedVisionService:
    """Get mock vision service explicitly."""
    return UnifiedVisionService(use_real=False)


def get_real_vision_service() -> UnifiedVisionService:
    """
    Get real AI vision service explicitly.
    
    Raises:
        RuntimeError: If no API credentials available
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY required for real AI service")
    
    return UnifiedVisionService(use_real=True)
