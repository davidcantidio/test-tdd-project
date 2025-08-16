# 📝 PROMPT_CODEX_6: HARDCODED STRINGS CENTRALIZATION

## 🎯 **TASK SPECIFICATION**
**TASK**: Centralize ALL hardcoded strings into comprehensive enums and constants
**TARGET**: Status values, tier names, error messages scattered across pages/*py files
**PRIORITY**: HIGH (Report.md Item 41)
**EFFORT**: MEDIUM (2-3 horas)
**CONFIDENCE**: HIGH (90% - Pattern matching and replacement)

---

## 📋 **DETAILED REQUIREMENTS**

### **SCOPE: Multiple Files (No Conflicts)**
- `streamlit_extension/pages/clients.py`
- `streamlit_extension/pages/projects.py` 
- `streamlit_extension/pages/epics.py`
- `streamlit_extension/pages/kanban.py`
- `streamlit_extension/pages/timer.py`
- `streamlit_extension/config/constants.py` (EXTEND existing)

### **HARDCODED STRINGS TO CENTRALIZE:**

#### **1. STATUS VALUES (35+ instances)**
```python
# FOUND IN: clients.py, projects.py, epics.py
"active", "inactive", "pending", "completed"
"planning", "in_progress", "on_hold", "cancelled"
"red", "green", "refactor", "blocked"
"draft", "review", "approved", "rejected"
```

#### **2. CLIENT TIER VALUES (15+ instances)**
```python
# FOUND IN: clients.py
"standard", "premium", "enterprise", "free_trial"
"startup", "small_business", "mid_market", "enterprise"
```

#### **3. COMPANY SIZE VALUES (10+ instances)**
```python
# FOUND IN: clients.py
"startup", "small", "medium", "large", "enterprise"
"1-10", "11-50", "51-200", "201-1000", "1000+"
```

#### **4. ERROR MESSAGES (50+ instances)**
```python
# FOUND IN: Multiple files
"❌ Error loading clients: {e}"
"❌ Error creating client: {e}"
"❌ Error updating client: {e}"
"❌ Error deleting client: {e}"
"⚠️ No clients match your current filters."
"🔍 No clients found"
"✅ Client created successfully!"
"✅ Client updated successfully!"
```

#### **5. UI CONSTANTS (25+ instances)**
```python
# FOUND IN: Multiple files
"🟢", "🟡", "🔴", "⚪", "✅", "⏸️", "📋", "📝"
"📊 Total:", "📄 Página", "📭 Nenhum", "🔍 Buscar"
"Todos", "Selecionar...", "Filtrar por"
```

---

## 🎯 **IMPLEMENTATION STRATEGY**

### **STEP 1: Extend constants.py**
```python
# ADD TO: streamlit_extension/config/constants.py

class StatusValues(Enum):
    """Centralized status values for all entities"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"

class TDDPhases(Enum):
    """TDD cycle phases"""
    RED = "red"
    GREEN = "green" 
    REFACTOR = "refactor"
    BLOCKED = "blocked"

class ClientTiers(Enum):
    """Client tier classifications"""
    FREE_TRIAL = "free_trial"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class CompanySizes(Enum):
    """Company size categories"""
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"
    SIZE_1_10 = "1-10"
    SIZE_11_50 = "11-50"
    SIZE_51_200 = "51-200"
    SIZE_201_1000 = "201-1000"
    SIZE_1000_PLUS = "1000+"

class ErrorMessages:
    """Centralized error message templates"""
    # Client errors
    CLIENT_LOAD_ERROR = "❌ Error loading clients: {error}"
    CLIENT_CREATE_ERROR = "❌ Error creating client: {error}"
    CLIENT_UPDATE_ERROR = "❌ Error updating client: {error}"
    CLIENT_DELETE_ERROR = "❌ Error deleting client: {error}"
    CLIENT_NOT_FOUND = "❌ Client not found"
    CLIENT_CREATE_SUCCESS = "✅ Client created successfully!"
    CLIENT_UPDATE_SUCCESS = "✅ Client updated successfully!"
    CLIENT_DELETE_SUCCESS = "✅ Client deleted successfully!"
    
    # Project errors  
    PROJECT_LOAD_ERROR = "❌ Error loading projects: {error}"
    PROJECT_CREATE_ERROR = "❌ Error creating project: {error}"
    PROJECT_UPDATE_ERROR = "❌ Error updating project: {error}"
    PROJECT_DELETE_ERROR = "❌ Error deleting project: {error}"
    
    # Generic errors
    NO_MATCHES_FILTER = "⚠️ No {entity} match your current filters."
    NO_ITEMS_FOUND = "🔍 No {entity} found"
    LOADING_ERROR = "❌ Error loading {entity}: {error}"

class UIConstants:
    """UI elements and icons"""
    # Status icons
    ICON_ACTIVE = "🟢"
    ICON_INACTIVE = "🔴"
    ICON_PENDING = "🟡"
    ICON_COMPLETED = "✅"
    ICON_PLANNING = "🟡"
    ICON_IN_PROGRESS = "🟢"
    ICON_ON_HOLD = "⏸️"
    ICON_CANCELLED = "🔴"
    ICON_UNKNOWN = "⚪"
    
    # Generic icons
    ICON_EPIC = "📋"
    ICON_TASK = "📝"
    ICON_SEARCH = "🔍"
    ICON_TOTAL = "📊"
    ICON_PAGE = "📄"
    ICON_EMPTY = "📭"
    
    # Common text
    TEXT_ALL = "Todos"
    TEXT_SELECT = "Selecionar..."
    TEXT_FILTER_BY = "Filtrar por"
    TEXT_SEARCH = "Buscar"
    TEXT_TOTAL = "📊 Total:"
    TEXT_PAGE = "📄 Página"
    TEXT_EMPTY = "📭 Nenhum"
    TEXT_NO_ITEMS = "{icon} Nenhum {entity} encontrado"
```

### **STEP 2: Update All Page Files**

#### **clients.py replacements:**
```python
# BEFORE:
status_colors = {
    "active": "🟢",
    "inactive": "🔴", 
    "pending": "🟡"
}

# AFTER:
from streamlit_extension.config.constants import StatusValues, UIConstants
status_colors = {
    StatusValues.ACTIVE.value: UIConstants.ICON_ACTIVE,
    StatusValues.INACTIVE.value: UIConstants.ICON_INACTIVE,
    StatusValues.PENDING.value: UIConstants.ICON_PENDING
}

# BEFORE:
st.error(f"❌ Error loading clients: {e}")

# AFTER:
st.error(ErrorMessages.CLIENT_LOAD_ERROR.format(error=e))
```

#### **projects.py replacements:**
```python
# BEFORE:
status_colors = {
    "planning": "🟡",
    "in_progress": "🟢", 
    "completed": "✅",
    "on_hold": "⏸️",
    "cancelled": "🔴"
}

# AFTER:
status_colors = {
    StatusValues.PLANNING.value: UIConstants.ICON_PLANNING,
    StatusValues.IN_PROGRESS.value: UIConstants.ICON_IN_PROGRESS,
    StatusValues.COMPLETED.value: UIConstants.ICON_COMPLETED,
    StatusValues.ON_HOLD.value: UIConstants.ICON_ON_HOLD,
    StatusValues.CANCELLED.value: UIConstants.ICON_CANCELLED
}
```

---

## 🔍 **VERIFICATION CRITERIA**

### **SUCCESS REQUIREMENTS:**
1. ✅ **Zero hardcoded status strings** in page files
2. ✅ **Zero hardcoded error messages** using f-strings
3. ✅ **Zero hardcoded UI icons** scattered across files
4. ✅ **Complete enum coverage** for all status/tier values
5. ✅ **Consistent imports** across all page files
6. ✅ **Template-based error messages** with .format()
7. ✅ **All tests still pass** after replacements

### **PATTERN VERIFICATION:**
```bash
# Check for remaining hardcoded strings
grep -r "active\|inactive\|pending" streamlit_extension/pages/ | grep -v "import\|Enum"
grep -r "❌ Error\|✅.*success" streamlit_extension/pages/ | grep -v "ErrorMessages"
grep -r "🟢\|🔴\|🟡\|✅" streamlit_extension/pages/ | grep -v "UIConstants"
```

---

## 📊 **DETAILED REPLACEMENTS**

### **File: clients.py (15 replacements)**
```python
# Status mappings (5 replacements)
"active" → StatusValues.ACTIVE.value
"inactive" → StatusValues.INACTIVE.value  
"pending" → StatusValues.PENDING.value

# Error messages (7 replacements)
f"❌ Error loading clients: {e}" → ErrorMessages.CLIENT_LOAD_ERROR.format(error=e)
f"❌ Error creating client: {e}" → ErrorMessages.CLIENT_CREATE_ERROR.format(error=e)
"✅ Client created successfully!" → ErrorMessages.CLIENT_CREATE_SUCCESS

# UI icons (3 replacements)
"🟢" → UIConstants.ICON_ACTIVE
"🔴" → UIConstants.ICON_INACTIVE
"📋" → UIConstants.ICON_EPIC
```

### **File: projects.py (12 replacements)**
```python
# Status mappings (8 replacements)
"planning" → StatusValues.PLANNING.value
"in_progress" → StatusValues.IN_PROGRESS.value
"completed" → StatusValues.COMPLETED.value
"on_hold" → StatusValues.ON_HOLD.value
"cancelled" → StatusValues.CANCELLED.value

# Error messages (4 replacements)
f"❌ Error loading projects: {e}" → ErrorMessages.PROJECT_LOAD_ERROR.format(error=e)
"⚠️ No projects match your current filters." → ErrorMessages.NO_MATCHES_FILTER.format(entity="projects")
```

---

## ⚠️ **CRITICAL REQUIREMENTS**

1. **PRESERVE FUNCTIONALITY** - All status checks must work identically
2. **MAINTAIN IMPORTS** - Add proper imports to each file
3. **ERROR MESSAGE FORMATTING** - Use .format() not f-strings for templates
4. **ENUM VALUE ACCESS** - Always use .value for string comparisons
5. **TEST COMPATIBILITY** - Verify all tests pass after changes

---

## 📈 **SUCCESS METRICS**

- ✅ **0 hardcoded status strings** in page files
- ✅ **60+ string literals** moved to constants
- ✅ **5 comprehensive enums** created
- ✅ **Consistent error handling** across all pages
- ✅ **Enhanced maintainability** - Single point of truth
- ✅ **Report.md Item 41** - RESOLVED

**PRIORITY**: Execute in parallel with other Codex tasks
**DEPENDENCIES**: None (isolated file modifications)
**RISK**: Low (pure refactoring, no logic changes)