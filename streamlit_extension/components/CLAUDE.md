# 🧩 CLAUDE.md - UI Components

**Module:** components/  
**Purpose:** Reusable UI components and form patterns + TDAH UI optimization  
**TDD Mission:** UI components that facilitate Red-Green-Refactor cycles  
**Architecture:** DRY components, validation-first design, TDAH accessibility  
**Last Updated:** 2025-08-19

---

## 🎯 **TDD + TDAH INTEGRATION**

### **TDD Workflow Components**
- **TDDPhaseIndicator**: Visual indicator of current Red/Green/Refactor phase
- **TestProgressWidget**: Real-time test execution progress
- **CycleCompletionCard**: TDD cycle completion celebration
- **PhaseTransitionButton**: Smart buttons for phase transitions

### **TDAH-Optimized UI Patterns**
- **FocusPreservingForms**: Forms that maintain focus context
- **ProgressFeedbackComponents**: Immediate visual feedback for dopamine
- **InterruptionSafeComponents**: Components that handle interruptions gracefully
- **EnergyAwareLayouts**: UI adaptation based on user energy levels

---

## 🔧 **Component Patterns**

### **Core Component Types**
- **StandardForm**: Base form with validation and TDAH-friendly error handling
- **DataProviders**: Component-specific data fetching abstractions
- **LayoutRenderers**: Consistent layout patterns across pages
- **FallbackComponents**: Error-safe UI fallbacks and graceful degradation
- **DebugWidgets**: Development-time debugging components
- **HealthWidgets**: System health display components

### **TDD-Aware Form Component Hierarchy**
```python
# TDD-integrated form pattern
from streamlit_extension.components import StandardForm

class TDDTaskForm(StandardForm):
    def __init__(self, tdd_phase: str = 'Red'):
        super().__init__(validation_rules=TaskValidation())
        self.tdd_phase = tdd_phase
        self.focus_preservation = True
    
    def render(self):
        # TDD phase-specific form rendering
        with st.container():
            # Clear phase indication
            self.render_phase_indicator()
            
            # Phase-specific fields
            if self.tdd_phase == 'Red':
                self.render_test_requirements_section()
            elif self.tdd_phase == 'Green':
                self.render_implementation_section()
            elif self.tdd_phase == 'Refactor':
                self.render_improvement_section()
            
            # TDAH-friendly validation feedback
            self.render_validation_with_positive_feedback()
    
    def render_phase_indicator(self):
        # Visual TDD phase indicator
        phase_colors = {'Red': '🔴', 'Green': '🟢', 'Refactor': '🔵'}
        st.markdown(f"### {phase_colors[self.tdd_phase]} {self.tdd_phase} Phase")
        
        # Progress indicator
        phase_progress = self.calculate_phase_progress()
        st.progress(phase_progress, text=f"{self.tdd_phase} Phase Progress")
```

### **TDAH-Optimized Data Provider Pattern**
```python
# TDAH-friendly data provider abstraction
from streamlit_extension.components import DataProvider

class TDAHEpicDataProvider(DataProvider):
    def __init__(self):
        super().__init__()
        self.chunking_strategy = 'micro_tasks'  # Break into small pieces
        self.feedback_frequency = 'immediate'   # Instant feedback
    
    def get_epic_data(self, epic_id: int):
        # Chunked data loading to prevent overwhelm
        epic_data = self.load_epic_base_data(epic_id)
        
        # Progressive disclosure based on focus capacity
        focus_level = self.get_current_focus_level()
        
        if focus_level <= 3:  # Low focus - minimal info
            return self.get_essential_epic_data(epic_data)
        elif focus_level <= 6:  # Medium focus - standard info
            return self.get_standard_epic_data(epic_data)
        else:  # High focus - full detail
            return self.get_detailed_epic_data(epic_data)
    
    def get_essential_epic_data(self, epic_data: dict) -> dict:
        # Minimum viable information for TDAH focus
        return {
            'id': epic_data['id'],
            'title': epic_data['title'],
            'current_task': epic_data.get('current_task'),
            'progress': epic_data.get('progress', 0),
            'next_action': epic_data.get('next_action', 'Start working')
        }
```

---

## 🎯 **Design Principles**

### **Single Responsibility for TDD**
- **One TDD purpose** per component (Red OR Green OR Refactor focus)
- **Clear TDD interfaces** with defined inputs/outputs
- **Minimal TDD dependencies** between components
- **Testable TDD design** with dependency injection

