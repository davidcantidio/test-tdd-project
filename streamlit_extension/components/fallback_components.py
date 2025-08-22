"""
🔄 Fallback Components

Fallback implementations for UI components when main components are unavailable.
Provides graceful degradation and consistent interfaces.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Safe streamlit import
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Import centralized safe_ui - NO FALLBACK NEEDED
from ..utils.streamlit_helpers import safe_ui
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


logger = logging.getLogger(__name__)

# === DASHBOARD WIDGET FALLBACKS ===============================================

class WelcomeHeader:
    """Fallback implementation for welcome header widget."""
    
    @staticmethod
    def render(username: str = "User", **kwargs) -> None:
        """
        Render welcome header fallback.
        
        Args:
            username: Username to display
            **kwargs: Additional arguments (ignored in fallback)
        """
        safe_ui(lambda: st.markdown(f"### 👋 Bem-vindo, {username}!"))

class DailyStats:
    """Fallback implementation for daily statistics widget."""
    
    @staticmethod
    def render(stats: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """
        Render daily stats fallback.
        
        Args:
            stats: Statistics data (ignored in fallback)
            **kwargs: Additional arguments (ignored in fallback)
        """
        safe_ui(lambda: st.write("📊 Estatísticas diárias indisponíveis."))

class ProductivityHeatmap:
    """Fallback implementation for productivity heatmap widget."""
    
    @staticmethod
    def render(activity_data: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """
        Render heatmap fallback.
        
        Args:
            activity_data: Activity data (ignored in fallback)
            **kwargs: Additional arguments (ignored in fallback)
        """
        safe_ui(lambda: st.write("🗓️ Heatmap indisponível."))

def ProgressRing(*args, **kwargs) -> None:
    """Fallback implementation for progress ring widget."""
    safe_ui(lambda: st.write("📈 Progresso indisponível."))

def SparklineChart(*args, **kwargs) -> None:
    """Fallback implementation for sparkline chart widget."""
    safe_ui(lambda: st.write("📉 Sparkline indisponível."))

def AchievementCard(*args, **kwargs) -> None:
    """Fallback implementation for achievement card widget."""
    safe_ui(lambda: st.write("🏆 Conquistas indisponíveis."))

def QuickActionButton(*args, **kwargs) -> None:
    """Fallback implementation for quick action button widget."""
    safe_ui(lambda: st.button("Ação"))

# === NOTIFICATION SYSTEM FALLBACKS ============================================

@dataclass
class NotificationData:
    """Data class for notification information."""
    
    title: str = ""
    message: str = ""
    type: str = "info"  # info, success, warning, error
    icon: str = "🔔"  # Default notification icon
    timestamp: datetime = field(default_factory=datetime.now)
    action_label: Optional[str] = None
    action_callback: Optional[callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "message": self.message,
            "type": self.type,
            "icon": self.icon,
            "timestamp": self.timestamp.isoformat()
        }

class NotificationToast:
    """Fallback implementation for notification toast widget."""
    
    @staticmethod
    def show(notification: Optional[NotificationData] = None, **kwargs) -> None:
        """
        Show notification toast fallback.
        
        Args:
            notification: Notification data to display
            **kwargs: Additional arguments (ignored in fallback)
        """
        def _show():
            if notification and getattr(notification, "message", None):
                message = f"🔔 {notification.message}"
                
                # Show notification based on type
                if notification.type == "success":
                    st.success(message)
                elif notification.type == "warning":
                    st.warning(message)
                elif notification.type == "error":
                    st.error(message)
                else:
                    st.info(message)
            else:
                st.info("🔔 Notificações indisponíveis.")
        
        safe_ui(_show)

# === TIMER COMPONENT FALLBACKS ================================================

class TimerComponent:
    """Fallback implementation for timer component."""
    
    def __init__(self):
        """Initialize timer component fallback."""
        self.is_running = False
        self.duration = 25  # Default 25 minutes
        self.remaining = self.duration * 60  # Convert to seconds
    
    def render(self) -> None:
        """Render timer component fallback."""
        def _render():
            st.write("⏱️ Timer Component (Fallback Mode)")
            st.info("Timer functionality indisponível. Componente principal não carregado.")
            
            # Basic timer controls fallback
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("▶️ Start" if not self.is_running else "⏸️ Pause"):
                    self.is_running = not self.is_running
            
            with col2:
                if st.button("⏹️ Stop"):
                    self.is_running = False
                    self.remaining = self.duration * 60
            
            with col3:
                st.write(f"⏱ {self.remaining // 60:02d}:{self.remaining % 60:02d}")
        
        safe_ui(_render)

# === FORM COMPONENT FALLBACKS =================================================

class StandardForm:
    """Fallback implementation for standard form component."""
    
    @staticmethod
    def render(fields: List[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Render standard form fallback.
        
        Args:
            fields: Form field definitions
            **kwargs: Additional form options
            
        Returns:
            Form result dictionary
        """
        if not STREAMLIT_AVAILABLE:
            return {"submitted": False, "valid": False, "data": {}}
        
        try:
            st.info("📝 Formulário padrão indisponível (modo fallback)")
            
            with st.form("fallback_form"):
                st.text_input("Campo de exemplo", disabled=True)
                submitted = st.form_submit_button("Enviar (Indisponível)")
            
            return {
                "submitted": False,
                "valid": False, 
                "data": {},
                "errors": ["Form component not available"]
            }
        
        except Exception as e:
            logger.error(f"Error in StandardForm fallback: {e}")
            return {"submitted": False, "valid": False, "data": {}, "errors": [str(e)]}

