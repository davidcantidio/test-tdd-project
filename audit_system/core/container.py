from __future__ import annotations

from pathlib import Path

from audit_system.agents.static_rules_agent import StaticRulesAgent
from audit_system.coordination.orchestrator import SystematicFileAuditOrchestrator
from audit_system.core.contracts import Auditor
from audit_system.services.file_repository import LocalFileRepository
from audit_system.services.planner_simple import SimpleAuditPlanner
from audit_system.services.session_sqlite import SQLiteSessionRepository


def build_default_auditor(project_root: Path, db_path: Path | None = None) -> Auditor:
    """
    Constrói um Auditor com implementações padrão (DI).
    """
    file_repo = LocalFileRepository(project_root)
    session_repo = SQLiteSessionRepository(db_path or (project_root / ".audit" / "audit_sessions.db"))
    planner = SimpleAuditPlanner()
    agents = [StaticRulesAgent()]
    return SystematicFileAuditOrchestrator(
        project_root=project_root,
        file_repo=file_repo,
        session_repo=session_repo,
        planner=planner,
        agents=agents,
    )
