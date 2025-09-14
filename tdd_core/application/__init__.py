"""
Application Layer - Use Cases and Orchestration

This layer coordinates domain objects to implement use cases.
It defines interfaces that infrastructure implementations will fulfill.

Components (to be implemented in future stories):
    - services: Application services that orchestrate domain logic (História 2.x)
    - dto: Data Transfer Objects for external communication (História 4.x)
    - validators: Input validation and business rule enforcement
    - use_cases: Specific business scenarios and workflows

Principles:
    - Orchestrates domain objects
    - Defines infrastructure interfaces  
    - Stateless operations
    - Framework independent
    - Dependency inversion

Dependencies: domain layer only

Status: História 1.1 - Structure Ready
Next: História 2.1 - VisionService Migration
"""

# Future imports (to be populated in História 2.x-4.x)
# from .services import VisionService, EpicService, AIService
# from .dto import ProductVisionDTO, EpicSuggestionDTO
# from .validators import ProductVisionValidator, EpicValidator
# from .use_cases import CreateProjectWizard, GenerateEpicsFromVision

__all__: list[str] = []  # Will be populated in História 2.x-4.x

# Layer metadata
LAYER_INFO = {
    "name": "application",
    "description": "Use cases and orchestration layer",
    "dependencies": ["domain"],  # Only depends on domain layer
    "principles": ["Clean Architecture", "Dependency Inversion", "Stateless"],
    "status": "História 1.1 Complete - Structure Ready",
}
