from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Protocol, Sequence


@dataclass(frozen=True)
class AgentRecommendation:
    name: str
    priority: int = 0


@dataclass(frozen=True)
class FileAnalysisResult:
    file_path: Path
    issues_found: int
    notes: str = ""


class Agent(Protocol):
    """Minimal contract expected from an analysis/refactoring agent."""
    name: str

    def analyze_file(self, file_path: Path) -> FileAnalysisResult: ...

    def can_apply(self, file_path: Path) -> bool: ...


class Auditor(Protocol):
    """High-level orchestration/auditor interface."""
    def plan_for(self, file_path: Path) -> Sequence[AgentRecommendation]: ...

    def execute_plan(self, file_path: Path, agents: Iterable[Agent]) -> List[FileAnalysisResult]: ...
