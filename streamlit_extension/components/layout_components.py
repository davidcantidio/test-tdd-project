"""
🎨 Layout Components for Streamlit Extension

Reusable layout containers and structural components:
- CardContainer: Styled card containers with borders and padding
- SidebarSection: Organized sidebar sections with collapsible content
- ExpandableSection: Expandable content sections with icons and state management
"""

from typing import Optional, Dict, Any, Union, List, Callable
from dataclasses import dataclass
from contextlib import contextmanager, nullcontext

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    st = None
    STREAMLIT_AVAILABLE = False


@dataclass
class CardStyle:
    """Styling configuration for card containers."""
    border_color: str = "#e0e0e0"
    background_color: str = "#ffffff"
    border_radius: str = "8px"
    padding: str = "16px"
    margin: str = "8px 0"
    shadow: bool = False
    hover_effect: bool = False


# Predefined card styles
CARD_STYLES = {
    "default": CardStyle(),
    "success": CardStyle(border_color="#28a745", background_color="#f8fff9"),
    "warning": CardStyle(border_color="#ffc107", background_color="#fffdf0"),
    "error": CardStyle(border_color="#dc3545", background_color="#fff5f5"),
    "info": CardStyle(border_color="#17a2b8", background_color="#f0f9ff"),
    "subtle": CardStyle(border_color="#f0f0f0", background_color="#fafafa"),
    "elevated": CardStyle(shadow=True, hover_effect=True),
    "minimal": CardStyle(border_color="transparent", padding="8px"),
}


class CardContainer:
    """Styled card container with customizable appearance."""
    
    def __init__(self, style: Union[str, CardStyle] = "default", title: str = None, 
                 subtitle: str = None, show_divider: bool = False):
        if isinstance(style, str):
            self.style = CARD_STYLES.get(style, CARD_STYLES["default"])
        else:
            self.style = style
        
        self.title = title
        self.subtitle = subtitle
        self.show_divider = show_divider
    
    @contextmanager
    def render(self):
        """Context manager for rendering content within the card."""
        if not STREAMLIT_AVAILABLE:
            if self.title:
                print(f"=== {self.title} ===")
            if self.subtitle:
                print(f"--- {self.subtitle} ---")
            
            yield
            print()  # Empty line after card
            return
        
        # Generate card CSS
        shadow_css = "box-shadow: 0 2px 4px rgba(0,0,0,0.1);" if self.style.shadow else ""
        hover_css = "transition: box-shadow 0.2s ease; cursor: pointer;" if self.style.hover_effect else ""
        hover_shadow = ":hover { box-shadow: 0 4px 8px rgba(0,0,0,0.15); }" if self.style.hover_effect else ""
        
        card_css = f"""
        <style>
        .card-container {{
            border: 1px solid {self.style.border_color};
            background-color: {self.style.background_color};
            border-radius: {self.style.border_radius};
            padding: {self.style.padding};
            margin: {self.style.margin};
            {shadow_css}
            {hover_css}
        }}
        .card-container{hover_shadow}
        </style>
        """
        
        st.markdown(card_css, unsafe_allow_html=True)
        
        # Start card container
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        
        # Render title and subtitle
        if self.title:
            st.markdown(f"### {self.title}")
        
        if self.subtitle:
            st.markdown(f"*{self.subtitle}*")
        
        if self.show_divider and (self.title or self.subtitle):
            st.divider()
        
        # Yield control to the content
        yield
        
        # Close card container
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_content(self, content_func: Callable[[], None]) -> None:
        """Render content using a function instead of context manager."""
        with self.render():
            content_func()
    
    @staticmethod
    def render_grid(cards: List[Dict[str, Any]], columns: int = 2) -> None:
        """Render multiple cards in a grid layout."""
        if not STREAMLIT_AVAILABLE:
            for card_data in cards:
                print(f"=== {card_data.get('title', 'Card')} ===")
                if 'content' in card_data:
                    print(card_data['content'])
                print()
            return
        
        cols = st.columns(columns)

        for i, card_data in enumerate(cards):
            col = cols[i % columns]
            if hasattr(col, "__enter__") and hasattr(col, "__exit__"):
                col_ctx = col
            else:
                col_ctx = nullcontext()

            with col_ctx:
                style = card_data.get('style', 'default')
                title = card_data.get('title')
                subtitle = card_data.get('subtitle')

                card = CardContainer(style=style, title=title, subtitle=subtitle)

                with card.render():
                    if 'content_func' in card_data:
                        card_data['content_func']()
                    elif 'content' in card_data:
                        st.markdown(card_data['content'])


