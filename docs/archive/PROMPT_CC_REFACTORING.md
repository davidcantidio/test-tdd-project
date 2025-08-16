# 🤖 PROMPT CC: FUNCTION REFACTORING ANALYTICS

## 🎯 OBJECTIVE
Refactor large functions (>100 lines) in analytics.py to reduce cyclomatic complexity and improve maintainability, addressing report.md requirement: "Functions exceed 100 lines leading to high cyclomatic complexity."

## 📁 FILE TO MODIFY
- `streamlit_extension/pages/analytics.py` (REFACTOR ONLY - MAINTAIN FUNCTIONALITY)

## 🔍 FUNCTIONS TO REFACTOR

Based on analysis, these functions exceed 100 lines and need refactoring:

### 1. `render_analytics_page()` (~280 lines)
**Current Issues:**
- Handles UI layout, data fetching, filtering, and multiple chart rendering
- High cyclomatic complexity due to multiple conditional branches
- Difficult to test individual components

**Refactoring Strategy:**
```python
def render_analytics_page():
    """Main analytics page with modular architecture."""
    # Initialize components
    analytics_engine = _initialize_analytics_engine()
    db_manager = _get_database_manager()
    
    # Render UI sections
    filters = _render_analytics_filters()
    analytics_data = _fetch_analytics_data(db_manager, filters)
    
    # Display components
    _render_analytics_header(analytics_data)
    _render_analytics_tabs(analytics_data, analytics_engine)
    _render_analytics_footer()

def _initialize_analytics_engine():
    """Initialize analytics engine with proper configuration."""
    # Implementation here (15-20 lines)

def _render_analytics_filters() -> Dict[str, Any]:
    """Render filter sidebar and return selected filters.""" 
    # Implementation here (25-30 lines)

def _fetch_analytics_data(db_manager, filters: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch and process analytics data based on filters."""
    # Implementation here (30-35 lines)

def _render_analytics_header(analytics_data: Dict[str, Any]):
    """Render analytics page header with key metrics."""
    # Implementation here (20-25 lines)

def _render_analytics_tabs(analytics_data: Dict[str, Any], analytics_engine):
    """Render tabbed interface for different analytics views."""
    # Implementation here (40-50 lines)

def _render_analytics_footer():
    """Render analytics page footer with export options."""
    # Implementation here (15-20 lines)
```

### 2. `_render_productivity_chart()` (~170 lines)  
**Current Issues:**
- Mixes data processing with chart configuration
- Complex conditional logic for different chart types
- Difficult to maintain chart options

**Refactoring Strategy:**
```python
def _render_productivity_chart(analytics_data: Dict[str, Any]):
    """Render productivity charts with modular data processing."""
    chart_data = _process_productivity_data(analytics_data)
    chart_config = _get_productivity_chart_config()
    
    _display_productivity_metrics(chart_data)
    _display_productivity_charts(chart_data, chart_config)

def _process_productivity_data(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process raw analytics data for productivity visualization."""
    # Data processing logic (40-50 lines)

def _get_productivity_chart_config() -> Dict[str, Any]:
    """Get chart configuration for productivity visualizations.""" 
    # Chart config logic (25-30 lines)

def _display_productivity_metrics(chart_data: Dict[str, Any]):
    """Display key productivity metrics in cards."""
    # Metrics display logic (30-35 lines)

def _display_productivity_charts(chart_data: Dict[str, Any], config: Dict[str, Any]):
    """Display productivity charts with given configuration."""
    # Chart rendering logic (50-60 lines)
```

### 3. `_render_focus_time_chart()` (~130 lines)
**Current Issues:**
- Complex data aggregation mixed with UI rendering
- Multiple chart types in single function
- Hard to test data processing separately

**Refactoring Strategy:**
```python
def _render_focus_time_chart(analytics_data: Dict[str, Any]):
    """Render focus time analysis charts.""" 
    focus_data = _aggregate_focus_time_data(analytics_data)
    
    _render_focus_summary(focus_data)
    _render_focus_trends(focus_data)
    _render_focus_patterns(focus_data)

def _aggregate_focus_time_data(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate and calculate focus time metrics."""
    # Data aggregation logic (40-45 lines)

def _render_focus_summary(focus_data: Dict[str, Any]):
    """Render focus time summary metrics."""
    # Summary rendering (25-30 lines)

def _render_focus_trends(focus_data: Dict[str, Any]):
    """Render focus time trend charts."""
    # Trend chart logic (35-40 lines)

def _render_focus_patterns(focus_data: Dict[str, Any]):
    """Render focus pattern analysis."""
    # Pattern analysis (25-30 lines)
```

