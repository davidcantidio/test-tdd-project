# API Migration Mapping - Step 2.2.3

**Generated:** 2025-08-24  
**Based on:** Steps 2.2.1 (Method Mapping) and 2.2.2 (Coverage Testing)  
**Total Methods:** 55 DatabaseManager methods analyzed  
**Purpose:** Provide clear migration paths for each DatabaseManager method

---

## 📊 **Migration Categories Overview**

| Category | Count | Description | Risk Level | Time Estimate |
|----------|-------|-------------|------------|---------------|
| ✅ **Direct Replacements** | 16 | 1:1 API mapping, works immediately | LOW | 5-10 min/file |
| ⚠️ **Parameter Issues** | 3 | Function exists, signature incompatible | LOW-MEDIUM | 10-15 min/method |
| ⚠️ **Service Layer Required** | 15 | Needs service layer implementation | MEDIUM | 30-60 min/method |
| ❌ **Missing/Incompatible** | 21 | No equivalent, needs implementation | HIGH | 60+ min/method |
| **TOTAL** | **55** | Complete DatabaseManager coverage | - | - |

---

## ✅ **Direct Replacements (SAFE) - 16 Methods**

*These methods have direct 1:1 replacements in the modular API and work immediately.*

### Connection Management (4 methods)
| Old API | New API | Status | Notes |
|---------|---------|--------|-------|
| `db.get_connection()` | `get_connection()` | ✅ WORKS | Direct replacement, connection pooling |
| `db.release_connection(conn)` | `release_connection(conn)` | ✅ WORKS | Direct replacement |
| `db.transaction()` | `transaction()` | ✅ WORKS | Context manager, same interface |
| `db.execute_query(sql, params)` | `execute(sql, params)` | ✅ WORKS | Direct replacement |

### Health & Maintenance (5 methods)
| Old API | New API | Status | Notes |
|---------|---------|--------|-------|
| `db.check_database_health()` | `check_health()` | ✅ WORKS | Direct replacement |
| `db.get_query_statistics()` | `get_query_stats()` | ✅ WORKS | Direct replacement |
| `db.optimize_database()` | `optimize()` | ✅ WORKS | Direct replacement |
| `db.create_backup(path)` | `create_backup(path)` | ✅ WORKS | Direct replacement |
| `db.restore_backup(path)` | `restore_backup(path)` | ✅ WORKS | Direct replacement |

### Basic Query Operations (4 methods)
| Old API | New API | Status | Notes |
|---------|---------|--------|-------|
| `db.get_epics()` | `list_epics()` | ✅ WORKS | Direct replacement, 5 epics returned |
| `db.get_all_epics()` | `list_all_epics()` | ✅ WORKS | Direct replacement, 3 epics returned |
| `db.get_all_tasks(epic_id)` | `list_all_tasks(epic_id)` | ✅ WORKS | Direct replacement, 4 tasks returned |
| `db.get_timer_sessions(days)` | `list_timer_sessions(days)` | ✅ WORKS | Direct replacement, 0 sessions |

### Utilities (3 methods)
| Old API | New API | Status | Notes |
|---------|---------|--------|-------|
| `db.set_database_manager()` | `set_dbm()` | ✅ WORKS | Direct replacement |
| `db.create_schema_if_needed()` | `create_schema_if_needed()` | ✅ WORKS | Direct replacement |
| `db.seed_initial_data()` | `seed_initial_data()` | ✅ WORKS | Direct replacement |

---

## ⚠️ **Parameter Issues (SIGNATURE INCOMPATIBLE) - 3 Methods**

*These methods exist but have incompatible signatures or missing required parameters.*

| Old API | New API | Status | Issue | Solution |
|---------|---------|--------|-------|----------|
| `db.get_tasks()` | `list_tasks(epic_id)` | ⚠️ INCOMPATIBLE | Missing required `epic_id` parameter | Add parameter or use `list_all_tasks()` |
| `db.get_user_stats()` | `get_user_stats(user_id)` | ⚠️ INCOMPATIBLE | Missing required `user_id` parameter | Add `user_id=1` default parameter |
| `db.get_achievements()` | `get_achievements(user_id)` | ⚠️ INCOMPATIBLE | Missing required `user_id` parameter | Add `user_id=1` default parameter |

### Migration Pattern for Parameter Issues:
```python
# OLD API (no parameters)
stats = db.get_user_stats()

# NEW API (requires parameter)  
stats = get_user_stats(user_id=1)  # or get current user ID

# MIGRATION WRAPPER (for backward compatibility)
def get_user_stats_compat():
    return get_user_stats(user_id=1)  # default user
```

---

## ⚠️ **Service Layer Required (COMPLEX) - 15 Methods**

