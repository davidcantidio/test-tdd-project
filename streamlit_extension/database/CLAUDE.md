# 📊 CLAUDE.md - Database Layer

**Module:** database/  
**Purpose:** Enterprise database layer with hybrid API + TDD data persistence  
**TDD Mission:** Reliable data persistence for Red-Green-Refactor cycles  
**Architecture:** OptimizedConnectionPool + LRU cache + Legacy compatibility  
**Performance:** 4,600x+ improvement with sub-millisecond queries  
**IA Enhancement:** Enhanced framework_epics schema for topological ordering (Phase 5.1)  
**Last Updated:** 2025-09-04 - IA-Driven Epic Generation Schema Extensions

---

## 🎯 **TDD + TDAH INTEGRATION**

### **TDD Data Persistence Patterns**
- **Phase State Management**: Reliable persistence of Red/Green/Refactor states
- **Test Result Storage**: Secure storage of test execution results
- **Cycle Analytics**: Performance data for TDD effectiveness measurement
- **Progress Tracking**: Granular progress data for motivation and analytics

### **TDAH-Optimized Data Operations**
- **Fast Queries**: Sub-millisecond responses for immediate feedback
- **Session Persistence**: Reliable storage of focus session context
- **Interruption Recovery**: Robust data preservation during interruptions
- **Analytics Integration**: Data patterns for TDAH productivity optimization

---

## 🔧 **Database Architecture**

### **Hybrid API Design for TDD**
- **Legacy DatabaseManager**: Monolithic API (42 files dependent) - battle-tested for TDD workflows
- **Modular Database API**: New service-oriented architecture - optimized for microservices
- **Coexistence Strategy**: Both APIs working simultaneously - zero disruption to TDD cycles
- **Migration Path**: Optional, performance-driven migration - maintain TDD workflow continuity

### **Performance Layer for TDAH**
- **OptimizedConnectionPool**: 4,600x+ performance improvement - instant feedback for TDAH users
- **LRU Cache**: 26x speedup for repeated queries - reduced waiting and frustration
- **Connection Management**: Thread-safe pooling with timeout - reliable during hyperfocus sessions
- **Query Optimization**: Sub-millisecond query execution - immediate dopamine feedback

### **Core Components**
- **connection.py**: OptimizedConnectionPool implementation with TDD session awareness
- **health.py**: Real-time database health monitoring with TDAH-friendly status display
- **queries.py**: Optimized query implementations for TDD and analytics workflows
- **schema.py**: Database schema definitions with TDD and TDAH data structures + IA epic generation fields
- **database_singleton.py**: Singleton pattern for connection management with session preservation
- **epic_migrations.py**: IA-enhanced schema migrations for topological ordering

---

## 🛡️ **Security Standards for TDD**

### **SQL Injection Prevention**
```python
# ✅ TDD-SAFE PATTERNS (Parameter binding)
def store_tdd_phase_transition(task_id: int, from_phase: str, to_phase: str):
    cursor.execute("""
        INSERT INTO tdd_phase_transitions (task_id, from_phase, to_phase, timestamp)
        VALUES (?, ?, ?, ?)
    """, (task_id, from_phase, to_phase, datetime.now()))

def get_test_results_for_task(task_id: int):
    cursor.execute("SELECT * FROM test_results WHERE task_id = ?", (task_id,))
    return cursor.fetchall()

# ❌ NEVER USE (SQL injection vulnerability)
def dangerous_tdd_query(task_id: int, phase: str):
    # This would be vulnerable to SQL injection
    # cursor.execute(f"SELECT * FROM tasks WHERE id = {task_id} AND phase = '{phase}'")
    pass
```

### **Transaction Safety for TDD Cycles**
```python
# TDD cycle transaction management
def complete_tdd_cycle_atomically(task_id: int, cycle_data: dict):
    with db_manager.get_connection("framework") as conn:
        try:
            # 1. Update task phase to Complete
            conn.execute("""
                UPDATE framework_tasks 
                SET tdd_phase = 'Complete', completed_at = ?
                WHERE task_id = ?
            """, (datetime.now(), task_id))
            
            # 2. Store cycle metrics
            conn.execute("""
                INSERT INTO tdd_cycle_metrics 
                (task_id, red_duration, green_duration, refactor_duration, total_duration)
                VALUES (?, ?, ?, ?, ?)
            """, (task_id, cycle_data['red_duration'], cycle_data['green_duration'], 
                  cycle_data['refactor_duration'], cycle_data['total_duration']))
            
            # 3. Update epic progress
            conn.execute("""
                UPDATE framework_epics 
                SET completed_tasks = completed_tasks + 1
                WHERE epic_id = (SELECT epic_id FROM framework_tasks WHERE task_id = ?)
            """, (task_id,))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise TDDDatabaseError(f"Failed to complete TDD cycle atomically: {e}")
```

