"""
📊 Dashboard Widget Components

Advanced visual components for the main dashboard:
- ProductivityHeatmap: Activity visualization
- ProgressRing: Circular progress indicators
- SparklineChart: Mini trend charts
- AchievementCard: Gamification displays
- NotificationToast: Alert system
- QuickActionButton: Fast action triggers
"""

from typing import Optional, Dict, Any, List, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import math
import re

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

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False


@dataclass
class NotificationData:
    """Data structure for notifications."""
    title: str
    message: str
    type: str  # 'info', 'success', 'warning', 'error'
    timestamp: datetime
    action_label: Optional[str] = None
    action_callback: Optional[callable] = None
    icon: Optional[str] = None


class ProductivityHeatmap:
    """Activity heatmap showing productivity over time."""
    
    @staticmethod
    def render(activity_data: Dict[str, int], title: str = "Activity Heatmap", 
              height: int = 150) -> None:
        """
        Render a productivity heatmap.
        
        Args:
            activity_data: Dict with date strings as keys and activity counts as values
            title: Title for the heatmap
            height: Height of the chart in pixels
        """
        if not STREAMLIT_AVAILABLE:
            return
        
        if not PLOTLY_AVAILABLE or not PANDAS_AVAILABLE:
            st.warning("📊 Install plotly and pandas for heatmap visualization")
            return
        
        if not activity_data:
            st.info("No activity data available")
            return
        
        # Prepare data for last 7 days
        today = datetime.now().date()
        dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        
        # Create data matrix
        values = []
        date_labels = []
        
        for date in dates:
            date_str = date.strftime("%Y-%m-%d")
            date_labels.append(date.strftime("%a\n%d"))
            values.append(activity_data.get(date_str, 0))
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=[values],
            x=date_labels,
            y=["Activity"],
            colorscale=[
                [0, "#f0f0f0"],
                [0.25, "#90EE90"],
                [0.5, "#32CD32"],
                [0.75, "#228B22"],
                [1, "#006400"]
            ],
            showscale=False,
            text=[[f"{v} tasks" for v in values]],
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>"
        ))
        
        fig.update_layout(
            title=title,
            height=height,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"heatmap_{title}")


class ProgressRing:
    """Circular progress indicator with percentage."""
    
    @staticmethod
    def render(progress: float, label: str = "", size: str = "medium", 
              color: str = "#00CC88") -> None:
        """
        Render a circular progress ring.
        
        Args:
            progress: Progress value between 0 and 1
            label: Label to display in center
            size: Size of the ring ('small', 'medium', 'large')
            color: Color of the progress ring
        """
        if not STREAMLIT_AVAILABLE:
            return
        
        progress = max(0, min(1, progress))  # Clamp between 0 and 1
        percentage = int(progress * 100)
        
        # Size configurations
        sizes = {
            "small": {"width": 80, "height": 80, "stroke": 8},
            "medium": {"width": 120, "height": 120, "stroke": 10},
            "large": {"width": 160, "height": 160, "stroke": 12}
        }
        
        config = sizes.get(size, sizes["medium"])
        radius = (config["width"] - config["stroke"]) / 2
        circumference = 2 * math.pi * radius
        stroke_dashoffset = circumference * (1 - progress)
        
        svg_html = f"""
        <div style="text-align: center;">
            <svg width="{config['width']}" height="{config['height']}" style="transform: rotate(-90deg);">
                <circle
                    cx="{config['width']/2}"
                    cy="{config['height']/2}"
                    r="{radius}"
                    stroke="#e0e0e0"
                    stroke-width="{config['stroke']}"
                    fill="none"
                />
                <circle
                    cx="{config['width']/2}"
                    cy="{config['height']/2}"
                    r="{radius}"
                    stroke="{color}"
                    stroke-width="{config['stroke']}"
                    fill="none"
                    stroke-dasharray="{circumference}"
                    stroke-dashoffset="{stroke_dashoffset}"
                    stroke-linecap="round"
                    style="transition: stroke-dashoffset 0.5s ease;"
                />
            </svg>
            <div style="margin-top: -60px; font-size: 24px; font-weight: bold; color: {color};">
                {percentage}%
            </div>
            {f'<div style="font-size: 14px; color: #666; margin-top: 5px;">{label}</div>' if label else ''}
        </div>
        """
        
        st.markdown(svg_html, unsafe_allow_html=True)


