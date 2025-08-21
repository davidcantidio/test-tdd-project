from __future__ import annotations

from pathlib import Path

import pytest

from audit_system.utils.safe_io import safe_join, PathSecurityError, write_text_atomic_secure, read_text_secure


def test_safe_join_blocks_traversal(tmp_path: Path):
    base = tmp_path / "root"
    base.mkdir()
    outside = Path("..") / "evil.txt"
    with pytest.raises(PathSecurityError):
        safe_join(base, outside)


def test_atomic_write_and_read(tmp_path: Path):
    base = tmp_path / "root"
    base.mkdir()
    rel = Path("a.txt")
    write_text_atomic_secure(base, rel, "hello")
    assert read_text_secure(base, rel) == "hello"