### **Connection Security for TDAH Sessions**
- **Connection timeout**: 30-second default timeout with extension for hyperfocus
- **Pool size limits**: Prevent resource exhaustion during intense work sessions
- **Access control**: Database-level permissions with role-based access
- **Connection encryption**: TLS for production with performance optimization

---

## 📊 **Performance Guidelines for TDAH**

### **Connection Pooling for Focus Sessions**
```python
# TDAH-optimized connection usage
def execute_tdah_friendly_query(query: str, params: tuple = ()):
    # Use connection pool for immediate response
    with db_manager.get_connection("framework") as conn:
        start_time = time.time()
        
        # Execute query
        cursor = conn.execute(query, params)
        result = cursor.fetchall()
        
        # Monitor performance for TDAH feedback
        duration = time.time() - start_time
        if duration > 0.001:  # 1ms threshold for TDAH immediate feedback
            logger.warning(f"Slow query detected for TDAH user: {duration:.3f}s")
            
        return result
```

### **LRU Cache Utilization for Immediate Feedback**
```python
# TDAH-optimized caching for instant gratification
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_epic_progress_cached(epic_id: int) -> float:
    """Cached epic progress for immediate TDAH feedback"""
    progress = calculate_epic_progress(epic_id)
    return progress

@lru_cache(maxsize=500)
def get_user_productivity_metrics(user_id: int, date: str) -> dict:
    """Cached productivity metrics for TDAH analytics"""
    return calculate_daily_productivity(user_id, date)

# Cache invalidation for TDD phase changes
def invalidate_tdd_caches(task_id: int):
    """Invalidate relevant caches when TDD phase changes"""
    epic_id = get_epic_id_for_task(task_id)
    get_epic_progress_cached.cache_clear()  # Clear epic progress cache
    
    # Selective cache invalidation for better performance
    cache_keys_to_clear = [
        f"task_status_{task_id}",
        f"epic_progress_{epic_id}",
        f"tdd_phase_{task_id}"
    ]
    
    for key in cache_keys_to_clear:
        if key in lru_cache_store:
            del lru_cache_store[key]
```

### **Query Optimization for TDD Workflows**
- **Batch operations** for TDD phase transitions
- **Use indexes** for all TDD-related foreign key lookups
- **Avoid N+1 queries** in analytics (use JOINs for TDD metrics)
- **Monitor performance** with <1ms target for TDAH immediate feedback

### **Performance Monitoring for TDAH**
```python
# Performance tracking optimized for TDAH feedback
class TDAHPerformanceMonitor:
    def __init__(self):
        self.performance_thresholds = {
            'instant_feedback': 0.001,  # 1ms for immediate dopamine
            'acceptable': 0.010,        # 10ms still feels responsive
            'slow_warning': 0.050,      # 50ms starts to feel sluggish
            'timeout_warning': 0.100    # 100ms triggers impatience
        }
    
    def track_query_for_tdah_user(self, query: str, duration: float, user_id: int):
        user_profile = get_user_profile(user_id)
        
        if user_profile.has_tdah_traits:
            if duration > self.performance_thresholds['slow_warning']:
                # Provide encouraging feedback even for slow queries
                self.show_patience_encouragement(f"Processing your request... {duration:.2f}s")
            
            # Track patterns for optimization
            self.record_tdah_performance_metric(user_id, query, duration)
```

---

## 🧠 **IA-Enhanced Schema Extensions - Phase 5.1**

### **Enhanced framework_epics Table for Topological Ordering**

The database schema has been enhanced to support AI-driven epic generation and deterministic topological ordering using the DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO algorithm.

#### **New Epic Fields for IA Integration**
```sql
-- Phase 5.1 Schema Extensions for IA-Driven Epic Generation
ALTER TABLE framework_epics ADD COLUMN complexity_score DECIMAL(5,2) DEFAULT 3.0;
ALTER TABLE framework_epics ADD COLUMN effort_estimate INTEGER DEFAULT 7;
ALTER TABLE framework_epics ADD COLUMN sort_order INTEGER DEFAULT 0;
ALTER TABLE framework_epics ADD COLUMN epic_dependencies JSON DEFAULT '[]';
ALTER TABLE framework_epics ADD COLUMN unblock_potential INTEGER DEFAULT 0;
ALTER TABLE framework_epics ADD COLUMN critical_path_weight DECIMAL(5,2) DEFAULT 1.0;
ALTER TABLE framework_epics ADD COLUMN ai_generated BOOLEAN DEFAULT FALSE;
ALTER TABLE framework_epics ADD COLUMN ai_confidence DECIMAL(3,2) DEFAULT 0.8;

-- Performance indexes for topological ordering
CREATE INDEX IF NOT EXISTS idx_epics_sort_order ON framework_epics(project_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_epics_ai_generated ON framework_epics(ai_generated, ai_confidence);
CREATE INDEX IF NOT EXISTS idx_epics_complexity ON framework_epics(complexity_score, effort_estimate);
```

