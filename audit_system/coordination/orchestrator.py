from __future__ import annotations

from pathlib import Path
from typing import Sequence, List

from audit_system.core.contracts import (
    AuditPlanner,
    Auditor,
    FileFinding,
    FileRepository,
    SessionRepository,
    Agent,
)
from audit_system.utils.resilience import retry


class SystematicFileAuditOrchestrator(Auditor):
    """
    Classe fina que apenas coordena serviços especializados (SRP).
    """
    def __init__(
        self,
        project_root: Path,
        file_repo: FileRepository,
        session_repo: SessionRepository,
        planner: AuditPlanner,
        agents: Sequence[Agent],
    ) -> None:
        self.root = project_root
        self.file_repo = file_repo
        self.session_repo = session_repo
        self.planner = planner
        self.agents = list(agents)

    def _scan_candidates(self) -> List[Path]:
        return self.file_repo.scan(self.root, patterns=["**/*.py"])

    @retry((Exception,), attempts=3, base_delay=0.2, max_delay=1.0)
    def _analyze_with_agent(self, agent: Agent, path: Path, content: str) -> List[FileFinding]:
        return agent.analyze(path, content)

    def run(self, targets: Sequence[Path] | None = None) -> List[FileFinding]:
        run_id = self.session_repo.start_run(self.root)
        try:
            candidates = list(targets) if targets else self._scan_candidates()
            selected = self.planner.select_targets(candidates)
            all_findings: List[FileFinding] = []
            for p in selected:
                content = self.file_repo.read_text(p)
                for agent in self.agents:
                    findings = self._analyze_with_agent(agent, p, content)
                    if findings:
                        self.session_repo.save_findings(run_id, findings)
                        all_findings.extend(findings)
            self.session_repo.end_run(run_id, "OK")
            return all_findings
        except Exception:
            self.session_repo.end_run(run_id, "FAILED")
            raise
