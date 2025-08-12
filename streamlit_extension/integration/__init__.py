"""
🔗 Integration Package for Streamlit Extension

Provides seamless integration with existing TDD Framework components:
- Epic JSON synchronization
- Analytics engine compatibility
- Gantt tracker integration
- Timer database bidirectional sync
"""

try:
    from .existing_system import (
        ExistingSystemIntegrator,
        quick_sync_epics_json_to_db,
        quick_health_check,
        check_integration_availability
    )
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False
    ExistingSystemIntegrator = None
    quick_sync_epics_json_to_db = quick_health_check = check_integration_availability = None

__version__ = "1.0.0"
__all__ = [
    "ExistingSystemIntegrator",
    "quick_sync_epics_json_to_db", 
    "quick_health_check",
    "check_integration_availability",
    "INTEGRATION_AVAILABLE"
]