*These methods require service layer implementation or are business logic operations.*

### Project Management - Service Layer (6 methods)
| Old API | New Service API | Status | Implementation Required |
|---------|-----------------|--------|------------------------|
| `db.get_projects()` | `get_project_service().get_all_projects()` | ⚠️ SERVICE | ProjectService operational |
| `db.get_all_projects()` | `get_project_service().get_all()` | ⚠️ SERVICE | ProjectService operational |
| `db.create_project()` | `get_project_service().create_project()` | ⚠️ SERVICE | ProjectService operational |
| `db.update_project()` | `get_project_service().update_project()` | ⚠️ SERVICE | ProjectService operational |
| `db.delete_project()` | `get_project_service().delete_project()` | ⚠️ SERVICE | ProjectService operational |
| `db.get_project_by_key()` | `get_project_service().get_by_key()` | ⚠️ SERVICE | ProjectService operational |

### Task Management - Service Layer (4 methods)
| Old API | New Service API | Status | Implementation Required |
|---------|-----------------|--------|------------------------|
| `db.create_task()` | `get_task_service().create_task()` | ⚠️ SERVICE | TaskService operational |
| `db.update_task()` | `get_task_service().update_task()` | ⚠️ SERVICE | TaskService operational |
| `db.update_task_status()` | `get_task_service().update_status()` | ⚠️ SERVICE | TaskService operational |
| `db.delete_task()` | `get_task_service().delete_task()` | ⚠️ SERVICE | TaskService operational |

### Epic Operations - Service Layer (3 methods)
| Old API | New Service API | Status | Implementation Required |
|---------|-----------------|--------|------------------------|
| `db.get_epic_progress()` | `get_epic_service().calculate_progress()` | ⚠️ SERVICE | EpicService operational |
| `db.calculate_epic_duration()` | `get_epic_service().calculate_duration()` | ⚠️ SERVICE | EpicService operational |
| `db.update_epic_project()` | `get_epic_service().update_project_assignment()` | ⚠️ SERVICE | EpicService operational |

### Timer Operations - Service Layer (1 method)
| Old API | New Service API | Status | Implementation Required |
|---------|-----------------|--------|------------------------|
| `db.create_timer_session()` | `get_timer_service().create_session()` | ⚠️ SERVICE | TimerService operational |

### Connection Utilities (1 method)
| Old API | New API | Status | Implementation Required |
|---------|---------|--------|------------------------|
| `db.close()` | `get_connection().close()` | ⚠️ MANUAL | Manual connection management |

**Service Layer Issue Identified:** ServiceContainer requires configuration fix (`db_manager é obrigatório quando use_modular_api=False`)

---

## ❌ **Missing/Incompatible (HYBRID REQUIRED) - 21 Methods** 

*These methods have no equivalent in modular API or are incompatible. Require implementation or hybrid approach.*

### Epic Hierarchy Operations (3 methods - HIGH PRIORITY)
| Old API | Equivalent | Status | Notes |
|---------|------------|--------|-------|
| `db.get_epics_with_hierarchy()` | No equivalent | ❌ MISSING | Critical for project organization |
| `db.get_all_epics_with_hierarchy()` | No equivalent | ❌ MISSING | Critical for project organization |
| `db.get_hierarchy_overview()` | No equivalent | ❌ MISSING | Dashboard functionality |

### Kanban Functionality (1 method - HIGH PRIORITY)
| Old API | Equivalent | Status | Notes |
|---------|------------|--------|-------|
| `db.get_kanban_tasks()` | No equivalent | ❌ MISSING | Core UI functionality |

### Advanced Analytics (5 methods - MEDIUM PRIORITY)
| Old API | Equivalent | Status | Notes |
|---------|------------|--------|-------|
| `db.get_productivity_stats()` | No equivalent | ❌ MISSING | Analytics dashboard |
| `db.get_daily_summary()` | No equivalent | ❌ MISSING | Analytics dashboard |
| `db.get_pending_notifications()` | No equivalent | ❌ MISSING | User notifications |
| `db.get_user_achievements()` | No equivalent | ❌ MISSING | Gamification system |
| `db.get_project_dashboard()` | No equivalent | ❌ MISSING | Project overview |

### Advanced Pagination (3 methods - LOW PRIORITY)
| Old API | Equivalent | Status | Notes |
|---------|------------|--------|-------|
| `db.get_paginated_results()` | No equivalent | ❌ MISSING | Performance optimization |
| `db.get_cursor_paginated_results()` | No equivalent | ❌ MISSING | Performance optimization |
| `db.get_keyset_paginated_results()` | No equivalent | ❌ MISSING | Performance optimization |