class SidebarSection:
    """Organized sidebar section with collapsible content and consistent styling."""
    
    def __init__(self, title: str, icon: str = "", collapsible: bool = False, 
                 expanded: bool = True, help_text: str = None):
        self.title = title
        self.icon = icon
        self.collapsible = collapsible
        self.expanded = expanded
        self.help_text = help_text
        self._section_key = f"sidebar_section_{title.lower().replace(' ', '_')}"
    
    @contextmanager
    def render(self):
        """Context manager for rendering sidebar section content."""
        if not STREAMLIT_AVAILABLE:
            icon_part = f"{self.icon} " if self.icon else ""
            print(f"[SIDEBAR] {icon_part}{self.title}")
            if self.help_text:
                print(f"  Help: {self.help_text}")
            
            yield
            print()
            return
        
        # Build title with icon
        display_title = f"{self.icon} {self.title}" if self.icon else self.title
        
        if self.collapsible:
            with st.sidebar.expander(display_title, expanded=self.expanded):
                if self.help_text:
                    st.help(self.help_text)
                yield
        else:
            st.sidebar.markdown(f"### {display_title}")
            if self.help_text:
                st.sidebar.info(f"💡 {self.help_text}")
            yield
    
    def render_content(self, content_func: Callable[[], None]) -> None:
        """Render content using a function."""
        with self.render():
            content_func()
    
    @staticmethod
    def render_divider(text: str = None) -> None:
        """Render a divider in the sidebar."""
        if not STREAMLIT_AVAILABLE:
            print(f"--- {text or ''} ---")
            return
        
        if text:
            st.sidebar.markdown(f"---\n**{text}**")
        else:
            st.sidebar.markdown("---")


class ExpandableSection:
    """Expandable content section with state management and custom styling."""
    
    def __init__(self, title: str, icon: str = "📋", default_expanded: bool = False,
                 key: str = None, help_text: str = None, 
                 style: Union[str, CardStyle] = None):
        self.title = title
        self.icon = icon
        self.default_expanded = default_expanded
        self.key = key or f"expandable_{title.lower().replace(' ', '_')}"
        self.help_text = help_text
        
        if isinstance(style, str):
            self.style = CARD_STYLES.get(style, CARD_STYLES["default"])
        else:
            self.style = style
    
    @contextmanager
    def render(self):
        """Context manager for rendering expandable section."""
        if not STREAMLIT_AVAILABLE:
            print(f"[EXPANDABLE] {self.icon} {self.title}")
            if self.help_text:
                print(f"  Help: {self.help_text}")
            
            yield
            print()
            return
        
        # Build title with icon
        display_title = f"{self.icon} {self.title}"
        
        # Render as expander
        with st.expander(display_title, expanded=self.default_expanded):
            if self.help_text:
                st.info(f"💡 {self.help_text}")
            
            # Apply card styling if specified
            if self.style:
                shadow_css = "box-shadow: 0 1px 3px rgba(0,0,0,0.1);" if self.style.shadow else ""
                
                card_css = f"""
                <div style="
                    background-color: {self.style.background_color};
                    border-radius: {self.style.border_radius};
                    padding: {self.style.padding};
                    margin: 4px 0;
                    {shadow_css}
                ">
                """
                st.markdown(card_css, unsafe_allow_html=True)
                
                yield
                
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                yield
    
    def render_content(self, content_func: Callable[[], None]) -> None:
        """Render content using a function."""
        with self.render():
            content_func()
    
    def is_expanded(self) -> bool:
        """Check if the section is currently expanded (approximation)."""
        if not STREAMLIT_AVAILABLE:
            return self.default_expanded
        
        # Note: Streamlit doesn't provide direct access to expander state
        # This is a best-effort approximation using session state
        return st.session_state.get(f"{self.key}_expanded", self.default_expanded)


