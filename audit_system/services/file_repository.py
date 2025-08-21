from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

from audit_system.core.contracts import FileRepository
from audit_system.utils.safe_io import read_text_secure, write_text_atomic_secure, safe_join


class LocalFileRepository(FileRepository):
    def __init__(self, project_root: Path) -> None:
        self.root = project_root

    def scan(self, root: Path, patterns: Sequence[str]) -> List[Path]:
        base = root.resolve()
        results: List[Path] = []
        for pat in patterns:
            # aceita "**/*.py", etc.
            for p in base.glob(pat):
                rp = safe_join(self.root, p)
                if rp.is_file():
                    results.append(rp)
        return sorted(set(results))

    def read_text(self, path: Path) -> str:
        return read_text_secure(self.root, path)

    def write_text(self, path: Path, data: str) -> None:
        write_text_atomic_secure(self.root, path, data)
