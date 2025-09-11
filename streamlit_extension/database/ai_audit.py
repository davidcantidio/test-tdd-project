"""
AI Audit helpers for epic ordering metadata persistence.

This module stores AI-related ordering context (model, version, explainer)
in the `framework_epic_ai_audit` table created by migration 013.

Usage:
    from streamlit_extension.database.ai_audit import log_epic_ai_ordering
    log_epic_ai_ordering(epic_id=1, project_id=2, model="gpt-5-nano", version="v1.2.3", explainer="ordered by score > ...")
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from .connection import execute


def log_epic_ai_ordering(
    epic_id: int,
    project_id: Optional[int] = None,
    model: Optional[str] = None,
    version: Optional[str] = None,
    explainer: Optional[str] = None,
) -> int:
    """Insert AI ordering audit record for a given epic.

    Returns the number of affected rows (1 on success).
    """
    sql = (
        "INSERT INTO framework_epic_ai_audit (epic_id, project_id, model, version, explainer)"
        " VALUES (?, ?, ?, ?, ?)"
    )
    return execute(sql, (epic_id, project_id, model, version, explainer))


def list_epic_ai_audit(epic_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """List recent AI audit records for an epic (most recent first)."""
    sql = (
        "SELECT id, epic_id, project_id, model, version, explainer, created_at"
        " FROM framework_epic_ai_audit WHERE epic_id = ?"
        " ORDER BY created_at DESC, id DESC LIMIT ?"
    )
    from .connection import execute as _exec  # local import to avoid cycles
    return _exec(sql, (epic_id, limit))  # type: ignore[return-value]

