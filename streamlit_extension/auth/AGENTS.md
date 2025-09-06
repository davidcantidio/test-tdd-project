# 🔐 CLAUDE.md - Authentication System

**Module:** auth/  
**Purpose:** Complete user management with session handling + TDD session context  
**TDD Mission:** Secure authentication for TDD workflows and TDAH focus sessions  
**Architecture:** OAuth2, session state, middleware decorators  
**Last Updated:** 2025-08-19

---

## 🎯 **TDD + TDAH INTEGRATION**

### **TDD Session Security**
- **Focus Session Auth**: Secure authentication for uninterrupted focus sessions
- **TDD Phase Tracking**: Authentication context for Red-Green-Refactor cycles
- **TDAH Session Support**: Persistent session during interruption handling
- **Progress Preservation**: Session continuity for long TDD cycles

### **Authentication Patterns for TDD**
```python
# TDD-aware authentication
@require_auth
@preserve_tdd_context
def tdd_protected_operation():
    session = SessionHandler()
    tdd_context = session.get_tdd_context()
    
    # Preserve current TDD phase
    current_phase = tdd_context.get('current_phase', 'Red')
    task_id = tdd_context.get('active_task_id')
    
    # Continue TDD workflow with preserved context
    return execute_tdd_operation(task_id, current_phase)

# Session context preservation
class TDDSessionHandler(SessionHandler):
    def preserve_tdd_state(self, task_id: int, phase: str):
        st.session_state['tdd_context'] = {
            'active_task_id': task_id,
            'current_phase': phase,
            'phase_start_time': datetime.now(),
            'focus_session_id': self.get_current_focus_session()
        }
    
    def restore_tdd_context(self) -> dict:
        return st.session_state.get('tdd_context', {})
```

---

## 🧠 **TDAH-OPTIMIZED AUTHENTICATION**

### **Focus-Friendly Login**
- **Quick OAuth**: Minimal friction Google OAuth2
- **Session Persistence**: Extended session for deep focus (2-4 hours)
- **Interruption Recovery**: Auto-resume after distractions
- **Energy-Aware**: Authentication timing based on energy levels

### **TDAH Session Patterns**
```python
# TDAH-optimized session management
class TDAHSessionHandler(SessionHandler):
    def __init__(self):
        super().__init__()
        self.session_duration = self._calculate_tdah_session_duration()
        self.interruption_tolerance = 'high'  # Allow frequent interruptions
    
    def _calculate_tdah_session_duration(self) -> int:
        # Longer sessions for TDAH users to accommodate hyperfocus
        user_profile = self.get_user_profile()
        
        if user_profile.has_hyperfocus_tendencies:
            return 4 * 3600  # 4 hours
        elif user_profile.attention_span == 'short':
            return 2 * 3600  # 2 hours with frequent re-auth prompts
        
        return 3 * 3600  # 3 hours default
    
    def handle_interruption(self):
        # Preserve complete TDD state during interruptions
        tdd_state = self.get_tdd_context()
        focus_session = self.get_current_focus_session()
        
        # Store interruption-safe state
        self.store_interruption_state({
            'tdd_context': tdd_state,
            'focus_session': focus_session,
            'interruption_time': datetime.now(),
            'return_guidance': self.generate_return_guidance()
        })
    
    def resume_focus_session(self):
        # Resume with full context restoration
        interruption_state = self.get_interruption_state()
        
        if interruption_state:
            # Restore TDD context
            self.restore_tdd_context(interruption_state['tdd_context'])
            
            # Provide gentle transition back
            self.show_gentle_return_message(interruption_state)
            
            # Resume focus session
            self.resume_timer_session(interruption_state['focus_session'])
```

