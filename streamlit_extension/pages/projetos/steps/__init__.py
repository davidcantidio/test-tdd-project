# streamlit_extension/pages/projetos/steps/__init__.py
"""
📄 UI Steps Package - Wizard Step Components

This package contains Streamlit-specific UI components that implement
individual steps in the Project Wizard workflow. Each step is responsible
for rendering UI elements, handling user interaction, and coordinating
with the controller layer for business operations.

Step Component Responsibilities:
    - User interface rendering with Streamlit components
    - User input collection and basic validation
    - UI state management and user experience flow
    - Integration with controller layer for business operations
    - Error message display and user feedback

UI Design Principles:
    - Progressive disclosure of information
    - Clear visual feedback for user actions
    - Accessibility and usability considerations
    - Responsive design for different screen sizes
    - Intuitive navigation between steps

Available Steps:
    - ProductVisionStep: 
        * Collects Product Vision information from user
        * Integrates with AI refinement services
        * Provides real-time validation feedback
        * Supports draft saving and loading

Step Workflow:
    User Input → UI Validation → Controller Coordination → Business Logic
    
    Steps focus on UI concerns while delegating business logic to controllers
    and domain services.

Usage Example:
    >>> from .product_vision_step import render_product_vision_step
    >>> # In Streamlit app context
    >>> result = render_product_vision_step(current_data, on_save=save_handler)
    >>> if result.completed:
    ...     # Move to next step

Architecture Notes:
    Steps are the only layer that should import Streamlit components.
    All business logic should be delegated to controllers, maintaining
    clean separation between UI and business concerns.
"""

# Import step modules for external access
from . import product_vision_step
from . import capitulos_step

__all__ = ['product_vision_step', 'capitulos_step']