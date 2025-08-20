# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole

#!/usr/bin/env python3
"""
🔗 API Package

API endpoints for TaskExecutionPlanner functionality integrated with Streamlit.
Uses query parameters approach to provide REST-like API without separate server.

This package provides:
- Task execution planning endpoints
- Epic dependency validation  
- Scoring system analysis
- API authentication and middleware
- Request logging and monitoring
"""

# Note: API endpoints are integrated into Streamlit via query parameters
# See streamlit_extension/endpoints/execution_api.py for implementation

__all__ = [
    # Main API entry point is in streamlit_extension/endpoints/execution_api.py
    # Usage: /?api=execution&epic_id=1&preset=balanced
]