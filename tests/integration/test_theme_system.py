"""
🎨 Integration Tests for Theme System

Tests theme management, customization, and application:
- Theme creation and modification
- Theme persistence and loading
- CSS generation and application
- Theme switching and validation
- Integration with Streamlit components
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

# Test imports
try:
    from streamlit_extension.config.themes import (
        Theme, ColorScheme, ThemeMode, ThemeManager,
        PREDEFINED_THEMES, get_theme_manager, apply_current_theme, render_theme_selector
    )
    THEMES_AVAILABLE = True
except ImportError:
    THEMES_AVAILABLE = False
    pytest.skip("Theme system not available", allow_module_level=True)


class TestColorScheme:
    """Test ColorScheme functionality."""
    
    def test_color_scheme_creation_default(self):
        """Test ColorScheme creation with default values."""
        colors = ColorScheme()
        
        # Test default primary colors
        assert colors.primary == "#1f77b4"
        assert colors.primary_light == "#5a9bd4" 
        assert colors.primary_dark == "#1565c0"
        
        # Test background colors
        assert colors.background == "#ffffff"
        assert colors.text_primary == "#212529"
        
        # Test status colors
        assert colors.success == "#28a745"
        assert colors.error == "#dc3545"
    
    def test_color_scheme_creation_custom(self):
        """Test ColorScheme creation with custom values."""
        colors = ColorScheme(
            primary="#ff6b6b",
            background="#f8f9fa",
            text_primary="#333333"
        )
        
        assert colors.primary == "#ff6b6b"
        assert colors.background == "#f8f9fa"
        assert colors.text_primary == "#333333"
        
        # Default values should still be set
        assert colors.success == "#28a745"  # Default value


class TestTheme:
    """Test Theme functionality."""
    
    def test_theme_creation_complete(self):
        """Test complete Theme creation."""
        colors = ColorScheme(primary="#4dabf7", background="#1a1a1a")
        
        theme = Theme(
            name="test_theme",
            display_name="Test Theme",
            mode=ThemeMode.DARK,
            colors=colors,
            description="Test theme for unit testing"
        )
        
        assert theme.name == "test_theme"
        assert theme.display_name == "Test Theme"
        assert theme.mode == ThemeMode.DARK
        assert theme.colors == colors
        assert theme.description == "Test theme for unit testing"
        
        # Default typography should be set
        assert "sans-serif" in theme.font_family
        assert theme.font_size_base == "14px"
    
    def test_theme_creation_minimal(self):
        """Test Theme creation with minimal required fields."""
        colors = ColorScheme()
        
        theme = Theme(
            name="minimal",
            display_name="Minimal Theme", 
            mode=ThemeMode.LIGHT,
            colors=colors
        )
        
        assert theme.name == "minimal"
        assert theme.display_name == "Minimal Theme"
        assert theme.colors == colors
        
        # Should have default values
        assert theme.description == ""
        assert theme.spacing_md == "16px"


class TestPredefinedThemes:
    """Test predefined themes."""
    
    def test_all_predefined_themes_valid(self):
        """Test that all predefined themes are valid."""
        for theme_name, theme in PREDEFINED_THEMES.items():
            assert isinstance(theme, Theme)
            assert theme.name == theme_name
            assert theme.display_name
            assert isinstance(theme.mode, ThemeMode)
            assert isinstance(theme.colors, ColorScheme)
    
    def test_light_theme_properties(self):
        """Test light theme specific properties."""
        light_theme = PREDEFINED_THEMES["light"]
        
        assert light_theme.mode == ThemeMode.LIGHT
        assert light_theme.colors.background == "#ffffff"
        assert light_theme.colors.text_primary == "#212529"
    
    def test_dark_theme_properties(self):
        """Test dark theme specific properties.""" 
        dark_theme = PREDEFINED_THEMES["dark"]
        
        assert dark_theme.mode == ThemeMode.DARK
        assert dark_theme.colors.background == "#1a1a1a"
        assert dark_theme.colors.text_primary == "#ffffff"
    
    def test_tdah_theme_properties(self):
        """Test TDAH-specific theme properties."""
        tdah_theme = PREDEFINED_THEMES["tdah"]
        
        assert tdah_theme.mode == ThemeMode.LIGHT
        assert "focus-friendly" in tdah_theme.description.lower()
        # Should use calming colors
        assert tdah_theme.colors.primary == "#6366f1"  # Indigo


class TestThemeManager:
    """Test ThemeManager functionality."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def theme_manager(self, temp_config_dir):
        """Create ThemeManager for testing."""
        return ThemeManager(config_dir=temp_config_dir)
    
    def test_theme_manager_initialization(self, theme_manager, temp_config_dir):
        """Test ThemeManager initialization."""
        assert theme_manager.config_dir == temp_config_dir
        assert theme_manager.config_dir.exists()
        assert theme_manager.themes_file.parent == temp_config_dir
        assert theme_manager.current_theme_file.parent == temp_config_dir
    
    def test_get_available_themes(self, theme_manager):
        """Test getting available themes."""
        themes = theme_manager.get_available_themes()
        
        # Should include all predefined themes
        for theme_name in PREDEFINED_THEMES:
            assert theme_name in themes
        
        # All themes should be Theme instances
        for theme in themes.values():
            assert isinstance(theme, Theme)
    
    def test_get_theme(self, theme_manager):
        """Test getting specific themes."""
        # Existing theme
        light_theme = theme_manager.get_theme("light")
        assert light_theme is not None
        assert light_theme.name == "light"
        
        # Non-existent theme
        fake_theme = theme_manager.get_theme("nonexistent")
        assert fake_theme is None
    
    def test_get_current_theme_default(self, theme_manager):
        """Test getting current theme with no selection."""
        current_theme = theme_manager.get_current_theme()
        
        # Should default to light theme
        assert current_theme.name == "light"
    
    def test_set_current_theme(self, theme_manager):
        """Test setting current theme."""
        # Valid theme
        result = theme_manager.set_current_theme("dark")
        assert result is True
        
        current_theme = theme_manager.get_current_theme()
        assert current_theme.name == "dark"
        
        # Invalid theme
        result = theme_manager.set_current_theme("nonexistent")
        assert result is False
        
        # Current theme should remain unchanged
        current_theme = theme_manager.get_current_theme()
        assert current_theme.name == "dark"
    
    def test_create_custom_theme(self, theme_manager):
        """Test creating custom theme."""
        modifications = {
            "display_name": "My Custom Blue",
            "colors": {
                "primary": "#007bff",
                "secondary": "#ffc107"
            },
            "description": "Custom blue theme for testing"
        }
        
        result = theme_manager.create_custom_theme("light", "custom_blue", modifications)
        assert result is True
        
        # Should be available
        custom_theme = theme_manager.get_theme("custom_blue")
        assert custom_theme is not None
        assert custom_theme.name == "custom_blue"
        assert custom_theme.display_name == "My Custom Blue"
        assert custom_theme.colors.primary == "#007bff"
        assert custom_theme.colors.secondary == "#ffc107"
        assert custom_theme.description == "Custom blue theme for testing"
        
        # Should be in available themes
        available_themes = theme_manager.get_available_themes()
        assert "custom_blue" in available_themes
    
    def test_create_custom_theme_invalid_base(self, theme_manager):
        """Test creating custom theme with invalid base."""
        result = theme_manager.create_custom_theme("nonexistent", "custom", {})
        assert result is False
    
    def test_delete_custom_theme(self, theme_manager):
        """Test deleting custom theme."""
        # Create custom theme first
        theme_manager.create_custom_theme("light", "deleteme", {"display_name": "Delete Me"})
        assert theme_manager.get_theme("deleteme") is not None
        
        # Delete it
        result = theme_manager.delete_custom_theme("deleteme")
        assert result is True
        assert theme_manager.get_theme("deleteme") is None
        
        # Try to delete non-existent theme
        result = theme_manager.delete_custom_theme("nonexistent")
        assert result is False
    
    def test_delete_custom_theme_current(self, theme_manager):
        """Test deleting currently selected custom theme."""
        # Create and set custom theme
        theme_manager.create_custom_theme("dark", "current_custom", {"display_name": "Current Custom"})
        theme_manager.set_current_theme("current_custom")
        
        assert theme_manager.get_current_theme().name == "current_custom"
        
        # Delete current theme
        result = theme_manager.delete_custom_theme("current_custom")
        assert result is True
        
        # Should fall back to light theme
        assert theme_manager.get_current_theme().name == "light"
    
    def test_theme_persistence(self, theme_manager):
        """Test theme persistence across manager instances."""
        # Create custom theme and set as current
        theme_manager.create_custom_theme("green", "persistent", {"display_name": "Persistent Theme"})
        theme_manager.set_current_theme("persistent")
        
        # Create new manager instance with same config dir
        new_manager = ThemeManager(config_dir=theme_manager.config_dir)
        
        # Should load the custom theme and current selection
        assert new_manager.get_theme("persistent") is not None
        assert new_manager.get_current_theme().name == "persistent"
    
    def test_apply_theme_css_generation(self, theme_manager):
        """Test CSS generation for theme application."""
        theme = theme_manager.get_theme("blue")
        css = theme_manager.apply_theme_css(theme)
        
        assert isinstance(css, str)
        assert len(css) > 0
        
        # Should contain CSS variables
        assert "--primary-color:" in css
        assert "--background-color:" in css
        assert "--text-primary:" in css
        
        # Should contain the theme's colors
        assert theme.colors.primary in css
        assert theme.colors.background in css
        
        # Should contain CSS rules
        assert ".stApp" in css
        assert "background-color: var(--background-color)" in css
    
    def test_apply_theme_css_current_theme(self, theme_manager):
        """Test CSS generation for current theme."""
        theme_manager.set_current_theme("purple")
        css = theme_manager.apply_theme_css()  # No theme specified, should use current
        
        purple_theme = theme_manager.get_theme("purple")
        assert purple_theme.colors.primary in css


