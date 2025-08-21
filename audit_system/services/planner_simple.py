from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

from audit_system.core.contracts import AuditPlanner


class SimpleAuditPlanner(AuditPlanner):
    """
    Seleciona todos os candidatos por padrão.
    Pode evoluir para critérios (diffs recentes, tamanho, heurísticas AST, etc.).
    """
    def select_targets(self, candidates: Sequence[Path]) -> List[Path]:
        return list(candidates)
