from __future__ import annotations

import io
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional


class PathSecurityError(Exception):
    """Raised when a path validation fails (possible path traversal or outside base)."""


def safe_join(base_dir: Path | str, candidate: Path | str) -> Path:
    """
    Join and normalize ensuring the resulting path stays inside base_dir.
    Prevents path traversal attacks (e.g., '../../etc/passwd').
    """
    base = Path(base_dir).resolve()
    target = (base / candidate).resolve()
    if base not in target.parents and target != base:
        raise PathSecurityError(f"Unsafe path outside base: {target} (base={base})")
    return target


def assert_within_base(base_dir: Path | str, candidate: Path | str) -> None:
    """Raise if candidate is not inside base_dir after resolution."""
    _ = safe_join(base_dir, candidate)


@contextmanager
def safe_open(
    base_dir: Path | str,
    candidate: Path | str,
    mode: str = "r",
    encoding: Optional[str] = "utf-8",
) -> Iterator[io.TextIOBase | io.BufferedIOBase]:
    """
    Open a file validating it resides under base_dir.
    - For text modes ('t' or default), returns a text IO with utf-8 by default.
    - For binary modes ('b'), returns a buffered binary IO.
    """
    path = safe_join(base_dir, candidate)
    is_binary = "b" in mode
    if is_binary:
        f = open(path, mode)  # noqa: P201  (path is validated by safe_join)
    else:
        f = open(path, mode, encoding=encoding)  # noqa: P201
    try:
        yield f
    finally:
        try:
            f.close()
        except Exception:
            pass


@dataclass(frozen=True)
class AtomicWriteResult:
    path: Path
    bytes_written: int
    backup_path: Optional[Path] = None


def _fsync_directory(path: Path) -> None:
    """Ensure directory entry is flushed to disk (best-effort; not all FS support)."""
    try:
        dir_fd = os.open(str(path), os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        pass


def atomic_write(
    base_dir: Path | str,
    candidate: Path | str,
    data: bytes | str,
    *,
    encoding: Optional[str] = "utf-8",
    create_backup: bool = True,
) -> AtomicWriteResult:
    """
    Atomically write content to a validated path:
    - write to temporary file in the same directory
    - fsync temp file
    - optional backup of original file
    - atomic rename over the destination
    """
    dest = safe_join(base_dir, candidate)
    dest.parent.mkdir(parents=True, exist_ok=True)

    backup_path: Optional[Path] = None
    if create_backup and dest.exists():
        backup_path = dest.with_suffix(dest.suffix + ".bak")
        try:
            if backup_path.exists():
                backup_path.unlink()
            dest.replace(backup_path)
        except Exception:
            backup_path = None

    fd, tmp_name = tempfile.mkstemp(prefix=f".{dest.name}.tmp-", dir=str(dest.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as tmp:
            if isinstance(data, str):
                tmp.write(data.encode(encoding or "utf-8"))
            else:
                tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
        tmp_path.replace(dest)
        _fsync_directory(dest.parent)
        byte_len = len(data if isinstance(data, (bytes, bytearray)) else data.encode(encoding or "utf-8"))
        return AtomicWriteResult(path=dest, bytes_written=byte_len, backup_path=backup_path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