### **Energy-Aware Authentication**
```python
# Authentication timing based on TDAH energy patterns
class EnergyAwareAuth:
    def suggest_login_timing(self, user_id: int) -> dict:
        energy_pattern = self.get_user_energy_pattern(user_id)
        current_hour = datetime.now().hour
        
        if current_hour in energy_pattern.peak_hours:
            return {
                'recommendation': 'optimal_time',
                'message': '🚀 Perfect time for focused work!',
                'session_type': 'extended_focus'
            }
        elif current_hour in energy_pattern.low_energy_hours:
            return {
                'recommendation': 'light_tasks',
                'message': '🧘 Good time for light tasks or breaks',
                'session_type': 'maintenance_mode'
            }
        
        return {
            'recommendation': 'standard',
            'message': '⚡ Ready for productive work',
            'session_type': 'standard_focus'
        }
```

---

## 🔧 **Authentication Patterns**

### **Core Components**
- **AuthManager**: Central authentication coordination with TDD context
- **SessionHandler**: Session state management and TDD persistence
- **LoginPage**: Authentication UI with TDAH-friendly design
- **UserModel**: User data model with TDAH profile validation
- **AuthMiddleware**: Decorator-based page protection with TDD preservation

### **Authentication Flow for TDD**
```python
# TDD-integrated authentication pattern
from streamlit_extension.auth import require_auth, get_current_user, preserve_tdd_context

@require_auth
@preserve_tdd_context
def tdd_protected_function():
    user = get_current_user()
    tdd_context = get_tdd_context()
    
    # Continue TDD workflow seamlessly
    if tdd_context.get('active_task_id'):
        return resume_tdd_task(tdd_context['active_task_id'])
    else:
        return suggest_optimal_task(user.id)

# TDD-aware session management
def initialize_tdd_session(user_id: int):
    session = SessionHandler()
    
    # Initialize with TDD-specific context
    session.initialize_user_session({
        'user_id': user_id,
        'tdd_context': {},
        'focus_preferences': get_user_focus_preferences(user_id),
        'tdah_profile': get_tdah_profile(user_id)
    })
    
    return session
```

### **Session Management for TDD**
```python
# Enhanced session patterns for TDD + TDAH
import streamlit as st
from streamlit_extension.auth import SessionHandler

class TDDSessionHandler(SessionHandler):
    def initialize_tdd_session(self, user_data: dict):
        # Standard session initialization
        super().initialize_user_session(user_data)
        
        # TDD-specific session state
        if 'tdd_context' not in st.session_state:
            st.session_state.tdd_context = {
                'current_epic_id': None,
                'current_task_id': None,
                'current_phase': 'Red',  # Default to Red phase
                'phase_start_time': None,
                'cycle_count': 0,
                'daily_goal': self.get_daily_tdd_goal(user_data['user_id'])
            }
        
        # TDAH-specific session state
        if 'tdah_context' not in st.session_state:
            st.session_state.tdah_context = {
                'current_energy_level': 5,  # 1-10 scale
                'current_focus_capacity': 5,  # 1-10 scale
                'interruption_count': 0,
                'last_break_time': None,
                'optimal_work_hours': self.get_optimal_hours(user_data['user_id'])
            }
    
    def preserve_across_navigation(self):
        # Preserve TDD and TDAH context across page navigation
        preserved_state = {
            'tdd_context': st.session_state.get('tdd_context', {}),
            'tdah_context': st.session_state.get('tdah_context', {}),
            'current_focus_session': st.session_state.get('current_focus_session'),
            'timer_state': st.session_state.get('timer_state', {})
        }
        
        return preserved_state
```

---

## 🛡️ **Security Guidelines**

### **Session Security for TDD**
- **Never store TDD sensitive data** in session state (test results, code snippets)
- **Always validate TDD context** before phase transitions
- **Use structured logging** for TDD and auth events
- **Implement proper logout cleanup** including TDD state
- **Session timeout** handling with TDD state preservation

### **OAuth2 Integration for TDAH**
- **Google OAuth2** with minimal interruption flow
- **Fallback local auth** for development and offline focus sessions
- **Secure token handling** with extended expiration for hyperfocus
- **Proper scope management** (email, profile) with privacy respect

