"""
Pagination Component for Streamlit
Provides consistent pagination across all list views
"""

import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import streamlit as st


@dataclass
class PaginationConfig:
    """Configuration for pagination component"""

    page_size: int = 20
    show_page_size_selector: bool = True
    page_size_options: Optional[List[int]] = None
    show_total_count: bool = True
    show_navigation_info: bool = True

    def __post_init__(self) -> None:
        if self.page_size_options is None:
            self.page_size_options = [10, 20, 50, 100]


@dataclass
class PaginationState:
    """Current pagination state"""

    current_page: int = 1
    page_size: int = 20
    total_items: int = 0
    total_pages: int = 0
    offset: int = 0

    def calculate_pagination(
        self, total_items: int, page_size: int, current_page: int = 1
    ) -> "PaginationState":
        """Calculate pagination values"""
        self.total_items = total_items
        self.page_size = page_size
        self.total_pages = math.ceil(total_items / page_size) if page_size > 0 else 1
        self.current_page = max(1, min(current_page, self.total_pages))
        self.offset = (self.current_page - 1) * page_size
        return self


class PaginationComponent:
    """Reusable pagination component for Streamlit"""

    def __init__(self, key_prefix: str, config: Optional[PaginationConfig] = None) -> None:
        self.key_prefix = key_prefix
        self.config = config or PaginationConfig()

    def _get_session_key(self, suffix: str) -> str:
        """Generate session state key"""
        return f"{self.key_prefix}_{suffix}"

    def _init_session_state(self) -> None:
        """Initialize session state if needed"""
        if self._get_session_key("page") not in st.session_state:
            st.session_state[self._get_session_key("page")] = 1
        if self._get_session_key("page_size") not in st.session_state:
            st.session_state[self._get_session_key("page_size")] = self.config.page_size

    def get_pagination_state(self, total_items: int) -> PaginationState:
        """Get current pagination state"""
        self._init_session_state()
        current_page = st.session_state[self._get_session_key("page")]
        page_size = st.session_state[self._get_session_key("page_size")]
        state = PaginationState()
        return state.calculate_pagination(total_items, page_size, current_page)

    def render_pagination_controls(self, state: PaginationState) -> PaginationState:
        """Render pagination controls"""
        if state.total_items == 0:
            st.info("📭 Nenhum item encontrado")
            return state

        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])

        with col1:
            if self.config.show_total_count:
                st.caption(f"📊 Total: {state.total_items} itens")

        with col2:
            if self.config.show_page_size_selector:
                new_page_size = st.selectbox(
                    "Itens/página",
                    self.config.page_size_options,
                    index=self.config.page_size_options.index(state.page_size)
                    if state.page_size in self.config.page_size_options
                    else 0,
                    key=self._get_session_key("page_size_select"),
                )
                if new_page_size != state.page_size:
                    st.session_state[self._get_session_key("page_size")] = new_page_size
                    st.session_state[self._get_session_key("page")] = 1
                    st.rerun()

        with col3:
            if state.total_pages > 1:
                nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
                with nav_col1:
                    if st.button(
                        "⏮️",
                        disabled=state.current_page <= 1,
                        key=self._get_session_key("first"),
                    ):
                        st.session_state[self._get_session_key("page")] = 1
                        st.rerun()
                with nav_col2:
                    if st.button(
                        "◀️",
                        disabled=state.current_page <= 1,
                        key=self._get_session_key("prev"),
                    ):
                        st.session_state[self._get_session_key("page")] = state.current_page - 1
                        st.rerun()
                with nav_col3:
                    if st.button(
                        "▶️",
                        disabled=state.current_page >= state.total_pages,
                        key=self._get_session_key("next"),
                    ):
                        st.session_state[self._get_session_key("page")] = state.current_page + 1
                        st.rerun()
                with nav_col4:
                    if st.button(
                        "⏭️",
                        disabled=state.current_page >= state.total_pages,
                        key=self._get_session_key("last"),
                    ):
                        st.session_state[self._get_session_key("page")] = state.total_pages
                        st.rerun()

        with col4:
            if self.config.show_navigation_info and state.total_pages > 1:
                st.caption(f"📄 Página {state.current_page} de {state.total_pages}")

        return state

    def paginate_data(
        self, data_fetcher: Callable, *args: Any, **kwargs: Any
    ) -> Tuple[List[Any], PaginationState]:
        """Paginate data using a data fetcher function"""
        state = self.get_pagination_state(0)
        try:
            data, total_count = data_fetcher(
                state.page_size, state.offset, *args, **kwargs
            )
            state = state.calculate_pagination(
                total_count, state.page_size, state.current_page
            )
            return data, state
        except Exception as e:  # pragma: no cover - streamlit error reporting
            st.error(f"❌ Erro ao carregar dados: {e}")
            return [], state


def create_pagination_wrapper(
    key_prefix: str, config: Optional[PaginationConfig] = None
) -> PaginationComponent:
    """Factory function to create pagination component"""
    return PaginationComponent(key_prefix, config)