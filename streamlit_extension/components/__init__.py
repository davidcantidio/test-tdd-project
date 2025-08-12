"""
🎨 Reusable UI Components for Streamlit Extension

Enhanced, reusable UI components that maintain consistency across pages:
- Status indicators and badges
- Card layouts and containers  
- Progress bars and metrics
- Interactive buttons and controls
- Data visualization wrappers
- Form components and validators
- Existing components (sidebar, timer)
"""

# Existing components
from .sidebar import render_sidebar
from .timer import TimerComponent

# New component graceful imports
try:
    from .status_components import StatusBadge, ProgressCard, MetricCard
    STATUS_COMPONENTS_AVAILABLE = True
except ImportError:
    StatusBadge = ProgressCard = MetricCard = None
    STATUS_COMPONENTS_AVAILABLE = False

try:
    from .layout_components import CardContainer, SidebarSection, ExpandableSection
    LAYOUT_COMPONENTS_AVAILABLE = True
except ImportError:
    CardContainer = SidebarSection = ExpandableSection = None
    LAYOUT_COMPONENTS_AVAILABLE = False

try:
    from .form_components import ValidatedInput, ConfigurationForm, ButtonGroup
    FORM_COMPONENTS_AVAILABLE = True
except ImportError:
    ValidatedInput = ConfigurationForm = ButtonGroup = None
    FORM_COMPONENTS_AVAILABLE = False

try:
    from .chart_components import ChartWrapper, DataTable, MiniChart
    CHART_COMPONENTS_AVAILABLE = True
except ImportError:
    ChartWrapper = DataTable = MiniChart = None
    CHART_COMPONENTS_AVAILABLE = False

# Component registry for discovery
COMPONENT_REGISTRY = {
    "existing": {
        "available": True,
        "components": ["render_sidebar", "TimerComponent"],
        "description": "Original framework components"
    },
    "status": {
        "available": STATUS_COMPONENTS_AVAILABLE,
        "components": ["StatusBadge", "ProgressCard", "MetricCard"],
        "description": "Status indicators, progress bars, and metric displays"
    },
    "layout": {
        "available": LAYOUT_COMPONENTS_AVAILABLE,
        "components": ["CardContainer", "SidebarSection", "ExpandableSection"],
        "description": "Layout containers and structural components"
    },
    "forms": {
        "available": FORM_COMPONENTS_AVAILABLE,
        "components": ["ValidatedInput", "ConfigurationForm", "ButtonGroup"],
        "description": "Form controls with validation and grouping"
    },
    "charts": {
        "available": CHART_COMPONENTS_AVAILABLE,
        "components": ["ChartWrapper", "DataTable", "MiniChart"],
        "description": "Data visualization and table components"
    }
}

def get_available_components():
    """Get list of available component categories."""
    return {
        cat_id: cat_info 
        for cat_id, cat_info in COMPONENT_REGISTRY.items() 
        if cat_info["available"]
    }

def get_component_status():
    """Get status of all component categories."""
    status = {}
    for cat_id, cat_info in COMPONENT_REGISTRY.items():
        status[cat_id] = {
            "available": cat_info["available"],
            "component_count": len(cat_info["components"]),
            "description": cat_info["description"]
        }
    return status

__all__ = [
    # Existing components
    "render_sidebar", "TimerComponent",
    # New components
    "StatusBadge", "ProgressCard", "MetricCard",
    "CardContainer", "SidebarSection", "ExpandableSection", 
    "ValidatedInput", "ConfigurationForm", "ButtonGroup",
    "ChartWrapper", "DataTable", "MiniChart",
    # Registry and utilities
    "COMPONENT_REGISTRY", "get_available_components", "get_component_status",
    "STATUS_COMPONENTS_AVAILABLE", "LAYOUT_COMPONENTS_AVAILABLE", 
    "FORM_COMPONENTS_AVAILABLE", "CHART_COMPONENTS_AVAILABLE"
]