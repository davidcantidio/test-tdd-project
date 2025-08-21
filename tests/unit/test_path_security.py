from __future__ import annotations

from pathlib import Path

import pytest
import sys, types, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.modules.setdefault("streamlit", types.ModuleType("streamlit"))

from audit_system.utils.path_security import (
    PathSecurityError,
    atomic_write,
    safe_join,
    safe_open,
)


def test_safe_join_blocks_traversal(tmp_path: Path) -> None:
    base = tmp_path / "project"
    base.mkdir()
    with pytest.raises(PathSecurityError):
        _ = safe_join(base, "../outside.txt")


def test_safe_open_write_and_read(tmp_path: Path) -> None:
    base = tmp_path / "pj"
    base.mkdir()
    with safe_open(base, "foo.txt", "w") as f:
        f.write("hello")
    with safe_open(base, "foo.txt", "r") as f:
        assert f.read() == "hello"


def test_atomic_write_creates_backup(tmp_path: Path) -> None:
    base = tmp_path
    res1 = atomic_write(base, "a.txt", "v1")
    assert (base / "a.txt").read_text() == "v1"
    assert res1.backup_path is None
    res2 = atomic_write(base, "a.txt", "v2", create_backup=True)
    assert (base / "a.txt").read_text() == "v2"
    assert res2.backup_path is not None
    assert res2.backup_path.exists()
    assert res2.backup_path.read_text() == "v1"
