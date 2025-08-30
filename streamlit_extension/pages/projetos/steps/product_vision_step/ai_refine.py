"""
AI Refinement module for Product Vision.

This module handles AI-powered refinement of Product Vision fields.
Currently using mock implementation until Phase 5.1.
"""

from .mock_refiner import (
    MockVisionRefineService,
    SingleFieldMockRefiner
)

# Export the main service class
VisionRefineService = MockVisionRefineService

__all__ = [
    'VisionRefineService',
    'MockVisionRefineService',
    'SingleFieldMockRefiner'
]