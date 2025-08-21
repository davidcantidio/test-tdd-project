from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Protocol, Sequence, runtime_checkable


@dataclass(frozen=True)
class FileFinding:
    path: Path
    rule: str
    severity: str  # "LOW" | "MEDIUM" | "HIGH"
    message: str


@runtime_checkable
class Agent(Protocol):
    name: str

    def analyze(self, path: Path, content: str) -> List[FileFinding]: ...


@runtime_checkable
class FileRepository(Protocol):
    def scan(self, root: Path, patterns: Sequence[str]) -> List[Path]: ...
    def read_text(self, path: Path) -> str: ...
    def write_text(self, path: Path, data: str) -> None: ...


@runtime_checkable
class SessionRepository(Protocol):
    def start_run(self, root: Path) -> str: ...
    def save_findings(self, run_id: str, findings: List[FileFinding]) -> None: ...
    def end_run(self, run_id: str, status: str) -> None: ...


@runtime_checkable
class AuditPlanner(Protocol):
    def select_targets(self, candidates: Sequence[Path]) -> List[Path]: ...


@runtime_checkable
class Auditor(Protocol):
    def run(self, targets: Sequence[Path] | None = None) -> List[FileFinding]: ...
