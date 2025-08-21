from __future__ import annotations

import sqlite3
from pathlib import Path

from audit_system.core.contracts import FileFinding
from audit_system.services.session_sqlite import SQLiteSessionRepository


def test_sqlite_wal_enabled(tmp_path: Path):
    db = tmp_path / "audit.db"
    repo = SQLiteSessionRepository(db)
    # validate WAL
    conn = sqlite3.connect(db)
    try:
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    finally:
        conn.close()
    assert mode.lower() == "wal"


def test_save_and_end_run(tmp_path: Path):
    db = tmp_path / "audit.db"
    repo = SQLiteSessionRepository(db)
    run_id = repo.start_run(tmp_path)
    repo.save_findings(run_id, [FileFinding(tmp_path / "f.py", "RULE", "LOW", "ok")])
    repo.end_run(run_id, "OK")
