import inspect
import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parents[1]))

sys.modules.setdefault("psutil", types.ModuleType("psutil"))

from streamlit_extension.utils.database import DatabaseManager

METHODS = [
    "get_connection",
    "execute_query",
    "get_projects",
    "create_project",
    "update_project",
    "delete_project",
    "get_epics",
    "get_tasks",
]

def test_database_manager_annotations():
    for name in METHODS:
        func = getattr(DatabaseManager, name)
        sig = inspect.signature(func)
        assert sig.return_annotation is not inspect._empty, f"{name} missing return annotation"
        for param in sig.parameters.values():
            if param.name == "self":
                continue
            assert param.annotation is not inspect._empty, f"{name} missing annotation for {param.name}"