### **Validation-First Design for TDAH**
- **Built-in validation** for all form components with positive feedback
- **Consistent error messaging** with encouraging language
- **Type-safe interfaces** with proper annotations
- **Security validation** integrated by default with minimal friction

### **TDAH-Responsive Design**
```python
# TDAH-adaptive component design
class TDAHResponsiveComponent:
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        self.adapt_to_tdah_needs()
    
    def adapt_to_tdah_needs(self):
        # Adjust component behavior based on TDAH profile
        if self.user_profile.has_attention_challenges:
            self.enable_focus_mode()
            self.increase_feedback_frequency()
            self.simplify_visual_hierarchy()
        
        if self.user_profile.has_hyperfocus_tendencies:
            self.enable_hyperfocus_protection()
            self.add_gentle_transition_warnings()
    
    def enable_focus_mode(self):
        # Reduce visual clutter and distractions
        self.hide_non_essential_elements = True
        self.use_high_contrast_colors = True
        self.enable_single_task_focus = True
    
    def increase_feedback_frequency(self):
        # More frequent positive reinforcement
        self.show_micro_progress_indicators = True
        self.enable_completion_celebrations = True
        self.provide_constant_encouragement = True
```

### **Progressive Disclosure for Focus Management**
```python
# Progressive information disclosure
class ProgressiveDisclosureComponent:
    def render_with_focus_awareness(self, data: dict, focus_level: int):
        # Level 1: Essential only (focus_level 1-3)
        self.render_essential_info(data)
        
        if focus_level >= 4:
            # Level 2: Add context (focus_level 4-6)
            with st.expander("📊 Additional Context", expanded=False):
                self.render_context_info(data)
        
        if focus_level >= 7:
            # Level 3: Full detail (focus_level 7-10)
            with st.expander("🔧 Advanced Options", expanded=False):
                self.render_advanced_options(data)
    
    def render_essential_info(self, data: dict):
        # Core information that's always visible
        st.markdown(f"### {data['title']}")
        
        # Single most important metric
        if 'progress' in data:
            st.metric("Progress", f"{data['progress']:.0%}")
        
        # One clear action
        if 'primary_action' in data:
            st.button(data['primary_action'], use_container_width=True, type="primary")
```

---

## 📊 **Component Categories**

### **TDD Workflow Components**
- **RedPhaseComponents**: Test design and requirement specification
- **GreenPhaseComponents**: Implementation tracking and progress
- **RefactorPhaseComponents**: Code improvement and optimization tools
- **CycleTransitionComponents**: Phase transition management

### **TDAH Support Components**
- **FocusTimerWidget**: Pomodoro timer with TDAH adaptations
- **InterruptionHandler**: Graceful interruption management
- **EnergyTracker**: Energy level monitoring and optimization
- **ProgressCelebration**: Dopamine-optimized success feedback

### **Form Components for TDD**
- **TestSpecificationForm**: Red phase test requirement forms
- **ImplementationForm**: Green phase implementation tracking
- **RefactorPlanForm**: Refactor phase improvement planning
- **TaskTransitionForm**: TDD phase transition management

### **Display Components for TDAH**
- **DashboardWidgets**: Analytics and metrics display with chunking
- **AnalyticsCards**: Performance metric cards with positive framing
- **HealthWidgets**: System health indicators with calming colors
- **StatusComponents**: System status displays with clear hierarchy

### **Layout Components**
- **TDDHeader**: Navigation with TDD phase awareness
- **TDAHSidebar**: Navigation with focus-friendly design
- **PageManager**: Page routing with state preservation
- **LayoutRenderers**: Consistent page layouts with accessibility

### **Specialized Components**
- **TDAHTimer**: TDAH-optimized focus timer with interruption handling
- **DebugWidgets**: Development debugging tools with minimal distraction
- **FallbackComponents**: Error recovery components with encouraging messages

---

## 🚨 **Anti-Patterns to Avoid**

### **🔴 Component Violations**
- **Massive form duplication**: Use StandardForm base instead
- **Direct database calls**: Use DataProviders
- **Missing validation**: All inputs must be validated with positive feedback
- **Hardcoded styling**: Use theme system
- **Business logic in UI**: Move to service layer

