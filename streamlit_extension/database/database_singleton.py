"""
🗄️ Database Singleton Manager

Centralized DatabaseManager singleton to eliminate semantic duplication.
Replaces 5 duplicate _db() implementations across database modules.

CONSOLIDATION: Eliminates semantic duplication found in deep audit:
- seed.py:22 - _db() implementation  
- schema.py:45 - _db() implementation
- health.py:42 - _db() implementation
- queries.py:13 - _db() implementation
- connection.py:76 - _db() implementation
"""

from typing import Optional
import threading

# Import DatabaseManager
from ..utils.database import DatabaseManager
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


# Global singleton instance
_DBM_INSTANCE: Optional[DatabaseManager] = None
_DBM_LOCK = threading.RLock()  # Reentrant lock for thread safety

def get_database_manager() -> DatabaseManager:
    """
    Thread-safe singleton DatabaseManager (double-checked locking).
    
    CANONICAL IMPLEMENTATION - replaces all duplicate _db() functions.
    
    Returns:
        DatabaseManager: Singleton instance
        
    Thread Safety:
        Uses double-checked locking pattern for optimal performance
    """
    global _DBM_INSTANCE
    
    # First check (without lock for performance)
    if _DBM_INSTANCE is not None:
        return _DBM_INSTANCE
    
    # Second check (with lock for thread safety) 
    with _DBM_LOCK:
        if _DBM_INSTANCE is None:
            _DBM_INSTANCE = DatabaseManager()
        return _DBM_INSTANCE

def reset_database_manager() -> None:
    """
    Reset singleton instance (useful for testing).
    
    Thread Safety:
        Properly synchronized with main singleton
    """
    global _DBM_INSTANCE
    with _DBM_LOCK:
        if _DBM_INSTANCE is not None:
            try:
                _DBM_INSTANCE.close()  # Clean up existing instance
            except Exception:
                pass  # Ignore cleanup errors
        _DBM_INSTANCE = None

# Backward compatibility alias
_db = get_database_manager

# Export main functions
__all__ = ['get_database_manager', 'reset_database_manager', '_db']