"""
📊 Status Components for Streamlit Extension

Reusable status indicators, badges, and metric display components:
- StatusBadge: Colored status indicators with icons
- ProgressCard: Progress bars with contextual information
- MetricCard: Key performance indicators with deltas and trends
"""

from typing import Optional, Dict, Any, Union, List
from dataclasses import dataclass
from datetime import datetime

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    st = None
    STREAMLIT_AVAILABLE = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    px = go = None
    PLOTLY_AVAILABLE = False


@dataclass
class StatusConfig:
    """Configuration for status badges."""
    color: str
    icon: str
    text_color: str = "black"
    background_alpha: float = 0.1


# Predefined status configurations
STATUS_CONFIGS = {
    "success": StatusConfig("green", "✅", "green"),
    "warning": StatusConfig("orange", "⚠️", "orange"), 
    "error": StatusConfig("red", "❌", "red"),
    "info": StatusConfig("blue", "ℹ️", "blue"),
    "pending": StatusConfig("gray", "⏳", "gray"),
    "in_progress": StatusConfig("yellow", "🔄", "#B8860B"),
    "completed": StatusConfig("green", "✅", "green"),
    "failed": StatusConfig("red", "🚫", "red"),
    "paused": StatusConfig("orange", "⏸️", "orange"),
    "active": StatusConfig("blue", "🟢", "blue"),
    "inactive": StatusConfig("gray", "⚪", "gray")
}


class StatusBadge:
    """Reusable status badge component with consistent styling."""
    
    def __init__(self, status: str, custom_config: Optional[StatusConfig] = None):
        self.status = status
        self.config = custom_config or STATUS_CONFIGS.get(status, STATUS_CONFIGS["info"])
    
    def render(self, text: str = None, show_icon: bool = True, size: str = "normal") -> None:
        """Render the status badge."""
        if not STREAMLIT_AVAILABLE:
            print(f"[{self.status.upper()}] {text or self.status}")
            return
        
        display_text = text or self.status.replace("_", " ").title()
        icon_part = f"{self.config.icon} " if show_icon else ""
        
        # Size variations
        if size == "small":
            font_size = "12px"
            padding = "2px 6px"
        elif size == "large":
            font_size = "16px"
            padding = "8px 12px"
        else:  # normal
            font_size = "14px"
            padding = "4px 8px"
        
        # Create badge HTML
        badge_html = f"""
        <div style="
            display: inline-block;
            background-color: {self.config.color}{hex(int(255 * self.config.background_alpha))[2:].zfill(2)};
            color: {self.config.text_color};
            border: 1px solid {self.config.color};
            border-radius: 12px;
            padding: {padding};
            font-size: {font_size};
            font-weight: 500;
            margin: 2px;
        ">
            {icon_part}{display_text}
        </div>
        """
        
        st.markdown(badge_html, unsafe_allow_html=True)
    
    @staticmethod
    def render_list(statuses: List[str], texts: Optional[List[str]] = None, 
                   show_icons: bool = True, size: str = "normal") -> None:
        """Render multiple status badges in a row."""
        if not STREAMLIT_AVAILABLE:
            for i, status in enumerate(statuses):
                text = texts[i] if texts and i < len(texts) else status
                print(f"[{status.upper()}] {text}")
            return
        
        badges_html = ""
        for i, status in enumerate(statuses):
            text = texts[i] if texts and i < len(texts) else None
            badge = StatusBadge(status)
            config = badge.config
            
            display_text = text or status.replace("_", " ").title()
            icon_part = f"{config.icon} " if show_icons else ""
            
            # Size variations
            if size == "small":
                font_size = "12px"
                padding = "2px 6px"
            elif size == "large":
                font_size = "16px"
                padding = "8px 12px"
            else:  # normal
                font_size = "14px"
                padding = "4px 8px"
            
            badges_html += f"""
            <div style="
                display: inline-block;
                background-color: {config.color}{hex(int(255 * config.background_alpha))[2:].zfill(2)};
                color: {config.text_color};
                border: 1px solid {config.color};
                border-radius: 12px;
                padding: {padding};
                font-size: {font_size};
                font-weight: 500;
                margin: 2px;
            ">
                {icon_part}{display_text}
            </div>
            """
        
        st.markdown(f'<div style="line-height: 2;">{badges_html}</div>', unsafe_allow_html=True)


