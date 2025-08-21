from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import List

from audit_system.core.contracts import FileFinding, SessionRepository


class SQLiteSessionRepository(SessionRepository):
    """
    Repositório simples com WAL + foreign_keys e binds parametrizados.
    """
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0, isolation_level=None)
        # Segurança/confiabilidade
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS audit_runs (
                id TEXT PRIMARY KEY,
                root TEXT NOT NULL,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                finished_at DATETIME,
                status TEXT
            );
            """
            )
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS audit_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                path TEXT NOT NULL,
                rule TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES audit_runs(id) ON DELETE CASCADE
            );
            """
            )
        finally:
            conn.close()

    def start_run(self, root: Path) -> str:
        run_id = str(uuid.uuid4())
        conn = self._connect()
        try:
            conn.execute("INSERT INTO audit_runs (id, root, status) VALUES (?, ?, ?);", (run_id, str(root), "RUNNING"))
        finally:
            conn.close()
        return run_id

    def save_findings(self, run_id: str, findings: List[FileFinding]) -> None:
        if not findings:
            return
        conn = self._connect()
        try:
            conn.executemany(
                "INSERT INTO audit_findings (run_id, path, rule, severity, message) VALUES (?, ?, ?, ?, ?);",
                [(run_id, str(f.path), f.rule, f.severity, f.message) for f in findings],
            )
        finally:
            conn.close()

    def end_run(self, run_id: str, status: str) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE audit_runs SET status = ?, finished_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (status, run_id),
            )
        finally:
            conn.close()
