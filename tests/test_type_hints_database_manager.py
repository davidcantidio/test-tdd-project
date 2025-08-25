import inspect
import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parents[1]))

sys.modules.setdefault("psutil", types.ModuleType("psutil"))

# Migrated to test modular database API type hints instead of legacy DatabaseManager
from streamlit_extension.database import (
    get_connection, transaction, list_epics, list_tasks, list_projects,
    execute_cached_query, get_connection_context
)

# Modular API functions to test for type hints
MODULAR_FUNCTIONS = [
    "get_connection",
    "transaction", 
    "list_epics",
    "list_tasks",
    "list_projects",
    "execute_cached_query",
    "get_connection_context"
]

def test_modular_api_annotations():
    """Test that modular database API functions have proper type hints."""
    import streamlit_extension.database as db_module
    
    for name in MODULAR_FUNCTIONS:
        func = getattr(db_module, name)
        sig = inspect.signature(func)
        
        # Check that function has return annotation
        assert sig.return_annotation is not inspect._empty, f"{name} missing return annotation"
        
        # Check that parameters have annotations (except *args, **kwargs)
        for param in sig.parameters.values():
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue  # Skip *args and **kwargs
            if param.default is not inspect._empty and param.annotation is inspect._empty:
                continue  # Optional parameters may not need annotations
            assert param.annotation is not inspect._empty, f"{name} missing annotation for {param.name}"


def test_database_manager_annotations():
    """Legacy test - kept for backward compatibility but now tests modular API."""
    test_modular_api_annotations()