class ProgressCard:
    """Progress card with contextual information and styling."""
    
    def __init__(self, title: str, current: Union[int, float], total: Union[int, float],
                 description: str = None, show_percentage: bool = True):
        self.title = title
        self.current = current
        self.total = total
        self.description = description
        self.show_percentage = show_percentage
        self.percentage = (current / total * 100) if total > 0 else 0
    
    def render(self, color_scheme: str = "blue", show_numbers: bool = True,
              height: int = 20) -> None:
        """Render the progress card."""
        if not STREAMLIT_AVAILABLE:
            print(f"{self.title}: {self.current}/{self.total} ({self.percentage:.1f}%)")
            if self.description:
                print(f"  {self.description}")
            return
        
        # Color schemes
        colors = {
            "blue": "#1f77b4",
            "green": "#2ca02c", 
            "red": "#d62728",
            "orange": "#ff7f0e",
            "purple": "#9467bd",
            "gray": "#7f7f7f"
        }
        
        color = colors.get(color_scheme, colors["blue"])
        
        # Create card container
        with st.container():
            st.markdown(f"**{self.title}**")
            
            if self.description:
                st.markdown(f"*{self.description}*")
            
            # Progress bar
            progress_html = f"""
            <div style="
                width: 100%;
                background-color: #f0f0f0;
                border-radius: 10px;
                overflow: hidden;
                height: {height}px;
                margin: 8px 0;
            ">
                <div style="
                    width: {self.percentage}%;
                    background-color: {color};
                    height: 100%;
                    transition: width 0.3s ease-in-out;
                "></div>
            </div>
            """
            
            st.markdown(progress_html, unsafe_allow_html=True)
            
            # Numbers and percentage
            if show_numbers or self.show_percentage:
                col1, col2 = st.columns(2)
                
                if show_numbers:
                    with col1:
                        st.markdown(f"**{self.current:,}** / {self.total:,}")
                
                if self.show_percentage:
                    with col2:
                        st.markdown(f"**{self.percentage:.1f}%**")
    
    def render_mini(self, width: int = 100) -> None:
        """Render a compact version of the progress card."""
        if not STREAMLIT_AVAILABLE:
            print(f"{self.title}: {self.percentage:.1f}%")
            return
        
        progress_html = f"""
        <div style="display: inline-block; margin: 4px;">
            <div style="font-size: 12px; margin-bottom: 2px;">{self.title}</div>
            <div style="
                width: {width}px;
                background-color: #f0f0f0;
                border-radius: 8px;
                overflow: hidden;
                height: 8px;
            ">
                <div style="
                    width: {self.percentage}%;
                    background-color: #1f77b4;
                    height: 100%;
                "></div>
            </div>
            <div style="font-size: 10px; color: #666;">{self.percentage:.0f}%</div>
        </div>
        """
        
        st.markdown(progress_html, unsafe_allow_html=True)