class TestThemeIntegration:
    """Test theme integration with other systems."""
    
    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit for testing."""
        with patch('streamlit_extension.config.themes.st') as mock_st:
            mock_st.markdown = Mock()
            mock_st.selectbox = Mock(return_value=0)
            mock_st.caption = Mock()
            mock_st.rerun = Mock()
            yield mock_st
    
    def test_apply_current_theme_with_streamlit(self, mock_streamlit):
        """Test applying current theme with Streamlit."""
        with patch('streamlit_extension.config.themes.STREAMLIT_AVAILABLE', True):
            css = apply_current_theme()
            
            # Should call st.markdown with CSS
            mock_streamlit.markdown.assert_called_once()
            args = mock_streamlit.markdown.call_args
            assert args[1]["unsafe_allow_html"] is True
            assert "--primary-color:" in args[0][0]
    
    def test_apply_current_theme_without_streamlit(self):
        """Test applying current theme without Streamlit."""
        with patch('streamlit_extension.config.themes.STREAMLIT_AVAILABLE', False):
            css = apply_current_theme()
            
            # Should return empty string
            assert css == ""
    
    def test_render_theme_selector(self, mock_streamlit):
        """Test rendering theme selector widget."""
        with patch('streamlit_extension.config.themes.STREAMLIT_AVAILABLE', True):
            # Mock theme manager
            mock_manager = Mock()
            mock_manager.get_available_themes.return_value = {
                "light": PREDEFINED_THEMES["light"],
                "dark": PREDEFINED_THEMES["dark"]
            }
            mock_manager.get_current_theme.return_value = PREDEFINED_THEMES["light"]
            
            with patch('streamlit_extension.config.themes.get_theme_manager', return_value=mock_manager):
                render_theme_selector()
            
            # Should call selectbox
            mock_streamlit.selectbox.assert_called_once()
            args = mock_streamlit.selectbox.call_args[1]
            assert args["key"] == "theme_selector"
            assert "Choose Theme:" in mock_streamlit.selectbox.call_args[0][0]
    
    def test_render_theme_selector_without_streamlit(self):
        """Test rendering theme selector without Streamlit."""
        with patch('streamlit_extension.config.themes.STREAMLIT_AVAILABLE', False):
            # Should not crash
            render_theme_selector()
    
    def test_global_theme_manager_singleton(self):
        """Test global theme manager singleton behavior."""
        manager1 = get_theme_manager()
        manager2 = get_theme_manager()
        
        # Should be the same instance
        assert manager1 is manager2
    
    def test_theme_css_variables_completeness(self):
        """Test that generated CSS includes all necessary variables."""
        manager = get_theme_manager()
        theme = manager.get_theme("dark")
        css = manager.apply_theme_css(theme)
        
        # Check for all major CSS variables
        required_vars = [
            "--primary-color:", "--primary-light:", "--primary-dark:",
            "--secondary-color:", "--background-color:", "--text-primary:",
            "--success-color:", "--warning-color:", "--error-color:",
            "--border-color:", "--card-background:", "--font-family:",
            "--spacing-md:", "--border-radius-md:", "--shadow-sm:"
        ]
        
        for var in required_vars:
            assert var in css, f"CSS variable {var} missing from generated CSS"
    
    def test_theme_css_component_styling(self):
        """Test that CSS includes component-specific styling."""
        manager = get_theme_manager()
        css = manager.apply_theme_css()
        
        # Check for component styling
        component_selectors = [
            ".stApp", ".card-container", ".stButton > button",
            ".css-1d391kg", ".metric-container"
        ]
        
        for selector in component_selectors:
            assert selector in css, f"Component selector {selector} missing from CSS"


class TestThemeValidation:
    """Test theme validation and error handling."""
    
    def test_theme_with_invalid_mode(self):
        """Test theme creation with invalid mode."""
        colors = ColorScheme()
        
        # Should handle valid ThemeMode
        theme = Theme("test", "Test", ThemeMode.DARK, colors)
        assert theme.mode == ThemeMode.DARK
    
    def test_theme_manager_file_corruption_handling(self, temp_config_dir):
        """Test theme manager handles corrupted files gracefully."""
        # Create corrupted themes file
        themes_file = temp_config_dir / "themes.json"
        with open(themes_file, 'w') as f:
            f.write("{invalid json content")
        
        # Should not crash and return empty custom themes
        manager = ThemeManager(config_dir=temp_config_dir)
        assert manager.custom_themes == {}
    
    def test_theme_manager_missing_files(self, temp_config_dir):
        """Test theme manager with missing configuration files."""
        # Delete directory to simulate missing files
        import shutil
        shutil.rmtree(temp_config_dir)
        
        # Should recreate directory and work normally
        manager = ThemeManager(config_dir=temp_config_dir)
        assert temp_config_dir.exists()
        assert manager.get_current_theme().name == "light"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])