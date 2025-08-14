"""
🎨 Theme System for Streamlit Extension

Comprehensive theme management with multiple color schemes and customization options:
- Predefined themes (light, dark, blue, green, purple, etc.)
- Custom theme creation and editing
- Component-specific styling
- Theme persistence and user preferences
- Dynamic theme switching
"""

from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    st = None
    STREAMLIT_AVAILABLE = False


class ThemeMode(Enum):
    """Theme mode enumeration."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # System preference


@dataclass
class ColorScheme:
    """Color scheme definition for theme components."""
    
    # Primary colors
    primary: str = "#1f77b4"
    primary_light: str = "#5a9bd4"
    primary_dark: str = "#1565c0"
    
    # Secondary colors
    secondary: str = "#ff7f0e"
    secondary_light: str = "#ffb74d"
    secondary_dark: str = "#f57c00"
    
    # Background colors
    background: str = "#ffffff"
    background_secondary: str = "#f8f9fa"
    background_accent: str = "#e9ecef"
    
    # Text colors
    text_primary: str = "#212529"
    text_secondary: str = "#6c757d"
    text_muted: str = "#9ca3af"
    
    # Status colors
    success: str = "#28a745"
    warning: str = "#ffc107"
    error: str = "#dc3545"
    info: str = "#17a2b8"
    
    # Interactive colors
    border: str = "#dee2e6"
    border_focus: str = "#80bdff"
    hover: str = "#e9ecef"
    
    # Card and component colors
    card_background: str = "#ffffff"
    card_border: str = "#e0e0e0"
    card_shadow: str = "rgba(0,0,0,0.1)"


@dataclass  
class Theme:
    """Complete theme definition with all styling information."""
    
    name: str
    display_name: str
    mode: ThemeMode
    colors: ColorScheme
    description: str = ""
    
    # Typography
    font_family: str = "'Segoe UI', 'Roboto', sans-serif"
    font_size_base: str = "14px"
    font_size_small: str = "12px"
    font_size_large: str = "16px"
    
    # Spacing
    spacing_xs: str = "4px"
    spacing_sm: str = "8px"
    spacing_md: str = "16px"
    spacing_lg: str = "24px"
    spacing_xl: str = "32px"
    
    # Border radius
    border_radius_sm: str = "4px"
    border_radius_md: str = "8px"
    border_radius_lg: str = "12px"
    
    # Shadows
    shadow_sm: str = "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)"
    shadow_md: str = "0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)"
    shadow_lg: str = "0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23)"


# Predefined themes
PREDEFINED_THEMES = {
    "light": Theme(
        name="light",
        display_name="Light Theme",
        mode=ThemeMode.LIGHT,
        colors=ColorScheme(),  # Default light colors
        description="Clean and bright theme for daytime use"
    ),
    
    "dark": Theme(
        name="dark", 
        display_name="Dark Theme",
        mode=ThemeMode.DARK,
        colors=ColorScheme(
            # Dark theme colors
            primary="#4dabf7",
            primary_light="#74c0fc",
            primary_dark="#339af0",
            
            secondary="#ffd43b",
            secondary_light="#ffe066",
            secondary_dark="#fab005",
            
            background="#1a1a1a",
            background_secondary="#2d2d2d",
            background_accent="#404040",
            
            text_primary="#ffffff",
            text_secondary="#b0b0b0",
            text_muted="#808080",
            
            success="#51cf66",
            warning="#ffd43b", 
            error="#ff6b6b",
            info="#4dabf7",
            
            border="#404040",
            border_focus="#4dabf7",
            hover="#2d2d2d",
            
            card_background="#2d2d2d",
            card_border="#404040",
            card_shadow="rgba(0,0,0,0.3)"
        ),
        description="Dark theme optimized for low-light environments"
    ),
    
    "blue": Theme(
        name="blue",
        display_name="Ocean Blue",
        mode=ThemeMode.LIGHT,
        colors=ColorScheme(
            primary="#0ea5e9",
            primary_light="#38bdf8",
            primary_dark="#0284c7",
            
            secondary="#f97316",
            secondary_light="#fb923c",
            secondary_dark="#ea580c",
            
            background="#f0f9ff",
            background_secondary="#e0f2fe",
            background_accent="#bae6fd",
            
            card_background="#ffffff",
            card_border="#bae6fd",
            
            border="#bae6fd",
            border_focus="#38bdf8",
            hover="#e0f2fe"
        ),
        description="Ocean-inspired blue theme with calming tones"
    ),
    
    "green": Theme(
        name="green",
        display_name="Nature Green", 
        mode=ThemeMode.LIGHT,
        colors=ColorScheme(
            primary="#10b981",
            primary_light="#34d399",
            primary_dark="#059669",
            
            secondary="#f59e0b",
            secondary_light="#fbbf24",
            secondary_dark="#d97706",
            
            background="#f0fdf4",
            background_secondary="#dcfce7",
            background_accent="#bbf7d0",
            
            card_background="#ffffff",
            card_border="#bbf7d0",
            
            border="#bbf7d0",
            border_focus="#34d399",
            hover="#dcfce7"
        ),
        description="Nature-inspired green theme for productivity focus"
    ),
    
    "purple": Theme(
        name="purple",
        display_name="Royal Purple",
        mode=ThemeMode.LIGHT,
        colors=ColorScheme(
            primary="#8b5cf6",
            primary_light="#a78bfa",
            primary_dark="#7c3aed",
            
            secondary="#f59e0b", 
            secondary_light="#fbbf24",
            secondary_dark="#d97706",
            
            background="#faf5ff",
            background_secondary="#f3e8ff",
            background_accent="#e9d5ff",
            
            card_background="#ffffff",
            card_border="#e9d5ff",
            
            border="#e9d5ff",
            border_focus="#a78bfa",
            hover="#f3e8ff"
        ),
        description="Elegant purple theme with royal aesthetics"
    ),
    
    "warm": Theme(
        name="warm",
        display_name="Warm Sunset",
        mode=ThemeMode.LIGHT,
        colors=ColorScheme(
            primary="#f97316",
            primary_light="#fb923c",
            primary_dark="#ea580c",
            
            secondary="#eab308",
            secondary_light="#facc15",
            secondary_dark="#ca8a04",
            
            background="#fffbeb",
            background_secondary="#fef3c7",
            background_accent="#fed7aa",
            
            card_background="#ffffff",
            card_border="#fed7aa",
            
            border="#fed7aa",
            border_focus="#fb923c",
            hover="#fef3c7"
        ),
        description="Warm sunset colors for a cozy feeling"
    ),
    
    "tdah": Theme(
        name="tdah",
        display_name="TDAH Focus",
        mode=ThemeMode.LIGHT,
        colors=ColorScheme(
            # Calming, focus-friendly colors
            primary="#6366f1",  # Indigo - calming but vibrant
            primary_light="#818cf8",
            primary_dark="#4f46e5",
            
            secondary="#10b981",  # Success green for positive feedback
            secondary_light="#34d399", 
            secondary_dark="#059669",
            
            background="#f8fafc",  # Very light blue-gray
            background_secondary="#f1f5f9",
            background_accent="#e2e8f0",
            
            # Soft, non-distracting colors
            success="#10b981",
            warning="#f59e0b",  # Softer orange
            error="#ef4444",    # Softer red
            info="#3b82f6",     # Clear blue
            
            border="#e2e8f0",
            border_focus="#6366f1",
            hover="#f1f5f9",
            
            card_background="#ffffff",
            card_border="#e2e8f0"
        ),
        description="Specially designed for TDAH users with focus-friendly colors"
    )
}


class ThemeManager:
    """Manages theme selection, customization, and persistence."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.cwd() / ".streamlit_themes"
        self.config_dir.mkdir(exist_ok=True)
        
        self.themes_file = self.config_dir / "themes.json"
        self.current_theme_file = self.config_dir / "current_theme.txt"
        
        # Load custom themes if they exist
        self.custom_themes = self._load_custom_themes()
        
        # Current theme
        self._current_theme = self._load_current_theme()
    
    def get_available_themes(self) -> Dict[str, Theme]:
        """Get all available themes (predefined + custom)."""
        all_themes = PREDEFINED_THEMES.copy()
        all_themes.update(self.custom_themes)
        return all_themes
    
    def get_theme(self, theme_name: str) -> Optional[Theme]:
        """Get a specific theme by name."""
        all_themes = self.get_available_themes()
        return all_themes.get(theme_name)
    
    def get_current_theme(self) -> Theme:
        """Get the currently active theme."""
        if self._current_theme:
            theme = self.get_theme(self._current_theme)
            if theme:
                return theme
        
        # Fallback to light theme
        return PREDEFINED_THEMES["light"]
    
    def set_current_theme(self, theme_name: str) -> bool:
        """Set the current active theme."""
        if theme_name in self.get_available_themes():
            self._current_theme = theme_name
            self._save_current_theme()
            return True
        return False
    
    def create_custom_theme(self, base_theme_name: str, custom_name: str, 
                          modifications: Dict[str, Any]) -> bool:
        """Create a custom theme based on an existing theme."""
        base_theme = self.get_theme(base_theme_name)
        if not base_theme:
            return False
        
        # Create new theme with modifications
        theme_dict = asdict(base_theme)
        theme_dict["name"] = custom_name
        theme_dict["display_name"] = modifications.get("display_name", custom_name.title())
        
        # Apply color modifications
        if "colors" in modifications:
            color_dict = theme_dict["colors"]
            color_dict.update(modifications["colors"])
            theme_dict["colors"] = ColorScheme(**color_dict)
        
        # Apply other modifications
        for key, value in modifications.items():
            if key != "colors" and key in theme_dict:
                theme_dict[key] = value
        
        # Create Theme object
        custom_theme = Theme(**theme_dict)
        
        # Save to custom themes
        self.custom_themes[custom_name] = custom_theme
        self._save_custom_themes()
        
        return True
    
    def delete_custom_theme(self, theme_name: str) -> bool:
        """Delete a custom theme."""
        if theme_name in self.custom_themes:
            del self.custom_themes[theme_name]
            self._save_custom_themes()
            
            # Switch to light theme if we're deleting current theme
            if self._current_theme == theme_name:
                self.set_current_theme("light")
            
            return True
        return False
    
    def apply_theme_css(self, theme: Optional[Theme] = None) -> str:
        """Generate CSS for applying theme styles."""
        if not theme:
            theme = self.get_current_theme()
        
        css = f"""
        <style>
        :root {{
            --primary-color: {theme.colors.primary};
            --primary-light: {theme.colors.primary_light};
            --primary-dark: {theme.colors.primary_dark};
            
            --secondary-color: {theme.colors.secondary};
            --secondary-light: {theme.colors.secondary_light};
            --secondary-dark: {theme.colors.secondary_dark};
            
            --background-color: {theme.colors.background};
            --background-secondary: {theme.colors.background_secondary};
            --background-accent: {theme.colors.background_accent};
            
            --text-primary: {theme.colors.text_primary};
            --text-secondary: {theme.colors.text_secondary};
            --text-muted: {theme.colors.text_muted};
            
            --success-color: {theme.colors.success};
            --warning-color: {theme.colors.warning};
            --error-color: {theme.colors.error};
            --info-color: {theme.colors.info};
            
            --border-color: {theme.colors.border};
            --border-focus: {theme.colors.border_focus};
            --hover-color: {theme.colors.hover};
            
            --card-background: {theme.colors.card_background};
            --card-border: {theme.colors.card_border};
            --card-shadow: {theme.colors.card_shadow};
            
            --font-family: {theme.font_family};
            --font-size-base: {theme.font_size_base};
            --font-size-small: {theme.font_size_small};
            --font-size-large: {theme.font_size_large};
            
            --spacing-xs: {theme.spacing_xs};
            --spacing-sm: {theme.spacing_sm};
            --spacing-md: {theme.spacing_md};
            --spacing-lg: {theme.spacing_lg};
            --spacing-xl: {theme.spacing_xl};
            
            --border-radius-sm: {theme.border_radius_sm};
            --border-radius-md: {theme.border_radius_md};
            --border-radius-lg: {theme.border_radius_lg};
            
            --shadow-sm: {theme.shadow_sm};
            --shadow-md: {theme.shadow_md};
            --shadow-lg: {theme.shadow_lg};
        }}
        
        /* Apply theme to common elements */
        .stApp {{
            background-color: var(--background-color);
            color: var(--text-primary);
            font-family: var(--font-family);
        }}
        
        /* Card styling */
        .card-container {{
            background-color: var(--card-background) !important;
            border-color: var(--card-border) !important;
            color: var(--text-primary) !important;
        }}
        
        /* Button styling */
        .stButton > button {{
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: var(--border-radius-md);
        }}
        
        .stButton > button:hover {{
            background-color: var(--primary-dark);
        }}
        
        /* Sidebar styling */
        .css-1d391kg {{
            background-color: var(--background-secondary);
        }}
        
        /* Metric styling */
        .metric-container {{
            background-color: var(--card-background);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius-md);
            padding: var(--spacing-md);
            box-shadow: var(--shadow-sm);
        }}
        </style>
        """
        
        return css
    
    def _load_custom_themes(self) -> Dict[str, Theme]:
        """Load custom themes from file."""
        if not self.themes_file.exists():
            return {}
        
        try:
            with open(self.themes_file, 'r') as f:
                themes_data = json.load(f)
            
            custom_themes = {}
            for name, theme_dict in themes_data.items():
                # Reconstruct ColorScheme
                colors_dict = theme_dict.pop("colors", {})
                colors = ColorScheme(**colors_dict)
                
                # Reconstruct Theme
                theme_dict["colors"] = colors
                custom_themes[name] = Theme(**theme_dict)
            
            return custom_themes
            
        except (json.JSONDecodeError, KeyError, TypeError):
            return {}
    
    def _save_custom_themes(self) -> None:
        """Save custom themes to file."""
        themes_data = {}
        for name, theme in self.custom_themes.items():
            data = asdict(theme)
            data["mode"] = theme.mode.value
            themes_data[name] = data
        
        try:
            with open(self.themes_file, 'w') as f:
                json.dump(themes_data, f, indent=2)
        except OSError:
            pass  # Fail silently
    
    def _load_current_theme(self) -> Optional[str]:
        """Load current theme selection."""
        if not self.current_theme_file.exists():
            return None
        
        try:
            with open(self.current_theme_file, 'r') as f:
                return f.read().strip()
        except OSError:
            return None
    
    def _save_current_theme(self) -> None:
        """Save current theme selection."""
        try:
            with open(self.current_theme_file, 'w') as f:
                f.write(self._current_theme or "light")
        except OSError:
            pass