#### **Field Definitions and Usage**
```python
# IA-Enhanced Epic Data Structure
@dataclass
class IAEnhancedEpic:
    # Existing fields
    id: int
    project_id: int  
    epic_key: str
    name: str
    description: str
    status: str
    priority: int
    duration_days: int
    
    # NEW: IA-generated fields (Phase 5.1)
    complexity_score: float      # 1.0-5.0 AI-calculated complexity
    effort_estimate: int         # Days estimate from AI analysis  
    sort_order: int             # Topological ordering position
    epic_dependencies: List[str] # Array of prerequisite epic_keys
    unblock_potential: int      # Number of epics this epic enables
    critical_path_weight: float # Critical path algorithm weight
    ai_generated: bool          # Flag for IA-generated epics
    ai_confidence: float        # AI confidence score (0.0-1.0)
```

#### **Database Operations for IA Epic Generation**
```python
# IA-enhanced database operations
class IAEpicDatabaseOperations:
    def create_ai_generated_epic(self, project_id: int, epic_data: dict) -> int:
        """Create an IA-generated epic with all enhanced fields"""
        with self.db_manager.get_connection("framework") as conn:
            cursor = conn.execute("""
                INSERT INTO framework_epics (
                    project_id, epic_key, name, description, status,
                    complexity_score, effort_estimate, epic_dependencies,
                    unblock_potential, ai_generated, ai_confidence,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id, epic_data['epic_key'], epic_data['name'], 
                epic_data['description'], 'generated',
                epic_data['complexity_score'], epic_data['effort_estimate'],
                json.dumps(epic_data['epic_dependencies']), 
                epic_data['unblock_potential'], True, epic_data['ai_confidence'],
                datetime.now(), datetime.now()
            ))
            
            epic_id = cursor.lastrowid
            conn.commit()
            return epic_id
    
    def update_epic_sort_order(self, epic_id: int, sort_order: int, critical_path_weight: float):
        """Update epic with topological ordering results"""
        with self.db_manager.get_connection("framework") as conn:
            conn.execute("""
                UPDATE framework_epics 
                SET sort_order = ?, critical_path_weight = ?, updated_at = ?
                WHERE id = ?
            """, (sort_order, critical_path_weight, datetime.now(), epic_id))
            conn.commit()
    
    def get_epics_by_topological_order(self, project_id: int) -> List[dict]:
        """Retrieve epics ordered by topological sort_order"""
        with self.db_manager.get_connection("framework") as conn:
            cursor = conn.execute("""
                SELECT 
                    id, epic_key, name, description, complexity_score,
                    effort_estimate, sort_order, epic_dependencies,
                    unblock_potential, critical_path_weight, ai_confidence
                FROM framework_epics 
                WHERE project_id = ? AND deleted_at IS NULL
                ORDER BY sort_order ASC, created_at ASC
            """, (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_epic_dependency_graph(self, project_id: int) -> Dict[str, List[str]]:
        """Extract dependency graph for topological ordering"""
        epics = self.get_epics_by_topological_order(project_id)
        dependency_graph = {}
        
        for epic in epics:
            epic_key = epic['epic_key']
            dependencies = json.loads(epic['epic_dependencies']) if epic['epic_dependencies'] else []
            dependency_graph[epic_key] = dependencies
            
        return dependency_graph
```