class SparklineChart:
    """Mini trend chart for inline data visualization."""
    
    @staticmethod
    def render(data: List[float], color: str = "#1f77b4",
              show_points: bool = False, height: int = 60) -> None:
        """
        Render a sparkline chart.
        
        Args:
            data: List of numerical values
            color: Line color
            show_points: Whether to show data points
            height: Height of the chart
        """
        if not STREAMLIT_AVAILABLE:
            return
        
        if not PLOTLY_AVAILABLE:
            # Fallback to simple text representation
            if data:
                trend = "↑" if data[-1] > data[0] else "↓" if data[-1] < data[0] else "→"
                st.text(f"Trend: {trend} ({data[0]:.1f} → {data[-1]:.1f})")
            return
        
        if not data:
            return
        
        fig = go.Figure()
        
        # garante hex para calcular fillcolor; caso contrário usa rgba default
        def _hex_to_rgba_fill(c: str, alpha: float = 0.1) -> str:
            if isinstance(c, str) and re.match(r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$", c):
                h = c[1:]
                if len(h) == 3:
                    h = "".join([ch * 2 for ch in h])
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                return f"rgba({r},{g},{b},{alpha})"
            return "rgba(31,119,180,0.1)"

        fig.add_trace(go.Scatter(
            y=data,
            x=list(range(len(data))),
            mode='lines+markers' if show_points else 'lines',
            line=dict(color=color, width=2),
            marker=dict(size=4, color=color) if show_points else None,
            fill='tozeroy',
            fillcolor=_hex_to_rgba_fill(color, 0.1),
            showlegend=False,
            hovertemplate="%{y:.1f}<extra></extra>"
        ))
        
        fig.update_layout(
            height=height,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            hovermode='x'
        )
        
        st.plotly_chart(fig, use_container_width=True)


class AchievementCard:
    """Display achievement or milestone cards."""
    
    @staticmethod
    def render(title: str, description: str, icon: str = "🏆", 
              progress: Optional[float] = None, unlocked: bool = True) -> None:
        """
        Render an achievement card.
        
        Args:
            title: Achievement title
            description: Achievement description
            icon: Icon/emoji for the achievement
            progress: Progress towards achievement (0-1)
            unlocked: Whether achievement is unlocked
        """
        if not STREAMLIT_AVAILABLE:
            return
        
        opacity = "1" if unlocked else "0.5"
        border_color = "#FFD700" if unlocked else "#cccccc"
        bg_color = "#FFF8DC" if unlocked else "#f5f5f5"
        
        card_html = f"""
        <div style="
            border: 2px solid {border_color};
            border-radius: 10px;
            padding: 15px;
            background-color: {bg_color};
            opacity: {opacity};
            transition: all 0.3s ease;
            margin: 10px 0;
        ">
            <div style="display: flex; align-items: center;">
                <div style="font-size: 40px; margin-right: 15px;">{icon}</div>
                <div style="flex-grow: 1;">
                    <div style="font-weight: bold; font-size: 16px;">{title}</div>
                    <div style="color: #666; font-size: 12px; margin-top: 5px;">{description}</div>
                    {f'''<div style="margin-top: 8px;">
                        <div style="background: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="background: #4CAF50; height: 100%; width: {progress*100}%; transition: width 0.5s ease;"></div>
                        </div>
                        <div style="font-size: 11px; color: #666; margin-top: 3px;">{int(progress*100)}% Complete</div>
                    </div>''' if progress is not None else ''}
                </div>
            </div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)


class NotificationToast:
    """Toast notification system."""
    
    @staticmethod
    def show(notification: NotificationData) -> None:
        """
        Show a toast notification.
        
        Args:
            notification: NotificationData object with notification details
        """
        if not STREAMLIT_AVAILABLE:
            return
        
        # Type to style mapping
        styles = {
            "success": {"bg": "#d4edda", "border": "#c3e6cb", "text": "#155724", "icon": "✅"},
            "error": {"bg": "#f8d7da", "border": "#f5c6cb", "text": "#721c24", "icon": "❌"},
            "warning": {"bg": "#fff3cd", "border": "#ffeaa7", "text": "#856404", "icon": "⚠️"},
            "info": {"bg": "#d1ecf1", "border": "#bee5eb", "text": "#0c5460", "icon": "ℹ️"}
        }
        
        style = styles.get(notification.type, styles["info"])
        icon = notification.icon or style["icon"]
        
        # Create columns for layout
        col1, col2, col3 = st.columns([1, 10, 1])
        
        with col2:
            toast_html = f"""
            <div style="
                background-color: {style['bg']};
                border: 1px solid {style['border']};
                border-radius: 8px;
                padding: 12px 15px;
                margin: 10px 0;
                color: {style['text']};
                animation: slideIn 0.3s ease;
            ">
                <div style="display: flex; align-items: start;">
                    <span style="font-size: 20px; margin-right: 10px;">{icon}</span>
                    <div style="flex-grow: 1;">
                        <div style="font-weight: bold; margin-bottom: 3px;">{notification.title}</div>
                        <div style="font-size: 14px;">{notification.message}</div>
                        <div style="font-size: 11px; color: #888; margin-top: 5px;">
                            {notification.timestamp.strftime("%H:%M:%S")}
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
                @keyframes slideIn {{
                    from {{
                        transform: translateX(100%);
                        opacity: 0;
                    }}
                    to {{
                        transform: translateX(0);
                        opacity: 1;
                    }}
                }}
            </style>
            """
            
            st.markdown(toast_html, unsafe_allow_html=True)
            
            if notification.action_label and notification.action_callback:
                if st.button(notification.action_label, key=f"notif_action_{notification.timestamp}"):
                    notification.action_callback()


class QuickActionButton:
    """Quick action buttons for common tasks."""
    
    @staticmethod
    def render(label: str, icon: str, callback: callable, 
              color: str = "primary", disabled: bool = False,
              tooltip: Optional[str] = None) -> bool:
        """
        Render a quick action button.
        
        Args:
            label: Button label
            icon: Icon/emoji for the button
            callback: Function to call on click
            color: Button color theme
            disabled: Whether button is disabled
            tooltip: Hover tooltip text
            
        Returns:
            True if button was clicked
        """
        if not STREAMLIT_AVAILABLE:
            return False
        
        # Color themes
        colors = {
            "primary": {"bg": "#0066cc", "hover": "#0052a3", "text": "white"},
            "success": {"bg": "#28a745", "hover": "#218838", "text": "white"},
            "warning": {"bg": "#ffc107", "hover": "#e0a800", "text": "black"},
            "danger": {"bg": "#dc3545", "hover": "#c82333", "text": "white"},
            "secondary": {"bg": "#6c757d", "hover": "#5a6268", "text": "white"}
        }
        
        theme = colors.get(color, colors["primary"])
        
        button_key = f"quick_action_{label}_{icon}"
        
        if tooltip:
            st.markdown(f"<span title='{tooltip}'>", unsafe_allow_html=True)
        
        button_html = f"""
        <style>
            .quick-action-{button_key} {{
                background-color: {theme['bg']};
                color: {theme['text']};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                cursor: {'not-allowed' if disabled else 'pointer'};
                opacity: {'0.5' if disabled else '1'};
                transition: all 0.3s ease;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                margin: 5px;
            }}
            
            .quick-action-{button_key}:hover {{
                background-color: {theme['hover'] if not disabled else theme['bg']};
                transform: {'none' if disabled else 'translateY(-2px)'};
                box-shadow: {'none' if disabled else '0 4px 8px rgba(0,0,0,0.2)'};
            }}
        </style>
        """
        
        st.markdown(button_html, unsafe_allow_html=True)
        
        clicked = st.button(
            f"{icon} {label}",
            key=button_key,
            disabled=disabled,
            on_click=callback if not disabled else None
        )
        
        if tooltip:
            st.markdown("</span>", unsafe_allow_html=True)
        
        return clicked


class DailyStats:
    """Display daily statistics in a compact format."""
    
    @staticmethod
    def render(stats: Dict[str, Any]) -> None:
        """
        Render daily statistics.
        
        Args:
            stats: Dictionary with statistics data
        """
        if not STREAMLIT_AVAILABLE:
            return
        
        # Default values
        tasks_completed = stats.get("tasks_completed", 0)
        focus_time = stats.get("focus_time_minutes", 0)
        streak_days = stats.get("streak_days", 0)
        achievements_unlocked = stats.get("achievements_today", 0)
        
        # Convert focus time to hours and minutes
        hours = focus_time // 60
        minutes = focus_time % 60
        time_display = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        # Create metrics layout
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📋 Tasks Done",
                value=tasks_completed,
                delta=f"+{tasks_completed}" if tasks_completed > 0 else None
            )
        
        with col2:
            st.metric(
                label="⏱️ Focus Time",
                value=time_display,
                delta="On track" if focus_time >= 120 else "Keep going"
            )
        
        with col3:
            st.metric(
                label="🔥 Streak",
                value=f"{streak_days} days",
                delta="Active" if streak_days > 0 else None
            )
        
        with col4:
            st.metric(
                label="🏆 Achievements",
                value=achievements_unlocked,
                delta=f"+{achievements_unlocked}" if achievements_unlocked > 0 else None
            )


class WelcomeHeader:
    """Dynamic welcome header with time-based greetings."""
    
    @staticmethod
    def render(username: str = "User") -> None:
        """
        Render a welcome header with dynamic greeting.
        
        Args:
            username: Name of the user
        """
        if not STREAMLIT_AVAILABLE:
            return
        
        now = datetime.now()
        hour = now.hour
        
        # Time-based greetings
        if hour < 5:
            greeting = "🌙 Late night coding"
            message = "Remember to rest!"
        elif hour < 12:
            greeting = "☀️ Good morning"
            message = "Ready to be productive?"
        elif hour < 17:
            greeting = "🌤️ Good afternoon"
            message = "Keep the momentum going!"
        elif hour < 21:
            greeting = "🌆 Good evening"
            message = "Time to wrap up tasks!"
        else:
            greeting = "🌃 Good night"
            message = "Don't forget to rest!"
        
        # Day of week motivation
        weekday = now.strftime("%A")
        motivations = {
            "Monday": "💪 Fresh start to the week!",
            "Tuesday": "🚀 Building momentum!",
            "Wednesday": "⚡ Halfway there!",
            "Thursday": "🎯 Almost Friday!",
            "Friday": "🎉 TGIF! Finish strong!",
            "Saturday": "🌈 Weekend productivity!",
            "Sunday": "🧘 Relax and recharge!"
        }
        
        motivation = motivations.get(weekday, "Keep going!")
        
        # Render header
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        ">
            <h2 style="margin: 0; color: white;">{greeting}, {username}!</h2>
            <p style="margin: 5px 0; opacity: 0.9;">{message}</p>
            <p style="margin: 0; font-size: 14px; opacity: 0.8;">
                {weekday} • {now.strftime("%B %d, %Y")} • {motivation}
            </p>
        </div>
        """, unsafe_allow_html=True)