"""
SQLite UserStory Repository

Concrete repository for persisting UserStory entities using SQLite.
Targets framework_user_stories table.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from ...domain.entities.user_story import UserStory
from ..mappers import UserStoryMapper


class UserStoryRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.conn = connection
        self.conn.row_factory = getattr(sqlite3, "Row")

    def create(self, us: UserStory) -> UserStory:
        data = UserStoryMapper.to_db_fields(us)
        excluded = {"id", "created_at", "updated_at"}
        cols = [k for k in data.keys() if k not in excluded]
        placeholders = ", ".join(["?" for _ in cols])
        columns_sql = ", ".join(cols)
        values = [data[c] for c in cols]

        sql = f"INSERT INTO framework_user_stories ({columns_sql}) VALUES ({placeholders})"
        cur = self.conn.cursor()
        cur.execute(sql, values)
        new_id = cur.lastrowid
        self.conn.commit()
        return self.get_by_id(new_id)  # type: ignore[return-value]

    def get_by_id(self, us_id: int) -> Optional[UserStory]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM framework_user_stories WHERE id = ?", (us_id,))
        row = cur.fetchone()
        if not row:
            return None
        return UserStoryMapper.from_db_row(row)

    def update(self, us: UserStory) -> UserStory:
        if us.id is None:
            raise ValueError("UserStory.id is required for update")
        data = UserStoryMapper.to_db_fields(us)
        excluded = {"id", "epic_id", "created_at", "updated_at"}
        set_cols = [k for k in data.keys() if k not in excluded]
        assignments = ", ".join([f"{k} = ?" for k in set_cols])
        values = [data[c] for c in set_cols]
        values.append(us.id)

        sql = f"UPDATE framework_user_stories SET {assignments} WHERE id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, values)
        self.conn.commit()
        return self.get_by_id(us.id)  # type: ignore[return-value]

    def delete(self, us_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM framework_user_stories WHERE id = ?", (us_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def list_by_epic_id(self, epic_id: int):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM framework_user_stories WHERE epic_id = ? ORDER BY id",
            (epic_id,),
        )
        return [UserStoryMapper.from_db_row(r) for r in cur.fetchall()]


__all__ = ["UserStoryRepository"]
