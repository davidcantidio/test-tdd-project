"""
🎨 Integration Tests for UI Components

Tests the reusable UI components functionality and integration:
- Status components (badges, progress cards, metrics)
- Layout components (cards, sections, tabs)
- Component rendering and styling
- Integration with Streamlit
- Graceful fallbacks when dependencies unavailable
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager
import io
import sys

# Test imports
try:
    from streamlit_extension.components.status_components import (
        StatusBadge, ProgressCard, MetricCard, StatusConfig, STATUS_CONFIGS,
        create_percentage_metric, create_count_metric, create_time_metric, create_score_metric
    )
    STATUS_COMPONENTS_AVAILABLE = True
except ImportError:
    STATUS_COMPONENTS_AVAILABLE = False

try:
    from streamlit_extension.components.layout_components import (
        CardContainer, SidebarSection, ExpandableSection, TabContainer,
        CardStyle, CARD_STYLES, create_two_column_layout, 
        create_three_column_layout, create_sidebar_main_layout
    )
    LAYOUT_COMPONENTS_AVAILABLE = True
except ImportError:
    LAYOUT_COMPONENTS_AVAILABLE = False


@contextmanager
def capture_output():
    """Capture stdout for testing fallback rendering."""
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    try:
        yield captured_output
    finally:
        sys.stdout = old_stdout


class TestStatusComponents:
    """Test status components functionality."""
    
    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit for testing."""
        with patch('streamlit_extension.components.status_components.st') as mock_st:
            mock_st.markdown = Mock()
            mock_st.columns = Mock(return_value=[Mock(), Mock()])
            mock_st.metric = Mock()
            mock_st.container = Mock()
            mock_st.plotly_chart = Mock()
            yield mock_st
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")
    def test_status_badge_creation(self):
        """Test StatusBadge creation and configuration."""
        badge = StatusBadge("success")
        assert badge.status == "success"
        assert badge.config == STATUS_CONFIGS["success"]
        
        # Custom config
        custom_config = StatusConfig("purple", "💜", "white")
        custom_badge = StatusBadge("custom", custom_config)
        assert custom_badge.config == custom_config
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")
    def test_status_badge_render_with_streamlit(self, mock_streamlit):
        """Test StatusBadge rendering with Streamlit."""
        with patch('streamlit_extension.components.status_components.STREAMLIT_AVAILABLE', True):
            badge = StatusBadge("success")
            badge.render("Test Success")
            
            # Should call st.markdown
            mock_streamlit.markdown.assert_called_once()
            args = mock_streamlit.markdown.call_args
            assert "Test Success" in args[0][0]
            assert "unsafe_allow_html" in args[1]
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")
    def test_status_badge_fallback_rendering(self):
        """Test StatusBadge fallback rendering without Streamlit."""
        with patch('streamlit_extension.components.status_components.STREAMLIT_AVAILABLE', False):
            badge = StatusBadge("warning")
            
            with capture_output() as output:
                badge.render("Test Warning")
            
            result = output.getvalue()
            assert "[WARNING]" in result
            assert "Test Warning" in result
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")  
    def test_status_badge_list_rendering(self, mock_streamlit):
        """Test StatusBadge list rendering."""
        with patch('streamlit_extension.components.status_components.STREAMLIT_AVAILABLE', True):
            statuses = ["success", "warning", "error"]
            texts = ["Complete", "In Progress", "Failed"]
            
            StatusBadge.render_list(statuses, texts)
            
            mock_streamlit.markdown.assert_called_once()
            args = mock_streamlit.markdown.call_args
            html_content = args[0][0]
            
            # Should contain all texts
            for text in texts:
                assert text in html_content
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")
    def test_progress_card_creation(self):
        """Test ProgressCard creation and calculation."""
        card = ProgressCard("Test Progress", 75, 100)
        
        assert card.title == "Test Progress"
        assert card.current == 75
        assert card.total == 100
        assert card.percentage == 75.0
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")
    def test_progress_card_render_with_streamlit(self, mock_streamlit):
        """Test ProgressCard rendering with Streamlit."""
        with patch('streamlit_extension.components.status_components.STREAMLIT_AVAILABLE', True):
            card = ProgressCard("Test Progress", 30, 50, "Test description")
            card.render()
            
            # Should call multiple streamlit functions
            mock_streamlit.markdown.assert_called()
            mock_streamlit.columns.assert_called()
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")
    def test_progress_card_mini_render(self, mock_streamlit):
        """Test ProgressCard mini rendering."""
        with patch('streamlit_extension.components.status_components.STREAMLIT_AVAILABLE', True):
            card = ProgressCard("Mini Progress", 25, 100)
            card.render_mini(width=150)
            
            mock_streamlit.markdown.assert_called_once()
            html_content = mock_streamlit.markdown.call_args[0][0]
            assert "150px" in html_content
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")
    def test_metric_card_creation(self):
        """Test MetricCard creation."""
        card = MetricCard("Test Metric", 42, delta=5, unit="MB", prefix="~")
        
        assert card.title == "Test Metric"
        assert card.value == 42
        assert card.delta == 5
        assert card.unit == "MB"
        assert card.prefix == "~"
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")
    def test_metric_card_render_default(self, mock_streamlit):
        """Test MetricCard default rendering."""
        with patch('streamlit_extension.components.status_components.STREAMLIT_AVAILABLE', True):
            card = MetricCard("CPU Usage", 85.5, delta=2.3, unit="%")
            card.render()
            
            mock_streamlit.metric.assert_called_once()
            args = mock_streamlit.metric.call_args[1]
            assert args["label"] == "CPU Usage"
            assert "85.5%" in args["value"]
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")
    def test_metric_card_render_compact(self, mock_streamlit):
        """Test MetricCard compact rendering."""
        with patch('streamlit_extension.components.status_components.STREAMLIT_AVAILABLE', True):
            mock_streamlit.columns.return_value = [Mock(), Mock(), Mock()]
            
            card = MetricCard("Memory", 4.2, delta=-0.1, unit="GB")
            card.render(layout="compact")
            
            mock_streamlit.columns.assert_called_once()
            mock_streamlit.markdown.assert_called()
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")
    def test_metric_card_render_detailed(self, mock_streamlit):
        """Test MetricCard detailed rendering with charts."""
        with patch('streamlit_extension.components.status_components.STREAMLIT_AVAILABLE', True):
            with patch('streamlit_extension.components.status_components.PLOTLY_AVAILABLE', True):
                mock_streamlit.columns.return_value = [Mock(), Mock()]
                mock_streamlit.container.return_value.__enter__ = Mock(return_value=Mock())
                mock_streamlit.container.return_value.__exit__ = Mock(return_value=None)
                
                card = MetricCard("Detailed Metric", 100, delta=10)
                chart_data = [90, 95, 98, 100, 105]
                
                card.render(layout="detailed", show_chart=True, chart_data=chart_data)
                
                mock_streamlit.container.assert_called()
    
    @pytest.mark.skipif(not STATUS_COMPONENTS_AVAILABLE, reason="Status components not available")
    def test_metric_utility_functions(self):
        """Test utility functions for metric creation."""
        # Percentage metric
        pct_metric = create_percentage_metric("Completion", 75, 100)
        assert pct_metric.value == "75.0"
        assert pct_metric.unit == "%"
        
        # Count metric
        count_metric = create_count_metric("Items", 1500, delta=50)
        assert count_metric.value == "1,500"
        assert count_metric.delta == 50
        
        # Time metric
        time_metric = create_time_metric("Duration", 90)  # 90 minutes
        assert time_metric.value == "1.5"  # Should convert to hours
        assert time_metric.unit == "h"
        
        # Score metric
        score_metric = create_score_metric("Rating", 8.5)
        assert score_metric.value == "8.5"
        assert score_metric.unit == "/10"


