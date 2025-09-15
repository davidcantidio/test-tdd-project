"""
SQLite Task Repository

Concrete repository for persisting Task entities using SQLite.
Assumes framework_tasks has standard columns (task_key, title, tdd_phase, etc.).
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from ...domain.entities.task import Task
from ..mappers import TaskMapper


class TaskRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.conn = connection
        self.conn.row_factory = getattr(sqlite3, "Row")

    def create(self, task: Task) -> Task:
        data = TaskMapper.to_db_fields(task)
        excluded = {"id", "created_at", "updated_at"}
        cols = [k for k in data.keys() if k not in excluded]
        placeholders = ", ".join(["?" for _ in cols])
        columns_sql = ", ".join(cols)
        values = [data[c] for c in cols]

        sql = f"INSERT INTO framework_tasks ({columns_sql}) VALUES ({placeholders})"
        cur = self.conn.cursor()
        cur.execute(sql, values)
        new_id = cur.lastrowid
        self.conn.commit()
        return self.get_by_id(new_id)  # type: ignore[return-value]

    def get_by_id(self, task_id: int) -> Optional[Task]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM framework_tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if not row:
            return None
        return TaskMapper.from_db_row(row)

    def update(self, task: Task) -> Task:
        if task.id is None:
            raise ValueError("Task.id is required for update")

        data = TaskMapper.to_db_fields(task)
        excluded = {"id", "epic_id", "created_at", "updated_at"}
        set_cols = [k for k in data.keys() if k not in excluded]
        assignments = ", ".join([f"{k} = ?" for k in set_cols])
        values = [data[c] for c in set_cols]
        values.append(task.id)

        sql = f"UPDATE framework_tasks SET {assignments} WHERE id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, values)
        self.conn.commit()
        return self.get_by_id(task.id)  # type: ignore[return-value]

    def delete(self, task_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM framework_tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def list_by_user_story_id(self, user_story_id: int):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM framework_tasks WHERE user_story_id = ? ORDER BY id",
            (user_story_id,),
        )
        return [TaskMapper.from_db_row(r) for r in cur.fetchall()]


__all__ = ["TaskRepository"]