### Cache Management (2 methods - LOW PRIORITY)
| Old API | Equivalent | Status | Notes |
|---------|------------|--------|-------|
| `db.clear_cache()` | No equivalent | ❌ MISSING | Performance management |
| `db.get_cache_stats()` | No equivalent | ❌ MISSING | Performance monitoring |

### Specialized Operations (3 methods - LOW PRIORITY)  
| Old API | Equivalent | Status | Notes |
|---------|------------|--------|-------|
| `db.get_epic_timeline()` | No equivalent | ❌ MISSING | Timeline visualization |
| `db.validate_date_consistency()` | No equivalent | ❌ MISSING | Data validation |
| `db.get_task_statistics()` | No equivalent | ❌ MISSING | Task analytics |

### Formatting & Utilities (3 methods - LOW PRIORITY)
| Old API | Equivalent | Status | Notes |
|---------|------------|--------|-------|
| `db.format_database_datetime()` | No equivalent | ❌ MISSING | Data formatting |
| `db.get_formatted_epic_data()` | No equivalent | ❌ MISSING | UI formatting |
| `db.get_formatted_timer_sessions()` | No equivalent | ❌ MISSING | UI formatting |

### Delete Operations (1 method - MEDIUM PRIORITY)
| Old API | Equivalent | Status | Notes |
|---------|------------|--------|-------|
| `db.delete_cascade_safe()` | No equivalent | ❌ MISSING | Safe deletion with relationships |

---

## 🏗️ **Migration Code Examples**

### ✅ Direct Replacement Pattern
```python
# OLD API
from streamlit_extension.utils.database import DatabaseManager
db_manager = DatabaseManager()
epics = db_manager.get_epics()
conn = db_manager.get_connection()
health = db_manager.check_database_health()

# NEW API - Direct replacement
from streamlit_extension.database import list_epics, get_connection, check_health
epics = list_epics()
conn = get_connection()
health = check_health()
```

### ⚠️ Service Layer Pattern
```python
# OLD API
from streamlit_extension.utils.database import DatabaseManager
db_manager = DatabaseManager()
project = db_manager.create_project(name="Test", description="Test project")
task = db_manager.create_task(title="Task", epic_id=1, description="Test task")

# NEW API - Service layer required
from streamlit_extension.services import get_project_service, get_task_service

# Create project via service
project_service = get_project_service()
result = project_service.create_project({
    'name': 'Test', 
    'description': 'Test project'
})
if result.is_success():
    project = result.get_value()

# Create task via service  
task_service = get_task_service()
result = task_service.create_task({
    'title': 'Task',
    'epic_id': 1,
    'description': 'Test task'
})
if result.is_success():
    task = result.get_value()
```

### ⚠️ Parameter Fix Pattern
```python
# OLD API
from streamlit_extension.utils.database import DatabaseManager
db_manager = DatabaseManager()
tasks = db_manager.get_tasks()  # No parameters required
stats = db_manager.get_user_stats()  # No parameters required

# NEW API - Parameters required
from streamlit_extension.database import list_tasks, get_user_stats

# Fix 1: Add required parameters
tasks = list_tasks(epic_id=1)  # Must specify epic
stats = get_user_stats(user_id=1)  # Must specify user

# Fix 2: Create compatibility wrapper
def get_tasks_compat(epic_id=None):
    if epic_id:
        return list_tasks(epic_id)
    else:
        return list_all_tasks()  # Get all tasks instead

def get_user_stats_compat(user_id=None):
    if user_id is None:
        user_id = 1  # Default user
    return get_user_stats(user_id)
```

### ❌ Hybrid Pattern (Keep Legacy)
```python
# HYBRID APPROACH - Use both APIs
from streamlit_extension.utils.database import DatabaseManager  # Legacy for missing methods
from streamlit_extension.database import list_epics, get_connection  # Modular for available methods

# Use modular for available operations
epics = list_epics()
conn = get_connection()

# Use legacy for missing operations
db_manager = DatabaseManager()
kanban_data = db_manager.get_kanban_tasks()  # Not available in modular
hierarchy = db_manager.get_epics_with_hierarchy()  # Not available in modular
```

---

## 📋 **File Migration Batching Strategy**

### **Batch 1: Simple Replacements (GREEN METHODS ONLY) - 8 files estimated**
**Risk Level:** LOW | **Time:** 30-60 minutes | **Success Rate:** 95%+

Files using ONLY green methods from the mapping above:
- Health check utilities
- Basic connection management
- Simple query operations

**Migration Steps:**
1. Replace imports: `DatabaseManager` → specific functions
2. Replace method calls: `db.method()` → `method()`
3. Test imports and basic functionality

### **Batch 2: Parameter Fixes + Service Layer (YELLOW METHODS) - 15 files estimated**
**Risk Level:** MEDIUM | **Time:** 2-3 hours | **Success Rate:** 80%+