#### **Migration Strategy for Existing Data**
```python
# Safe migration preserving existing epic data
class EpicSchemaMigration:
    def migrate_existing_epics_to_ia_enhanced(self):
        """Safely migrate existing epics with default IA values"""
        with self.db_manager.get_connection("framework") as conn:
            # Add columns with safe defaults
            conn.execute("ALTER TABLE framework_epics ADD COLUMN complexity_score DECIMAL(5,2) DEFAULT 3.0")
            conn.execute("ALTER TABLE framework_epics ADD COLUMN effort_estimate INTEGER DEFAULT 7") 
            conn.execute("ALTER TABLE framework_epics ADD COLUMN sort_order INTEGER DEFAULT 0")
            conn.execute("ALTER TABLE framework_epics ADD COLUMN epic_dependencies JSON DEFAULT '[]'")
            conn.execute("ALTER TABLE framework_epics ADD COLUMN unblock_potential INTEGER DEFAULT 0")
            conn.execute("ALTER TABLE framework_epics ADD COLUMN critical_path_weight DECIMAL(5,2) DEFAULT 1.0")
            conn.execute("ALTER TABLE framework_epics ADD COLUMN ai_generated BOOLEAN DEFAULT FALSE")
            conn.execute("ALTER TABLE framework_epics ADD COLUMN ai_confidence DECIMAL(3,2) DEFAULT 0.8")
            
            # Initialize sort_order for existing epics
            conn.execute("""
                UPDATE framework_epics 
                SET sort_order = id - (SELECT MIN(id) FROM framework_epics WHERE project_id = framework_epics.project_id)
                WHERE sort_order = 0
            """)
            
            conn.commit()
            
        # Log migration success
        logger.info("Successfully migrated existing epics to IA-enhanced schema")
```

#### **Performance Optimizations for IA Operations**
```python
# TDAH-friendly IA database operations
class IAPerformanceOptimizations:
    @lru_cache(maxsize=200)
    def get_cached_epic_dependencies(self, project_id: int) -> dict:
        """Cache epic dependencies for fast topological sorting"""
        return self.get_epic_dependency_graph(project_id)
    
    def bulk_insert_ai_epics(self, project_id: int, epics_data: List[dict]) -> List[int]:
        """Bulk insert IA-generated epics for better performance"""
        epic_ids = []
        with self.db_manager.get_connection("framework") as conn:
            for epic_data in epics_data:
                cursor = conn.execute("""
                    INSERT INTO framework_epics (
                        project_id, epic_key, name, description,
                        complexity_score, effort_estimate, epic_dependencies,
                        unblock_potential, ai_generated, ai_confidence,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_id, epic_data['epic_key'], epic_data['name'],
                    epic_data['description'], epic_data['complexity_score'],
                    epic_data['effort_estimate'], json.dumps(epic_data['epic_dependencies']),
                    epic_data['unblock_potential'], True, epic_data['ai_confidence'],
                    datetime.now()
                ))
                epic_ids.append(cursor.lastrowid)
            
            conn.commit()
            
        # Clear dependency cache for project
        self.get_cached_epic_dependencies.cache_clear()
        
        return epic_ids
```

---

## 🔗 **API Patterns for TDD Integration**

### **Legacy DatabaseManager Pattern for TDD**
```python
# Existing TDD pattern (maintained for compatibility)
from streamlit_extension.utils.database import DatabaseManager

def tdd_legacy_pattern():
    db_manager = DatabaseManager()
    
    # TDD cycle management
    result = db_manager.get_all_epics()
    db_manager.create_task_in_red_phase(epic_id, task_data)
    db_manager.transition_tdd_phase(task_id, 'Red', 'Green')
    
    return result
```

### **Modular Database Pattern for TDD**
```python
# New TDD-optimized pattern
from streamlit_extension.database import queries, tdd_operations

def tdd_modular_pattern():
    # TDD-specific operations
    result = tdd_operations.start_red_phase(epic_id, requirements)
    tdd_operations.transition_to_green_phase(task_id)
    tdd_operations.complete_refactor_phase(task_id, improvements)
    
    return result
```

### **Hybrid Usage Pattern for TDD + TDAH**
```python
# Use both APIs optimally for TDD and TDAH needs
from streamlit_extension.utils.database import DatabaseManager
from streamlit_extension.database import queries, tdd_operations

def hybrid_tdd_tdah_pattern():
    # Legacy for complex TDD analytics (battle-tested)
    db_manager = DatabaseManager()
    complex_tdd_analytics = db_manager.get_epic_tdd_effectiveness(epic_id)
    
    # Modular for simple TDAH operations (optimized)
    quick_progress = queries.get_task_progress_fast(task_id)
    immediate_feedback = tdd_operations.get_instant_tdd_status(task_id)
    
    # Best of both worlds for TDD + TDAH workflows
    return {
        'detailed_analytics': complex_tdd_analytics,
        'instant_feedback': quick_progress,
        'tdd_status': immediate_feedback
    }
```

---

## 🚨 **Critical Anti-Patterns for TDD**

