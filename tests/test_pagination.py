"""Test suite for pagination system with edge cases."""

import time
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from streamlit_extension.utils.pagination import (
    PaginationManager,
    PaginationResult,
    PaginationConfig,
)


# Helper query function
def list_query(data: List[int]) -> callable:
    def _query(limit: int, offset: int) -> Tuple[List[int], int]:
        sliced = data[offset : offset + limit]
        return sliced, len(data)

    return _query


class TestPaginationManager:
    def test_basic_pagination(self):
        """Test basic pagination functionality."""
        data = list(range(100))
        manager = PaginationManager()
        result = manager.paginate_query(list_query(data), page=2, page_size=10)

        assert isinstance(result, PaginationResult)
        assert list(result.data) == list(range(10, 20))
        assert result.page == 2
        assert result.page_size == 10
        assert result.total_count == 100
        assert result.total_pages == 10
        assert result.has_next is True
        assert result.has_previous is True
        assert result.start_index == 11
        assert result.end_index == 20

    def test_edge_cases(self):
        """Test edge cases: empty results, single page, large datasets."""
        manager = PaginationManager()

        # Empty dataset
        empty_result = manager.paginate_query(list_query([]), page=1, page_size=10)
        assert empty_result.total_pages == 0
        assert empty_result.start_index == 0
        assert empty_result.end_index == 0

        # Single page dataset
        single_data = list(range(5))
        single_result = manager.paginate_query(list_query(single_data), page=1, page_size=10)
        assert single_result.total_pages == 1
        assert single_result.has_next is False
        assert single_result.has_previous is False

        # Large dataset
        large_data = list(range(1000))
        large_result = manager.paginate_query(list_query(large_data), page=5, page_size=100)
        assert list(large_result.data) == list(range(400, 500))
        assert large_result.total_pages == 10

    def test_performance_large_datasets(self):
        """Test performance with large datasets."""
        data = list(range(10000))
        manager = PaginationManager()
        start = time.perf_counter()
        manager.paginate_query(list_query(data), page=1, page_size=50)
        elapsed = (time.perf_counter() - start) * 1000
        assert elapsed < 100, f"Pagination took too long: {elapsed}ms"

    def test_streamlit_integration(self, monkeypatch):
        """Test Streamlit UI component integration."""
        manager = PaginationManager()
        result = PaginationResult(data=[], page=1, page_size=10, total_count=100)

        # Create dummy streamlit object
        class DummyStreamlit:
            def __init__(self):
                self.calls = []

            def write(self, *args, **kwargs):
                self.calls.append("write")

            def columns(self, n):
                return [self, self, self]

            def button(self, *args, **kwargs):
                self.calls.append("button")
                return False

            def number_input(self, *args, **kwargs):
                self.calls.append("number_input")
                return 1

            def selectbox(self, *args, **kwargs):
                self.calls.append("selectbox")
                return 10

        dummy = DummyStreamlit()
        monkeypatch.setattr(
            "streamlit_extension.utils.pagination.st", dummy, raising=False
        )
        monkeypatch.setattr(
            "streamlit_extension.utils.pagination.STREAMLIT_AVAILABLE", True
        )

        ui_result = manager.render_streamlit_pagination(result)
        assert ui_result is not None
        assert set(ui_result.keys()) == {"prev", "next", "page", "page_size"}
        assert dummy.calls  # ensure methods were called

