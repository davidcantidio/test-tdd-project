"""
SQLite Epic Repository

Concrete repository for persisting Epic entities using SQLite.
Assumes framework_epics has explicit columns and uses a helper table
framework_epic_dependencies (epic_id INTEGER, depends_on_key TEXT)
to persist dependency keys.
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from ...domain.entities.epic import Epic
from ..mappers import EpicMapper


class EpicRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.conn = connection
        self.conn.row_factory = getattr(sqlite3, "Row")

    # ──────────────────────────────────────────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────────────────────────────────────────
    def create(self, epic: Epic) -> Epic:
        data = EpicMapper.to_db_fields(epic)
        excluded = {"id", "created_at", "updated_at", "started_at", "completed_at"}
        cols = [k for k in data.keys() if k not in excluded]
        placeholders = ", ".join(["?" for _ in cols])
        columns_sql = ", ".join(cols)
        values = [data[c] for c in cols]

        sql = f"INSERT INTO framework_epics ({columns_sql}) VALUES ({placeholders})"
        cur = self.conn.cursor()
        cur.execute(sql, values)
        new_id = cur.lastrowid
        self._persist_dependencies(new_id, epic.epic_dependencies)
        self.conn.commit()
        return self.get_by_id(new_id)  # type: ignore[return-value]

    def get_by_id(self, epic_id: int) -> Optional[Epic]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM framework_epics WHERE id = ?", (epic_id,))
        row = cur.fetchone()
        if not row:
            return None
        entity = EpicMapper.from_db_row(row)
        entity.epic_dependencies = self._load_dependencies(epic_id)
        return entity

    def update(self, epic: Epic) -> Epic:
        if epic.id is None:
            raise ValueError("Epic.id is required for update")
        data = EpicMapper.to_db_fields(epic)
        excluded = {"id", "project_id", "created_at", "started_at", "completed_at"}
        set_cols = [k for k in data.keys() if k not in excluded]
        assignments = ", ".join([f"{k} = ?" for k in set_cols])
        values = [data[c] for c in set_cols]
        values.append(epic.id)

        sql = f"UPDATE framework_epics SET {assignments} WHERE id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, values)
        # refresh dependencies
        self._persist_dependencies(epic.id, epic.epic_dependencies, replace=True)
        self.conn.commit()
        return self.get_by_id(epic.id)  # type: ignore[return-value]

    def delete(self, epic_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM framework_epic_dependencies WHERE epic_id = ?", (epic_id,))
        cur.execute("DELETE FROM framework_epics WHERE id = ?", (epic_id,))
        self.conn.commit()
        return cur.rowcount > 0

    # Queries auxiliares
    def list_by_product_vision_id(self, product_vision_id: int) -> List[Epic]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM framework_epics WHERE product_vision_id = ? ORDER BY id",
            (product_vision_id,),
        )
        rows = cur.fetchall()
        results: List[Epic] = []
        for r in rows:
            e = EpicMapper.from_db_row(r)
            e.epic_dependencies = self._load_dependencies(e.id) if e.id else []
            results.append(e)
        return results

    # ──────────────────────────────────────────────────────────────────────────
    # Dependencies helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _persist_dependencies(self, epic_id: int, deps: List[str], replace: bool = False) -> None:
        cur = self.conn.cursor()
        if replace:
            cur.execute("DELETE FROM framework_epic_dependencies WHERE epic_id = ?", (epic_id,))
        for key in deps or []:
            cur.execute(
                "INSERT INTO framework_epic_dependencies (epic_id, depends_on_key) VALUES (?, ?)",
                (epic_id, key),
            )

    def _load_dependencies(self, epic_id: int) -> List[str]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT depends_on_key FROM framework_epic_dependencies WHERE epic_id = ?",
            (epic_id,),
        )
        return [row[0] for row in cur.fetchall()]


__all__ = ["EpicRepository"]
