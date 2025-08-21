from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Union


class PathSecurityError(Exception):
    pass


def safe_join(base: Path, candidate: Path) -> Path:
    base_r = base.resolve()
    cand_r = (base / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    if not str(cand_r).startswith(str(base_r) + os.sep) and cand_r != base_r:
        raise PathSecurityError(f"Traversal detected: {cand_r} not under {base_r}")
    return cand_r


def read_text_secure(base: Path, target: Union[str, Path], encoding: str = "utf-8") -> str:
    p = safe_join(base, Path(target))
    return p.read_text(encoding=encoding)


def write_text_atomic_secure(
    base: Path,
    target: Union[str, Path],
    data: str,
    encoding: str = "utf-8",
) -> None:
    dest = safe_join(base, Path(target))
    dest.parent.mkdir(parents=True, exist_ok=True)
    # escreve em tmp no MESMO dir p/ atomic rename
    with tempfile.NamedTemporaryFile("w", encoding=encoding, dir=str(dest.parent), delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    tmp_path.replace(dest)
