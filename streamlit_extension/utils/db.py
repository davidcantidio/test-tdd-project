#!/usr/bin/env python3
"""
🔧 DB Utils - Database utility functions for repository layer

Re-exports commonly used database utilities from the main database module
to provide a clean interface for repository implementations.

This module specifically provides context managers and utilities needed
by the repository pattern implementation.
"""

from .database import dict_rows

__all__ = [
    'dict_rows'
]