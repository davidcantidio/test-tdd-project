"""
📄 Pagination System - Enterprise Large Dataset Management

Resolves report.md bottleneck: Heavy SQL queries without pagination.
Features:
- LIMIT/OFFSET pagination for all database operations
- Configurable page sizes (10, 25, 50, 100, 250)
- Thread-safe page tracking
- Performance metrics
- Integration with existing DatabaseManager
- Streamlit UI components for pagination controls
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Callable, Any, Iterable, Dict, List, Optional, Tuple

# Graceful Streamlit import
try:  # pragma: no cover - import check
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except Exception:  # pragma: no cover - environment without streamlit
    st = None  # type: ignore
    STREAMLIT_AVAILABLE = False


class PaginationConfig:
    """Pagination configuration and constants."""

    DEFAULT_PAGE_SIZE = 25
    PAGE_SIZES = [10, 25, 50, 100, 250]
    MAX_PAGE_SIZE = 1000


@dataclass
class PaginationResult:
    """Pagination result with metadata."""

    data: Iterable[Any]
    page: int
    page_size: int
    total_count: int

    def __post_init__(self) -> None:
        if self.total_count == 0:
            self.total_pages = 0
            self.has_next = False
            self.has_previous = False
            self.start_index = 0
            self.end_index = 0
        else:
            self.total_pages = (self.total_count + self.page_size - 1) // self.page_size
            self.has_next = self.page < self.total_pages
            self.has_previous = self.page > 1
            self.start_index = (self.page - 1) * self.page_size + 1
            self.end_index = min(self.page * self.page_size, self.total_count)


class PaginationManager:
    """Enterprise pagination manager for large datasets."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.last_query_time: float = 0.0
        self.query_history: List[float] = []

    def paginate_query(
        self,
        query_func: Callable[..., Tuple[Iterable[Any], int]],
        page: int = 1,
        page_size: int = PaginationConfig.DEFAULT_PAGE_SIZE,
        **kwargs: Any,
    ) -> PaginationResult:
        """Apply pagination to any query function.

        Args:
            query_func: Function accepting ``limit`` and ``offset`` and returning
                ``(data, total_count)``.
            page: 1-based page number.
            page_size: Number of items per page.
            **kwargs: Additional keyword arguments passed to ``query_func``.

        Returns:
            PaginationResult containing paginated data and metadata.
        """

        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size < 1 or page_size > PaginationConfig.MAX_PAGE_SIZE:
            raise ValueError(
                f"page_size must be between 1 and {PaginationConfig.MAX_PAGE_SIZE}"
            )

        offset = (page - 1) * page_size

        start = time.perf_counter()
        data, total_count = query_func(limit=page_size, offset=offset, **kwargs)
        end = time.perf_counter()
        elapsed = (end - start) * 1000.0  # milliseconds

        with self._lock:
            self.last_query_time = elapsed
            self.query_history.append(elapsed)

        return PaginationResult(data=data, page=page, page_size=page_size, total_count=total_count)

    def get_page_info(self, total_count: int, page: int, page_size: int) -> Dict[str, int]:
        """Get pagination metadata."""

        result = PaginationResult([], page, page_size, total_count)
        return {
            "total_pages": result.total_pages,
            "has_next": int(result.has_next),
            "has_previous": int(result.has_previous),
            "start_index": result.start_index,
            "end_index": result.end_index,
        }

    def generate_page_numbers(
        self, current_page: int, total_pages: int, window: int = 5
    ) -> List[int]:
        """Generate page number list for UI."""

        start_page = max(1, current_page - window)
        end_page = min(total_pages, current_page + window)
        return list(range(start_page, end_page + 1))

    def render_streamlit_pagination(
        self, pagination_result: PaginationResult, key_prefix: str = "pagination"
    ) -> Optional[Dict[str, Any]]:
        """Render Streamlit pagination controls."""

        if not STREAMLIT_AVAILABLE:  # pragma: no cover - handled in tests via patch
            return None

        st.write(
            f"Showing {pagination_result.start_index}-{pagination_result.end_index} "
            f"of {pagination_result.total_count}"
        )
        cols = st.columns(3)
        prev = cols[0].button(
            "Previous", key=f"{key_prefix}_prev", disabled=not pagination_result.has_previous
        )
        page_input = cols[1].number_input(
            "Page",
            min_value=1,
            max_value=max(1, pagination_result.total_pages),
            value=pagination_result.page,
            key=f"{key_prefix}_page",
        )
        next_ = cols[2].button(
            "Next", key=f"{key_prefix}_next", disabled=not pagination_result.has_next
        )
        page_size = st.selectbox(
            "Page size",
            PaginationConfig.PAGE_SIZES,
            index=PaginationConfig.PAGE_SIZES.index(pagination_result.page_size)
            if pagination_result.page_size in PaginationConfig.PAGE_SIZES
            else 0,
            key=f"{key_prefix}_size",
        )
        return {
            "prev": prev,
            "next": next_,
            "page": int(page_input),
            "page_size": int(page_size),
        }