### **🔴 SQL Injection Vulnerabilities**
```python
# ❌ NEVER USE IN TDD WORKFLOWS
def dangerous_tdd_query(task_id: int, phase: str):
    # SQL injection vulnerability in TDD context
    query = f"SELECT * FROM framework_tasks WHERE task_id = {task_id} AND tdd_phase = '{phase}'"
    cursor.execute(query)  # DANGEROUS!

# ✅ ALWAYS USE FOR TDD SAFETY
def safe_tdd_query(task_id: int, phase: str):
    cursor.execute("""
        SELECT * FROM framework_tasks 
        WHERE task_id = ? AND tdd_phase = ?
    """, (task_id, phase))
```

### **🔴 Resource Leaks During Hyperfocus**
```python
# ❌ Connection leaks during TDAH hyperfocus sessions
def leaky_hyperfocus_query():
    conn = sqlite3.connect("database.db")
    cursor = conn.execute("SELECT ...")
    # User enters hyperfocus, connection never closed!
    # Can cause resource exhaustion

# ✅ Hyperfocus-safe resource management
def hyperfocus_safe_query():
    with db_manager.get_connection("framework") as conn:
        cursor = conn.execute("SELECT ...")
        result = cursor.fetchall()
        # Connection automatically closed even during hyperfocus
    return result
```

### **🔴 N+1 Query Problems in TDD Analytics**
```python
# ❌ N+1 queries in TDD analytics (slow for TDAH users)
def slow_tdd_analytics():
    epics = get_all_epics()
    for epic in epics:
        tasks = get_tasks_for_epic(epic.id)  # N queries!
        for task in tasks:
            tdd_metrics = get_tdd_metrics_for_task(task.id)  # N*M queries!
    # Causes frustration for TDAH users waiting for feedback

# ✅ Combined query for TDD analytics (TDAH-friendly)
def fast_tdd_analytics():
    query = """
        SELECT 
            e.epic_id, e.title,
            t.task_id, t.title as task_title, t.tdd_phase,
            tm.red_duration, tm.green_duration, tm.refactor_duration
        FROM framework_epics e
        LEFT JOIN framework_tasks t ON e.epic_id = t.epic_id
        LEFT JOIN tdd_metrics tm ON t.task_id = tm.task_id
        ORDER BY e.epic_id, t.task_id
    """
    result = execute_query(query)  # 1 query total - instant for TDAH
    return process_combined_tdd_analytics(result)
```

### **🔴 Missing Error Handling in TDD Operations**
```python
# ❌ Silent failures in TDD workflows
def dangerous_tdd_operation():
    try:
        transition_tdd_phase(task_id, 'Red', 'Green')
    except Exception:
        return None  # TDD state corruption!

# ✅ Proper TDD error handling
def safe_tdd_operation():
    try:
        result = transition_tdd_phase(task_id, 'Red', 'Green')
        return result
    except TDDPhaseError as e:
        logger.error(f"TDD phase transition failed: {e}")
        raise TDDWorkflowError(f"Cannot transition from Red to Green: {e}") from e
    except DatabaseError as e:
        logger.error(f"Database error in TDD operation: {e}")
        raise TDDDatabaseError(f"TDD operation failed: {e}") from e
```

---

## 🔧 **File Tracking - Database Module**

### **Modified Files Checklist**
```
📊 **DATABASE MODULE - ARQUIVOS MODIFICADOS:**

**Core Database:**
- database/connection.py:linha_X - [TDD session-aware connection pooling]
- database/health.py:linha_Y - [TDAH-friendly health monitoring]

**TDD Integration:**
- database/tdd_operations.py - [TDD-specific database operations]
- database/cycle_metrics.py - [TDD cycle analytics storage]

**Query Layer:**
- database/queries.py:linha_Z - [TDAH-optimized query performance]
- database/schema.py:seção_W - [TDD and TDAH data schema]

**Performance:**
- database/database_singleton.py:linha_V - [Hyperfocus-safe singleton pattern]

**Status:** Ready for manual review
**Performance:** All queries <1ms for TDAH immediate feedback
**Security:** SQL injection prevention verified for TDD workflows
**TDD Integration:** Phase transitions and cycle storage operational
**TDAH Support:** Hyperfocus session handling implemented
**Impact:** [Impact on database performance, TDD workflows, and TDAH usability]
```

### **Database Validation Required**
- [ ] No SQL f-strings detected in TDD operations
- [ ] Connection pooling utilized for hyperfocus sessions
- [ ] Error handling comprehensive for TDD workflows
- [ ] Performance thresholds met (<1ms for TDAH feedback)
- [ ] Health monitoring functional with encouraging messages
- [ ] TDD phase transitions atomic and reliable
- [ ] TDAH interruption recovery mechanisms tested

---

*Enterprise database layer with 4,600x+ performance, TDD workflow integration, and TDAH accessibility optimization*