class TabContainer:
    """Enhanced tab container with consistent styling and state management."""
    
    def __init__(self, tabs: List[str], icons: List[str] = None, 
                 default_tab: int = 0, key: str = None):
        self.tabs = tabs
        self.icons = icons or ["📄"] * len(tabs)
        self.default_tab = default_tab
        self.key = key or "tab_container"
        
        # Ensure icons list matches tabs length
        if len(self.icons) < len(self.tabs):
            self.icons.extend(["📄"] * (len(self.tabs) - len(self.icons)))
    
    def render(self) -> int:
        """Render tabs and return the selected tab index."""
        if not STREAMLIT_AVAILABLE:
            print(f"[TABS] Available: {', '.join(self.tabs)}")
            return self.default_tab
        
        # Build tab labels with icons
        tab_labels = [f"{self.icons[i]} {tab}" for i, tab in enumerate(self.tabs)]
        
        # Create tabs
        tab_objects = st.tabs(tab_labels)
        
        return tab_objects
    
    @contextmanager
    def render_tab_content(self, tab_index: int):
        """Context manager for rendering content in a specific tab."""
        tab_objects = self.render()
        
        if STREAMLIT_AVAILABLE:
            with tab_objects[tab_index]:
                yield
        else:
            print(f"[TAB {tab_index}] {self.tabs[tab_index]}")
            yield


# Layout utility functions
def create_two_column_layout(left_content: Callable[[], None], 
                           right_content: Callable[[], None],
                           ratio: List[int] = [1, 1]) -> None:
    """Create a simple two-column layout."""
    if not STREAMLIT_AVAILABLE:
        print("[LEFT COLUMN]")
        left_content()
        print("[RIGHT COLUMN]")
        right_content()
        return
    
    col1, col2 = st.columns(ratio)

    if hasattr(col1, "__enter__") and hasattr(col1, "__exit__"):
        with col1:
            left_content()
    else:
        left_content()

    if hasattr(col2, "__enter__") and hasattr(col2, "__exit__"):
        with col2:
            right_content()
    else:
        right_content()


def create_three_column_layout(left_content: Callable[[], None],
                             center_content: Callable[[], None], 
                             right_content: Callable[[], None],
                             ratio: List[int] = [1, 1, 1]) -> None:
    """Create a three-column layout."""
    if not STREAMLIT_AVAILABLE:
        print("[LEFT COLUMN]")
        left_content()
        print("[CENTER COLUMN]") 
        center_content()
        print("[RIGHT COLUMN]")
        right_content()
        return
    
    col1, col2, col3 = st.columns(ratio)

    cols = [col1, col2, col3]
    contents = [left_content, center_content, right_content]

    for col, content in zip(cols, contents):
        if hasattr(col, "__enter__") and hasattr(col, "__exit__"):
            with col:
                content()
        else:
            content()


def create_sidebar_main_layout(sidebar_content: Callable[[], None],
                             main_content: Callable[[], None]) -> None:
    """Create sidebar + main content layout."""
    if not STREAMLIT_AVAILABLE:
        print("[SIDEBAR]")
        sidebar_content()
        print("[MAIN CONTENT]")
        main_content()
        return
    
    # Render sidebar content
    sidebar_ctx = st.sidebar if hasattr(st.sidebar, "__enter__") and hasattr(st.sidebar, "__exit__") else nullcontext()
    with sidebar_ctx:
        sidebar_content()

    # Render main content
    main_content()


# Export for convenience  
__all__ = [
    "CardContainer", "SidebarSection", "ExpandableSection", "TabContainer",
    "CardStyle", "CARD_STYLES",
    "create_two_column_layout", "create_three_column_layout", "create_sidebar_main_layout"
]