class ClientForm:
    """Fallback implementation for client form component."""
    
    @staticmethod
    def render(data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Render client form fallback."""
        return StandardForm.render(fields=[
            {"name": "name", "type": "text", "label": "Nome"},
            {"name": "email", "type": "email", "label": "Email"}
        ])

class ProjectForm:
    """Fallback implementation for project form component."""
    
    @staticmethod
    def render(data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Render project form fallback."""
        return StandardForm.render(fields=[
            {"name": "name", "type": "text", "label": "Nome do Projeto"},
            {"name": "description", "type": "textarea", "label": "Descrição"}
        ])

# === CHART AND ANALYTICS FALLBACKS ============================================

class AnalyticsChart:
    """Fallback implementation for analytics charts."""
    
    @staticmethod
    def render_bar_chart(data: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Render bar chart fallback."""
        safe_ui(lambda: st.info("📊 Gráfico de barras indisponível"))
    
    @staticmethod
    def render_line_chart(data: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Render line chart fallback."""
        safe_ui(lambda: st.info("📈 Gráfico de linha indisponível"))
    
    @staticmethod
    def render_pie_chart(data: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Render pie chart fallback."""
        safe_ui(lambda: st.info("🥧 Gráfico de pizza indisponível"))

class MetricCard:
    """Fallback implementation for metric cards."""
    
    @staticmethod
    def render(title: str, value: Any, delta: Optional[Any] = None, **kwargs) -> None:
        """
        Render metric card fallback.
        
        Args:
            title: Metric title
            value: Metric value
            delta: Change indicator
            **kwargs: Additional options
        """
        def _render():
            st.metric(
                label=title,
                value=str(value) if value is not None else "N/A",
                delta=str(delta) if delta is not None else None
            )
        
        safe_ui(_render)

# === NAVIGATION FALLBACKS =====================================================

class NavigationMenu:
    """Fallback implementation for navigation menu."""
    
    @staticmethod
    def render(items: List[Dict[str, Any]] = None, **kwargs) -> Optional[str]:
        """
        Render navigation menu fallback.
        
        Args:
            items: Menu item definitions
            **kwargs: Additional options
            
        Returns:
            Selected menu item or None
        """
        if not STREAMLIT_AVAILABLE:
            return None
        
        try:
            st.info("🧭 Menu de navegação indisponível (modo fallback)")
            
            # Basic navigation fallback
            default_items = [
                {"label": "Dashboard", "value": "dashboard"},
                {"label": "Clients", "value": "clients"},
                {"label": "Projects", "value": "projects"}
            ]
            
            menu_items = items or default_items
            labels = [item.get("label", "Item") for item in menu_items]
            
            if labels:
                selected_index = st.selectbox(
                    "Navegação",
                    range(len(labels)),
                    format_func=lambda x: labels[x]
                )
                
                return menu_items[selected_index].get("value", "dashboard")
            
            return "dashboard"
        
        except Exception as e:
            logger.error(f"Error in NavigationMenu fallback: {e}")
            return "dashboard"

# === FALLBACK REGISTRY ========================================================

class FallbackRegistry:
    """Registry for managing fallback components."""
    
    _fallbacks: Dict[str, Any] = {
        # Dashboard widgets
        "WelcomeHeader": WelcomeHeader,
        "DailyStats": DailyStats,
        "ProductivityHeatmap": ProductivityHeatmap,
        "ProgressRing": ProgressRing,
        "SparklineChart": SparklineChart,
        "AchievementCard": AchievementCard,
        "QuickActionButton": QuickActionButton,
        
        # Notification system
        "NotificationData": NotificationData,
        "NotificationToast": NotificationToast,
        
        # Timer
        "TimerComponent": TimerComponent,
        
        # Forms
        "StandardForm": StandardForm,
        "ClientForm": ClientForm,
        "ProjectForm": ProjectForm,
        
        # Charts and analytics
        "AnalyticsChart": AnalyticsChart,
        "MetricCard": MetricCard,
        
        # Navigation
        "NavigationMenu": NavigationMenu
    }
    
    @classmethod
    def get_fallback(cls, component_name: str) -> Optional[Any]:
        """Get fallback implementation for a component."""
        return cls._fallbacks.get(component_name)
    
    @classmethod
    def register_fallback(cls, component_name: str, fallback_class: Any) -> None:
        """Register a new fallback component."""
        cls._fallbacks[component_name] = fallback_class
    
    @classmethod
    def list_fallbacks(cls) -> List[str]:
        """List all available fallback components."""
        return list(cls._fallbacks.keys())

# === HEALTH CHECK =============================================================

def check_fallback_components_health() -> Dict[str, Any]:
    """Check health of fallback components system."""
    return {
        "streamlit_available": STREAMLIT_AVAILABLE,
        "registered_fallbacks": len(FallbackRegistry._fallbacks),
        "available_components": FallbackRegistry.list_fallbacks(),
        "safe_ui_functional": callable(safe_ui),
        "status": "healthy" if STREAMLIT_AVAILABLE else "degraded"
    }

# === EXPORTS ==================================================================

__all__ = [
    # Safe UI helper
    "safe_ui",
    
    # Dashboard widgets
    "WelcomeHeader",
    "DailyStats",
    "ProductivityHeatmap",
    "ProgressRing",
    "SparklineChart", 
    "AchievementCard",
    "QuickActionButton",
    
    # Notification system
    "NotificationData",
    "NotificationToast",
    
    # Timer
    "TimerComponent",
    
    # Forms
    "StandardForm",
    "ClientForm", 
    "ProjectForm",
    
    # Charts and analytics
    "AnalyticsChart",
    "MetricCard",
    
    # Navigation
    "NavigationMenu",
    
    # Registry
    "FallbackRegistry",
    
    # Health check
    "check_fallback_components_health",
]