### **Authentication Middleware for TDD**
```python
# TDD-aware authentication decorator
def require_auth_with_tdd_context(func):
    def wrapper(*args, **kwargs):
        # Standard authentication check
        if not is_authenticated():
            # Preserve TDD context for post-login restoration
            preserve_tdd_context_for_login()
            redirect_to_login()
            return
        
        # Restore TDD context after authentication
        restore_tdd_context_after_login()
        
        return func(*args, **kwargs)
    return wrapper

# TDAH-friendly authentication flow
def tdah_friendly_login():
    # Minimal cognitive load login
    st.markdown("### 🔐 Quick Login")
    
    # Single click Google OAuth
    if st.button("🚀 Continue with Google", use_container_width=True, type="primary"):
        initiate_google_oauth()
    
    # Alternative for offline work
    with st.expander("🔧 Offline Mode"):
        st.info("For focused offline work sessions")
        if st.button("Start Offline Session"):
            start_offline_session()
```

---

## 📊 **Common Anti-Patterns to Avoid**

### **🔴 Session State Violations**
- **Direct manipulation**: `st.session_state.user = data` (use SessionHandler)
- **Missing TDD preservation**: Not preserving TDD context during auth
- **TDAH context loss**: Losing focus session state during login
- **Inconsistent state**: Multiple session state patterns
- **Interruption data loss**: Not handling TDAH interruption gracefully

### **🔴 Authentication Bypasses**
- **Missing TDD decorators**: Unprotected TDD-sensitive functions
- **Hardcoded bypass**: Development shortcuts in production
- **Token leakage**: Logging tokens or credentials
- **Insecure logout**: Not clearing TDD and TDAH session data
- **Focus session exposure**: Exposing sensitive focus session data

### **🔴 OAuth2 Misuse for TDAH**
- **Hardcoded credentials**: Use environment variables
- **Missing state validation**: CSRF protection in OAuth flow
- **Scope creep**: Requesting unnecessary permissions
- **Token mishandling**: Improper token storage/validation
- **Interruption blindness**: Not handling OAuth during focus sessions

### **🔴 TDAH-Specific Anti-Patterns**
```python
# ❌ TDAH-hostile authentication patterns
def bad_tdah_auth():
    # Complex multi-step authentication
    username = st.text_input("Username")
    password = st.text_input("Password")
    captcha = st.text_input("Captcha")
    two_factor = st.text_input("2FA Code")
    security_question = st.text_input("Security Question")
    # Too many steps - cognitive overload!
    
    # No focus session preservation
    if authenticate(username, password):
        # Lost all focus session context!
        st.session_state.clear()  # DISASTER for TDAH users
    
    # No interruption tolerance
    if session_timeout():
        force_logout()  # No grace period for TDAH interruptions

# ✅ TDAH-friendly authentication
def good_tdah_auth():
    # Single-click authentication
    if st.button("🚀 Quick Login", use_container_width=True):
        initiate_oauth()  # Simple, fast
    
    # Preserve all context
    preserve_focus_session_context()
    preserve_tdd_workflow_context()
    
    # Graceful timeout handling
    if approaching_timeout():
        offer_session_extension()  # Give choice to extend
```

---

## 🔧 **File Tracking - Auth Module**

### **Modified Files Checklist**
```
📊 **AUTH MODULE - ARQUIVOS MODIFICADOS:**

**Authentication Core:**
- auth/auth_manager.py:linha_X - [TDD context integration]
- auth/session_handler.py:linha_Y - [TDAH session management]

**Security Components:**
- auth/middleware.py:linha_Z - [TDD-aware decorators]
- auth/login_page.py:seção_W - [TDAH-friendly login UI]

**User Management:**
- auth/user_model.py:linha_V - [TDAH profile integration]

**Status:** Ready for manual review
**Security:** All auth patterns validated
**TDD Integration:** Workflow context preserved
**TDAH Support:** Focus session continuity maintained
**Impact:** [Impact on authentication flow and session management]
```

### **Security Validation Required**
- [ ] No hardcoded credentials
- [ ] Proper TDD session management
- [ ] OAuth2 configuration secure
- [ ] All auth endpoints protected
- [ ] TDAH logout cleanup complete
- [ ] Focus session preservation functional

---

*Authentication module with TDD workflow integration and TDAH accessibility optimization*