### **🔴 TDD Anti-Patterns**
```python
# ❌ TDD-hostile component patterns
def bad_tdd_component():
    # Phase confusion
    if st.button("Red Phase"):
        pass
    if st.button("Green Phase"):
        pass
    if st.button("Refactor Phase"):
        pass
    # No clear indication of current phase!
    
    # Missing TDD context
    task_form()  # No awareness of TDD phase
    
    # No test integration
    if st.button("Save Task"):
        save_task()  # No connection to test status

# ✅ TDD-friendly component
def good_tdd_component():
    # Clear phase indication
    current_phase = get_current_tdd_phase()
    st.markdown(f"### 🔄 Current Phase: {current_phase}")
    
    # Phase-aware actions
    if current_phase == 'Red':
        render_test_design_actions()
    elif current_phase == 'Green':
        render_implementation_actions()
    
    # Test status integration
    test_status = get_current_test_status()
    if test_status == 'failing':
        st.error("Tests failing - ready for Green phase!")
    elif test_status == 'passing':
        st.success("Tests passing - ready for Refactor!")
```

### **🔴 TDAH Anti-Patterns**
```python
# ❌ TDAH-hostile UI patterns
def bad_tdah_component():
    # Information overload
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        show_complex_data()
    with col2:
        show_more_complex_data()
    # Too much information at once!
    
    # No focus preservation
    if form_submitted():
        st.session_state.clear()  # Lost all context!
    
    # Harsh error messaging
    if validation_failed():
        st.error("ERROR: You did everything wrong!")  # Demotivating!
    
    # No interruption tolerance
    if user_distracted():
        force_form_reset()  # Lost all progress!

# ✅ TDAH-friendly component
def good_tdah_component():
    # Single focus point
    with st.container():
        st.markdown("### 🎯 Current Focus")
        show_current_task_only()
    
    # Focus preservation
    if form_submitted():
        preserve_form_context()  # Keep working context
    
    # Encouraging feedback
    if validation_failed():
        st.info("💡 Let's adjust a few things:")  # Positive framing
        show_helpful_suggestions()
    
    # Interruption recovery
    if user_returns_from_interruption():
        offer_context_restoration()  # Help them remember where they were
```

### **🔴 Form Anti-Patterns**
- **Inconsistent validation**: Use centralized validation rules
- **Missing error handling**: All forms need error display with encouragement
- **Direct service calls**: Use proper abstraction layers
- **State management chaos**: Use consistent state patterns
- **Overwhelming forms**: Break into micro-forms for TDAH users

### **🔴 Layout Anti-Patterns**
- **Inconsistent layouts**: Use LayoutRenderers
- **Hardcoded responsive breakpoints**: Use theme constants
- **Missing accessibility**: Include ARIA labels and roles
- **Poor navigation**: Use consistent navigation patterns
- **Cognitive overload**: Too much information without progressive disclosure

---

## 🔧 **File Tracking - Components Module**

### **Modified Files Checklist**
```
📊 **COMPONENTS MODULE - ARQUIVOS MODIFICADOS:**

**TDD Components:**
- components/tdd_phase_indicator.py - [TDD phase visualization]
- components/cycle_completion_card.py - [TDD cycle celebration]

**Form Components:**
- components/form_components.py:linha_X - [TDAH-friendly form validation]
- components/dashboard_widgets.py:linha_Y - [Progressive disclosure widgets]

**Layout Components:**
- components/header.py:linha_Z - [TDD phase aware navigation]
- components/page_manager.py:seção_W - [Focus state preservation]

**TDAH Components:**
- components/focus_timer_widget.py - [TDAH-optimized timer]
- components/interruption_handler.py - [Graceful interruption management]

**Specialized Components:**
- components/timer.py:linha_V - [Timer functionality with TDD integration]
- components/fallback_components.py:linha_U - [Error handling with encouragement]

**Status:** Ready for manual review
**TDD Integration:** All components TDD-phase aware
**TDAH Support:** Focus preservation and accessibility verified
**Validation:** All components tested with positive feedback
**Impact:** [Impact on UI consistency, TDD workflow, and TDAH usability]
```

### **Component Validation Required**
- [ ] All forms use StandardForm base with TDAH adaptations
- [ ] No direct database calls in components
- [ ] Consistent validation patterns with positive messaging
- [ ] TDD phase awareness in all workflow components
- [ ] TDAH accessibility compliance verified
- [ ] Progressive disclosure implemented
- [ ] Interruption handling graceful

---

*UI component system with TDD workflow integration and TDAH accessibility optimization*