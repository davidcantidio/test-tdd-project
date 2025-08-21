from __future__ import annotations

from pathlib import Path
from typing import List

from audit_system.core.contracts import Agent, FileFinding


class StaticRulesAgent(Agent):
    name = "static_rules"

    def analyze(self, path: Path, content: str) -> List[FileFinding]:
        findings: List[FileFinding] = []
        if "TODO" in content:
            findings.append(FileFinding(path, "TODO_PRESENT", "LOW", "Encontrado TODO no arquivo"))
        if len(content) > 200_000:
            findings.append(FileFinding(path, "FILE_TOO_LARGE", "MEDIUM", "Arquivo muito grande para análise eficiente"))
        return findings
