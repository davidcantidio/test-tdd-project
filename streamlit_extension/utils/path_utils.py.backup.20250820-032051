"""
📁 Project Path Utilities

Project path management and Python path manipulation helpers.
Extracted from streamlit_helpers.py for better modularity.
"""

from __future__ import annotations

from typing import Union
from pathlib import Path
import sys
import logging
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole

logger = logging.getLogger(__name__)

# === PROJECT PATH HELPERS =================================================

def get_project_root() -> Path:
    """
    Get project root directory path.
    
    Returns:
        Path to project root directory
    """
    # Get the path of this file and go up to project root
    current_file = Path(__file__)
    
    # Go up from utils -> streamlit_extension -> project_root
    project_root = current_file.parent.parent.parent
    
    return project_root.resolve()

def add_project_to_path() -> None:
    """Add project root to Python path if not already present."""
    project_root = str(get_project_root())
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.info(f"Added project root to Python path: {project_root}")

def get_relative_path(file_path: Union[str, Path]) -> Path:
    """
    Get path relative to project root.
    
    Args:
        file_path: File path to make relative
        
    Returns:
        Path relative to project root
    """
    project_root = get_project_root()
    file_path = Path(file_path)
    
    try:
        return file_path.relative_to(project_root)
    except ValueError:
        # Path is not relative to project root
        return file_path

# === EXPORTS ==============================================================

__all__ = [
    # Project path helpers
    "get_project_root",
    "add_project_to_path",
    "get_relative_path",
]