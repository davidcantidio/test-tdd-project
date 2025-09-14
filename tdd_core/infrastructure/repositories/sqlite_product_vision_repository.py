"""
SQLite ProductVision Repository

Concrete repository for persisting ProductVision entities using SQLite.
Depends on migration 012 (explicit product_visions columns).
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from ...domain.entities.product_vision import ProductVision
from ..mappers import ProductVisionMapper


class ProductVisionRepository:
    """SQLite repository for ProductVision.

    Notes:
        - Foreign keys must be enabled in the connection if enforced.
        - Caller is responsible for providing a valid project_id on create.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.conn = connection
        self.conn.row_factory = getattr(sqlite3, "Row")

    def create(self, project_id: int, vision: ProductVision) -> ProductVision:
        data = ProductVisionMapper.to_db_fields(vision)
        data["project_id"] = project_id

        # Exclude non-insert fields
        excluded = {"id", "created_at", "updated_at"}
        cols = [k for k in data.keys() if k not in excluded]
        placeholders = ", ".join(["?" for _ in cols])
        columns_sql = ", ".join(cols)
        values = [data[c] for c in cols]

        sql = f"INSERT INTO product_visions ({columns_sql}) VALUES ({placeholders})"
        cur = self.conn.cursor()
        cur.execute(sql, values)
        new_id = cur.lastrowid
        self.conn.commit()

        return self.get_by_id(new_id)  # type: ignore[return-value]

    def get_by_id(self, vision_id: int) -> Optional[ProductVision]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM product_visions WHERE id = ?", (vision_id,))
        row = cur.fetchone()
        if not row:
            return None
        return ProductVisionMapper.from_db_row(row)

    def update(self, vision: ProductVision) -> ProductVision:
        if vision.id is None:
            raise ValueError("ProductVision.id is required for update")

        data = ProductVisionMapper.to_db_fields(vision)
        # Exclude immutable/managed fields on update
        excluded = {"id", "project_id", "created_at", "updated_at"}
        set_cols = [k for k in data.keys() if k not in excluded]
        assignments = ", ".join([f"{k} = ?" for k in set_cols])
        values = [data[c] for c in set_cols]
        values.append(vision.id)

        sql = f"UPDATE product_visions SET {assignments} WHERE id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, values)
        self.conn.commit()

        return self.get_by_id(vision.id)  # type: ignore[return-value]

    def delete(self, vision_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM product_visions WHERE id = ?", (vision_id,))
        self.conn.commit()
        return cur.rowcount > 0


__all__ = ["ProductVisionRepository"]