class MetricCard:
    """Enhanced metric display with trends and deltas."""
    
    def __init__(self, title: str, value: Union[int, float, str], 
                 delta: Optional[Union[int, float]] = None,
                 delta_color: Optional[str] = None,
                 unit: str = "", prefix: str = "", suffix: str = ""):
        self.title = title
        self.value = value
        self.delta = delta
        self.delta_color = delta_color
        self.unit = unit
        self.prefix = prefix
        self.suffix = suffix
    
    def render(self, layout: str = "default", show_chart: bool = False,
              chart_data: Optional[List[Union[int, float]]] = None) -> None:
        """Render the metric card with various layout options."""
        if not STREAMLIT_AVAILABLE:
            print(f"{self.title}: {self.prefix}{self.value}{self.unit}{self.suffix}")
            if self.delta is not None:
                print(f"  Delta: {self.delta:+}")
            return
        
        if layout == "compact":
            self._render_compact()
        elif layout == "detailed":
            self._render_detailed(show_chart, chart_data)
        else:
            self._render_default()
    
    def _render_default(self) -> None:
        """Render standard Streamlit metric."""
        formatted_value = f"{self.prefix}{self.value}{self.unit}{self.suffix}"
        
        delta_value = None
        delta_color = "normal"
        
        if self.delta is not None:
            delta_value = f"{self.delta:+}{self.unit}"
            if self.delta_color:
                delta_color = self.delta_color
            elif self.delta > 0:
                delta_color = "normal"
            elif self.delta < 0:
                delta_color = "inverse"
        
        st.metric(
            label=self.title,
            value=formatted_value,
            delta=delta_value,
            delta_color=delta_color
        )
    
    def _render_compact(self) -> None:
        """Render compact horizontal layout."""
        formatted_value = f"{self.prefix}{self.value}{self.unit}{self.suffix}"
        
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.markdown(f"**{self.title}**")
        
        with col2:
            st.markdown(f"**{formatted_value}**")
        
        with col3:
            if self.delta is not None:
                color = "green" if self.delta >= 0 else "red"
                icon = "📈" if self.delta >= 0 else "📉"
                st.markdown(f"<span style='color: {color}'>{icon} {self.delta:+}</span>", 
                           unsafe_allow_html=True)
    
    def _render_detailed(self, show_chart: bool = False, 
                        chart_data: Optional[List[Union[int, float]]] = None) -> None:
        """Render detailed card with optional sparkline chart."""
        formatted_value = f"{self.prefix}{self.value}{self.unit}{self.suffix}"
        
        # Create bordered container
        with st.container():
            st.markdown(f"""
            <div style="
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 16px;
                margin: 8px 0;
            ">
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"### {self.title}")
                st.markdown(f"# {formatted_value}")
                
                if self.delta is not None:
                    color = "green" if self.delta >= 0 else "red"
                    icon = "▲" if self.delta >= 0 else "▼"
                    st.markdown(f"<span style='color: {color}; font-size: 16px;'>{icon} {self.delta:+}{self.unit}</span>", 
                               unsafe_allow_html=True)
            
            with col2:
                if show_chart and chart_data and PLOTLY_AVAILABLE:
                    # Create mini sparkline
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        y=chart_data,
                        mode='lines',
                        line=dict(color='#1f77b4', width=2),
                        showlegend=False
                    ))
                    fig.update_layout(
                        height=80,
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis=dict(visible=False),
                        yaxis=dict(visible=False),
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    @staticmethod
    def render_grid(metrics: List['MetricCard'], columns: int = 3) -> None:
        """Render multiple metrics in a grid layout."""
        if not STREAMLIT_AVAILABLE:
            for metric in metrics:
                metric.render()
            return
        
        cols = st.columns(columns)
        
        for i, metric in enumerate(metrics):
            with cols[i % columns]:
                metric.render()


# Utility functions for quick metric creation
def create_percentage_metric(title: str, current: Union[int, float], total: Union[int, float]) -> MetricCard:
    """Create a percentage-based metric."""
    percentage = (current / total * 100) if total > 0 else 0
    return MetricCard(title, f"{percentage:.1f}", unit="%")

def create_count_metric(title: str, count: int, delta: Optional[int] = None) -> MetricCard:
    """Create a simple count metric."""
    return MetricCard(title, f"{count:,}", delta=delta)

def create_time_metric(title: str, minutes: Union[int, float], delta: Optional[Union[int, float]] = None) -> MetricCard:
    """Create a time-based metric."""
    if minutes >= 60:
        hours = minutes / 60
        return MetricCard(title, f"{hours:.1f}", delta=delta/60 if delta else None, unit="h")
    else:
        return MetricCard(title, f"{minutes:.0f}", delta=delta, unit="m")

def create_score_metric(title: str, score: Union[int, float], max_score: Union[int, float] = 10) -> MetricCard:
    """Create a score metric with rating context."""
    return MetricCard(title, f"{score:.1f}", unit=f"/{max_score}")


# Export for convenience
__all__ = [
    "StatusBadge", "ProgressCard", "MetricCard", "StatusConfig", "STATUS_CONFIGS",
    "create_percentage_metric", "create_count_metric", "create_time_metric", "create_score_metric"
]