class TestLayoutComponents:
    """Test layout components functionality."""
    
    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit for testing."""
        with patch('streamlit_extension.components.layout_components.st') as mock_st:
            mock_st.markdown = Mock()
            mock_st.columns = Mock(return_value=[Mock(), Mock()])
            mock_st.expander = Mock()
            mock_st.tabs = Mock(return_value=[Mock(), Mock()])
            mock_st.divider = Mock()
            mock_st.sidebar = Mock()
            mock_st.components = Mock()
            mock_st.components.v1 = Mock()
            mock_st.components.v1.html = Mock()
            yield mock_st
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_card_container_creation(self):
        """Test CardContainer creation with different styles."""
        # Default style
        card = CardContainer()
        assert card.style == CARD_STYLES["default"]
        
        # Named style
        card = CardContainer(style="success")
        assert card.style == CARD_STYLES["success"]
        
        # Custom style
        custom_style = CardStyle(border_color="#ff0000", background_color="#ffe6e6")
        card = CardContainer(style=custom_style)
        assert card.style == custom_style
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_card_container_render_context_manager(self, mock_streamlit):
        """Test CardContainer as context manager."""
        with patch('streamlit_extension.components.layout_components.STREAMLIT_AVAILABLE', True):
            card = CardContainer(title="Test Card", subtitle="Test subtitle")
            
            with card.render():
                # Simulate content inside card
                pass
            
            # Should have called markdown for CSS and HTML structure
            assert mock_streamlit.markdown.call_count >= 2
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_card_container_render_function(self, mock_streamlit):
        """Test CardContainer with render function."""
        with patch('streamlit_extension.components.layout_components.STREAMLIT_AVAILABLE', True):
            card = CardContainer(title="Function Card")
            
            def test_content():
                mock_streamlit.write("Test content")
            
            card.render_content(test_content)
            
            mock_streamlit.markdown.assert_called()
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_card_container_grid_render(self, mock_streamlit):
        """Test CardContainer grid rendering."""
        with patch('streamlit_extension.components.layout_components.STREAMLIT_AVAILABLE', True):
            mock_streamlit.columns.return_value = [Mock(), Mock()]
            
            cards_data = [
                {"title": "Card 1", "content": "Content 1", "style": "success"},
                {"title": "Card 2", "content": "Content 2", "style": "warning"}
            ]
            
            CardContainer.render_grid(cards_data, columns=2)
            
            mock_streamlit.columns.assert_called_with(2)
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_sidebar_section_creation(self):
        """Test SidebarSection creation."""
        section = SidebarSection("Test Section", icon="🧪", collapsible=True)
        
        assert section.title == "Test Section"
        assert section.icon == "🧪"
        assert section.collapsible is True
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_sidebar_section_render(self, mock_streamlit):
        """Test SidebarSection rendering."""
        with patch('streamlit_extension.components.layout_components.STREAMLIT_AVAILABLE', True):
            mock_streamlit.sidebar.expander.return_value.__enter__ = Mock(return_value=Mock())
            mock_streamlit.sidebar.expander.return_value.__exit__ = Mock(return_value=None)
            
            section = SidebarSection("Collapsible Section", collapsible=True)
            
            with section.render():
                pass
            
            mock_streamlit.sidebar.expander.assert_called_once()
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_sidebar_section_divider(self, mock_streamlit):
        """Test SidebarSection divider rendering."""
        with patch('streamlit_extension.components.layout_components.STREAMLIT_AVAILABLE', True):
            SidebarSection.render_divider("Test Divider")
            
            mock_streamlit.sidebar.markdown.assert_called()
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_expandable_section_creation(self):
        """Test ExpandableSection creation."""
        section = ExpandableSection(
            title="Expandable Test",
            icon="📂",
            default_expanded=True,
            help_text="This is help text"
        )
        
        assert section.title == "Expandable Test"
        assert section.icon == "📂"
        assert section.default_expanded is True
        assert section.help_text == "This is help text"
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_expandable_section_render(self, mock_streamlit):
        """Test ExpandableSection rendering."""
        with patch('streamlit_extension.components.layout_components.STREAMLIT_AVAILABLE', True):
            mock_streamlit.expander.return_value.__enter__ = Mock(return_value=Mock())
            mock_streamlit.expander.return_value.__exit__ = Mock(return_value=None)
            
            section = ExpandableSection("Test Section", help_text="Help")
            
            with section.render():
                pass
            
            mock_streamlit.expander.assert_called_once()
            mock_streamlit.info.assert_called_once()  # For help text
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_tab_container_creation(self):
        """Test TabContainer creation."""
        tabs = ["Tab 1", "Tab 2", "Tab 3"]
        icons = ["📊", "📈", "📉"]
        
        container = TabContainer(tabs, icons, default_tab=1)
        
        assert container.tabs == tabs
        assert container.icons == icons
        assert container.default_tab == 1
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_tab_container_render(self, mock_streamlit):
        """Test TabContainer rendering."""
        with patch('streamlit_extension.components.layout_components.STREAMLIT_AVAILABLE', True):
            mock_tabs = [Mock(), Mock()]
            mock_streamlit.tabs.return_value = mock_tabs
            
            container = TabContainer(["Tab 1", "Tab 2"], ["📊", "📈"])
            result = container.render()
            
            assert result == mock_tabs
            mock_streamlit.tabs.assert_called_once()
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_layout_utility_functions(self, mock_streamlit):
        """Test layout utility functions."""
        with patch('streamlit_extension.components.layout_components.STREAMLIT_AVAILABLE', True):
            mock_streamlit.columns.return_value = [Mock(), Mock()]
            mock_streamlit.sidebar.__enter__ = Mock(return_value=Mock())
            mock_streamlit.sidebar.__exit__ = Mock(return_value=None)
            
            def left_content():
                pass
            
            def right_content():
                pass
            
            # Two column layout
            create_two_column_layout(left_content, right_content, ratio=[1, 2])
            mock_streamlit.columns.assert_called_with([1, 2])
            
            # Three column layout
            mock_streamlit.columns.return_value = [Mock(), Mock(), Mock()]
            
            def center_content():
                pass
            
            create_three_column_layout(left_content, center_content, right_content)
            mock_streamlit.columns.assert_called_with([1, 1, 1])  # Default ratio
    
    @pytest.mark.skipif(not LAYOUT_COMPONENTS_AVAILABLE, reason="Layout components not available")
    def test_fallback_rendering(self):
        """Test component fallback rendering without Streamlit."""
        with patch('streamlit_extension.components.layout_components.STREAMLIT_AVAILABLE', False):
            
            # Test CardContainer fallback
            card = CardContainer(title="Fallback Card")
            
            with capture_output() as output:
                with card.render():
                    print("Card content")
            
            result = output.getvalue()
            assert "=== Fallback Card ===" in result
            assert "Card content" in result
            
            # Test SidebarSection fallback
            section = SidebarSection("Fallback Section", icon="🧪")
            
            with capture_output() as output:
                with section.render():
                    print("Section content")
            
            result = output.getvalue()
            assert "[SIDEBAR] 🧪 Fallback Section" in result
            assert "Section content" in result


class TestComponentIntegration:
    """Test component integration and interoperability."""
    
    @pytest.mark.skipif(not (STATUS_COMPONENTS_AVAILABLE and LAYOUT_COMPONENTS_AVAILABLE), 
                       reason="Both component types not available")
    def test_components_in_card_layout(self, mock_streamlit=None):
        """Test using status components within card layouts."""
        if mock_streamlit is None:
            with patch('streamlit_extension.components.layout_components.st') as mock_st:
                mock_st.markdown = Mock()
                mock_streamlit = mock_st
        
        with patch('streamlit_extension.components.layout_components.STREAMLIT_AVAILABLE', True):
            with patch('streamlit_extension.components.status_components.STREAMLIT_AVAILABLE', True):
                
                card = CardContainer(title="Status Dashboard", style="info")
                
                def card_content():
                    # Use status components inside card
                    badge = StatusBadge("success")
                    badge.render("System Online")
                    
                    metric = MetricCard("CPU Usage", 85.2, delta=1.5, unit="%")
                    metric.render()
                
                card.render_content(card_content)
                
                # Both components should have been called
                mock_streamlit.markdown.assert_called()
    
    @pytest.mark.skipif(not (STATUS_COMPONENTS_AVAILABLE and LAYOUT_COMPONENTS_AVAILABLE),
                       reason="Both component types not available")  
    def test_components_responsive_behavior(self):
        """Test components behave correctly in different screen sizes."""
        # This would test responsive behavior
        # For now, we verify components can handle different parameters
        
        # Test status badge with different sizes
        badge = StatusBadge("info")
        
        # Should handle different size parameters
        with patch('streamlit_extension.components.status_components.STREAMLIT_AVAILABLE', True):
            with patch('streamlit_extension.components.status_components.st') as mock_st:
                mock_st.markdown = Mock()
                
                badge.render("Test", size="small")
                badge.render("Test", size="normal") 
                badge.render("Test", size="large")
                
                assert mock_st.markdown.call_count == 3
        
        # Test progress card with different widths
        progress = ProgressCard("Test Progress", 50, 100)
        
        with patch('streamlit_extension.components.status_components.STREAMLIT_AVAILABLE', True):
            with patch('streamlit_extension.components.status_components.st') as mock_st:
                mock_st.markdown = Mock()
                
                progress.render_mini(width=50)   # Small
                progress.render_mini(width=100)  # Default
                progress.render_mini(width=200)  # Large
                
                assert mock_st.markdown.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])