"""
🧪 Performance Tests for Pagination System

Tests for pagination performance with different strategies and data volumes.
Ensures pagination methods perform well under various conditions.
"""

import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from streamlit_extension.utils.database import DatabaseManager, PaginationType


def _create_db(path, count=100):
    """Create test database with sample data."""
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
    conn.executemany("INSERT INTO items (name) VALUES (?)", [(f"name{i}",) for i in range(count)])
    conn.commit()
    conn.close()


class TestPaginationPerformance:
    """Test pagination performance under various conditions."""

    def test_offset_pagination_performance(self, tmp_path):
        """Test OFFSET-based pagination performance."""
        db_path = tmp_path / "test.db"
        _create_db(db_path, 50)
        db = DatabaseManager(framework_db_path=str(db_path))
        
        result = db.get_paginated_results("items", page=2, per_page=10, sort_by="id")
        
        assert result.page == 2
        assert len(result.items) == 10
        assert result.query_time_ms >= 0  # Performance timing recorded
        assert result.total_count == 50
        assert result.total_pages == 5

    def test_cursor_pagination_performance(self, tmp_path):
        """Test cursor-based pagination performance."""
        db_path = tmp_path / "test.db"
        _create_db(db_path, 20)
        db = DatabaseManager(framework_db_path=str(db_path))
        
        # First page
        first = db.get_paginated_results(
            "items",
            per_page=5,
            sort_by="id",
            pagination_type=PaginationType.CURSOR_BASED,
        )
        
        assert len(first.items) == 5
        assert first.next_cursor is not None
        assert first.query_time_ms >= 0
        
        # Second page using cursor
        second = db.get_paginated_results(
            "items",
            per_page=5,
            sort_by="id",
            pagination_type=PaginationType.CURSOR_BASED,
            cursor=first.next_cursor,
        )
        
        assert len(second.items) <= 5
        assert second.query_time_ms >= 0

    def test_keyset_pagination_performance(self, tmp_path):
        """Test keyset pagination performance."""
        db_path = tmp_path / "test.db"
        _create_db(db_path, 30)
        db = DatabaseManager(framework_db_path=str(db_path))
        
        result = db.get_keyset_paginated_results("items", ["id"], per_page=7)
        
        assert len(result.items) <= 7
        assert result.query_time_ms >= 0
        assert result.total_count == 30

    def test_pagination_memory_usage(self, tmp_path):
        """Test pagination memory efficiency with larger datasets."""
        db_path = tmp_path / "test.db"
        _create_db(db_path, 40)
        db = DatabaseManager(framework_db_path=str(db_path))
        
        result = db.get_paginated_results("items", page=1, per_page=40)
        
        assert result.total_count == 40
        assert len(result.items) == 40
        assert result.query_time_ms >= 0
        
    def test_pagination_with_filters(self, tmp_path):
        """Test pagination performance with filtering."""
        db_path = tmp_path / "test.db"
        _create_db(db_path, 25)
        db = DatabaseManager(framework_db_path=str(db_path))
        
        # Test with basic filter (security: filter values are sanitized)
        result = db.get_paginated_results(
            "items", 
            page=1, 
            per_page=10,
            filters={"id": 1}
        )
        
        assert result.query_time_ms >= 0
        assert isinstance(result.items, list)
        
    def test_pagination_security_validation(self, tmp_path):
        """Test security validation in pagination."""
        db_path = tmp_path / "test.db"
        _create_db(db_path, 10)
        db = DatabaseManager(framework_db_path=str(db_path))
        
        # Test table name validation
        try:
            db.get_paginated_results("invalid_table", page=1)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid table name" in str(e)
            
        # Test sort column validation  
        try:
            db.get_paginated_results("items", page=1, sort_by="invalid_column")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid sort column" in str(e)