### 4. `_render_tdd_phase_distribution()` (~120 lines)
**Refactoring Strategy:**
```python
def _render_tdd_phase_distribution(analytics_data: Dict[str, Any]):
    """Render TDD phase distribution analysis."""
    tdd_data = _calculate_tdd_metrics(analytics_data)
    
    _render_tdd_overview(tdd_data)
    _render_tdd_phase_chart(tdd_data)
    _render_tdd_recommendations(tdd_data)

def _calculate_tdd_metrics(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate TDD phase metrics and balance scores."""
    # TDD calculations (35-40 lines)

def _render_tdd_overview(tdd_data: Dict[str, Any]):
    """Render TDD overview metrics."""
    # Overview rendering (25-30 lines)

def _render_tdd_phase_chart(tdd_data: Dict[str, Any]):
    """Render TDD phase distribution chart."""
    # Chart rendering (30-35 lines)

def _render_tdd_recommendations(tdd_data: Dict[str, Any]):
    """Render TDD improvement recommendations."""
    # Recommendations logic (25-30 lines)
```

### 5. `_render_epic_progress_chart()` (~150 lines)
**Refactoring Strategy:**
```python
def _render_epic_progress_chart(analytics_data: Dict[str, Any]):
    """Render epic progress visualization."""
    progress_data = _calculate_epic_progress(analytics_data)
    
    _render_progress_overview(progress_data)
    _render_progress_charts(progress_data)
    _render_progress_details(progress_data)

def _calculate_epic_progress(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate epic progress metrics and completion rates."""
    # Progress calculations (45-50 lines)

def _render_progress_overview(progress_data: Dict[str, Any]):
    """Render epic progress overview."""
    # Overview rendering (30-35 lines)

def _render_progress_charts(progress_data: Dict[str, Any]):
    """Render epic progress charts."""
    # Chart rendering (40-45 lines)

def _render_progress_details(progress_data: Dict[str, Any]):
    """Render detailed epic progress information."""
    # Details rendering (30-35 lines)
```

## 📋 REFACTORING PRINCIPLES

### 1. Single Responsibility Principle
- Each function should have ONE clear purpose
- Separate data processing from UI rendering
- Extract configuration from logic

### 2. Function Size Guidelines
- **Target: <50 lines per function**
- **Maximum: 80 lines per function**
- **Helper functions: 15-30 lines**

### 3. Naming Conventions
- `_process_*`: Data processing functions
- `_calculate_*`: Calculation functions  
- `_render_*`: UI rendering functions
- `_get_*`: Configuration/setup functions
- `_display_*`: Display helper functions

### 4. Data Flow Pattern
```python
# Main function coordinates the flow
def main_function(data):
    processed_data = _process_raw_data(data)
    config = _get_configuration()
    _render_components(processed_data, config)

# Processing functions transform data
def _process_raw_data(data) -> ProcessedData:
    # Pure data transformation

# Configuration functions return settings
def _get_configuration() -> Config:
    # Return configuration objects

# Rendering functions display UI
def _render_components(data, config):
    # Display logic only
```

## ✅ REQUIREMENTS

1. **Maintain 100% functionality** - All features must work identically
2. **Reduce function complexity** - No function >80 lines
3. **Improve testability** - Separate data processing from UI
4. **Keep imports unchanged** - Don't modify import statements
5. **Preserve performance** - No performance degradation
6. **Add docstrings** - Document new helper functions
7. **Maintain code style** - Follow existing patterns

## 🚫 WHAT NOT TO CHANGE
- Function signatures of public functions
- Import statements
- Global variables or constants
- Streamlit component behavior
- Chart output or appearance
- Data processing logic (only reorganize)

## ✅ VERIFICATION CHECKLIST
- [ ] No function exceeds 80 lines
- [ ] All original functionality preserved
- [ ] New helper functions have docstrings
- [ ] Data processing separated from UI rendering
- [ ] Configuration extracted from logic
- [ ] Code follows existing style patterns
- [ ] No performance regression

## 🎯 CONTEXT
This addresses report.md issue: "Functions exceed 100 lines (e.g., render_clients_page) leading to high cyclomatic complexity" in the Code Quality Report section.

The goal is to improve maintainability while preserving all existing functionality.