Files using parameter-incompatible methods or requiring service layer:
- Project management operations
- Task CRUD operations  
- User statistics and achievements
- Complex business logic

**Migration Steps:**
1. Fix service layer configuration issues
2. Replace parameter-incompatible calls
3. Implement service layer patterns
4. Test business logic operations

### **Batch 3: Hybrid/Complex Operations (RED METHODS) - 13 files estimated**
**Risk Level:** HIGH | **Time:** 4+ hours | **Success Rate:** 60%+

Files using missing methods or complex operations:
- Kanban functionality
- Epic hierarchy operations
- Advanced analytics
- Specialized formatting

**Migration Approach:**
1. **Option A:** Keep hybrid approach (recommended)
2. **Option B:** Implement missing methods in modular API
3. **Option C:** Replace functionality with service layer equivalents

---

## 🎯 **Migration Decision Framework**

### **Recommended Approach: SELECTIVE MIGRATION**
Based on the analysis:

1. **✅ MIGRATE (Green + Yellow):** 34 methods (62% of functionality)
   - **Time Investment:** 3-4 hours
   - **Risk Level:** Low-Medium  
   - **Business Value:** High (covers core operations)

2. **❌ KEEP HYBRID (Red):** 21 methods (38% of functionality)
   - **Time Investment:** 8+ hours to implement
   - **Risk Level:** High
   - **Business Value:** Medium (specialized features)

### **Migration Priority Matrix**

| Priority | Methods | Reason | Action |
|----------|---------|---------|--------|
| **CRITICAL** | 19 Green methods | Working, direct replacement | ✅ Migrate immediately |
| **HIGH** | 3 Yellow parameter methods | Easy fixes, 15 min each | ⚠️ Fix parameters |
| **MEDIUM** | 15 Yellow service methods | Service layer needed | ⚠️ Fix service layer first |
| **LOW** | 18 Red specialized methods | Complex implementation | ❌ Keep hybrid |
| **OPTIONAL** | 3 Red missing high-priority | Kanban, hierarchy | ❌ Implement only if critical |

### **Business Decision Points**

#### **Continue Hybrid (Recommended)**
- **Pros:** Minimal risk, immediate functionality, proven stability
- **Cons:** Technical debt, dual maintenance
- **Time:** 0 additional hours
- **When to choose:** Production system, tight timelines, risk-averse

#### **Partial Migration (34 methods)**  
- **Pros:** Modern architecture for core features, reduced complexity
- **Cons:** Still hybrid, service layer configuration needed
- **Time:** 3-4 hours
- **When to choose:** Development system, moderate risk tolerance

#### **Full Migration (55 methods)**
- **Pros:** Pure modular architecture, single API
- **Cons:** High risk, significant time investment, potential instability  
- **Time:** 8-12 hours
- **When to choose:** Greenfield projects, high risk tolerance, long-term investment

---

## 🚨 **Critical Blockers Identified**

### **Service Layer Configuration Issue**
```
ERROR: ServiceContainer initialization failed: 
db_manager é obrigatório quando use_modular_api=False
```

**Impact:** All 15 service layer methods unavailable  
**Priority:** HIGH - Must fix before any service layer migration  
**Solution Required:** Configure ServiceContainer properly or fix `use_modular_api` parameter

### **Missing Core Business Functions**
- **Kanban functionality** (1 method) - Core UI feature
- **Epic hierarchy** (3 methods) - Project organization
- **Project dashboard** (1 method) - Analytics overview

**Impact:** Major functional gaps in modular API  
**Priority:** MEDIUM - Consider business impact  
**Solution Options:** Implement in modular API or maintain hybrid

---

## ✅ **Step 2.2.3 Completion Summary**

**✅ API Mapping Complete:**
- All 55 DatabaseManager methods analyzed and categorized
- Migration complexity determined for each method
- Code examples provided for all migration patterns
- File batching strategy created based on method usage
- Clear decision framework established for migration approach

**📊 Key Statistics:**
- **16 methods (29%):** Direct replacements available ✅  
- **3 methods (5%):** Parameter compatibility issues ⚠️
- **15 methods (27%):** Service layer required ⚠️
- **21 methods (38%):** Missing or incompatible ❌
- **Success Rate:** 62% of functionality can be migrated with low-medium effort

**🎯 Recommendation:** 
**SELECTIVE MIGRATION** - Migrate green and fixable yellow methods (34 total), keep hybrid approach for red methods. This provides 62% modernization with minimal risk and achievable time investment.

**Next Step:** If migration proceeds, address service layer configuration issues before starting Batch 2 migrations.

---

*Generated: 2025-08-24 | Based on comprehensive analysis of DatabaseManager methods*