# Global theme manager instance
_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """Get global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def apply_current_theme() -> str:
    """Apply the current theme and return CSS."""
    if not STREAMLIT_AVAILABLE:
        return ""
    
    theme_manager = get_theme_manager()
    css = theme_manager.apply_theme_css()
    st.markdown(css, unsafe_allow_html=True)
    return css


def render_theme_selector(key: str = "theme_selector") -> None:
    """Render a theme selection widget."""
    if not STREAMLIT_AVAILABLE:
        print("[THEME SELECTOR]")
        return
    
    theme_manager = get_theme_manager()
    available_themes = theme_manager.get_available_themes()
    current_theme = theme_manager.get_current_theme()
    
    theme_options = list(available_themes.keys())
    theme_labels = [theme.display_name for theme in available_themes.values()]
    
    # Current selection
    try:
        default_index = theme_options.index(current_theme.name)
    except ValueError:
        default_index = 0
    
    selected_index = st.selectbox(
        "Choose Theme:",
        range(len(theme_options)),
        format_func=lambda i: theme_labels[i],
        index=default_index,
        key=key,
        help="Select a visual theme for the application"
    )
    
    selected_theme_name = theme_options[selected_index]
    
    # Apply theme if changed
    if selected_theme_name != current_theme.name:
        theme_manager.set_current_theme(selected_theme_name)
        st.rerun()
    
    # Show theme description
    selected_theme = available_themes[selected_theme_name]
    if selected_theme.description:
        st.caption(f"💡 {selected_theme.description}")


# Export for convenience
__all__ = [
    "Theme", "ColorScheme", "ThemeMode", "ThemeManager", 
    "PREDEFINED_THEMES", "get_theme_manager", 
    "apply_current_theme", "render_theme_selector"
]