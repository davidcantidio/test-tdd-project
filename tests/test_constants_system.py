import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parents[1]))

sys.modules.setdefault("psutil", types.ModuleType("psutil"))

from streamlit_extension.utils.constants import (
    TableNames,
    FieldNames,
    ClientStatus,
    ProjectStatus,
    TaskStatus,
    EpicStatus,
    TDDPhase,
    Priority,
    Complexity,
)

def test_table_constants():
    assert TableNames.CLIENTS == "framework_clients"
    assert TableNames.PROJECTS == "framework_projects"
    assert FieldNames.STATUS == "status"


def test_enum_values():
    assert ClientStatus.ACTIVE.value == "active"
    assert ProjectStatus.PLANNING.value == "planning"
    assert TaskStatus.TODO.value == "todo"
    assert EpicStatus.DRAFT.value == "draft"
    assert TDDPhase.RED.value == "red"


def test_int_enums():
    assert Priority.HIGH == 3
    assert Complexity.COMPLEX == 4