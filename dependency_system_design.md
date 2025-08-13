# 🔗 Dependency System Design - Task Resolution & Validation
**Date:** 2025-08-13  
**Phase:** 1.3 - Design do Sistema de Dependências  
**Focus:** Task Dependency Resolution for Duration System  

---

## 🎯 Overview

The Dependency System manages relationships between tasks within and across epics, ensuring proper execution order and preventing circular dependencies. Based on analysis of real epic data, tasks use string keys like `"5.1a"`, `"3.2b.2"` for dependency references.

---

## 📊 Dependency Patterns Analysis

### **Real Epic Data Patterns**
From analyzed epic files:

**Epic 5 (Cache Management):**
```json
"dependencies": ["5.1a"],                    // Simple within-epic
"dependencies": ["5.1b.1"],                  // TDD phase dependency  
"dependencies": ["5.1b.2", "5.2b.2"],       // Multiple dependencies
"dependencies": ["5.3b.2"],                  // Cross-section dependency
```

**Epic 3 (Interactive Warnings):**
```json
"dependencies": [],                          // No dependencies
"dependencies": ["3.1b.1"],                  // Sequential TDD
"dependencies": ["3.3b.2", "3.2b.2"],       // Multiple parallel completion
"dependencies": ["3.1b.2", "3.2b.2", "3.3b.2", "3.4b.2"],  // Complex convergence
```

**Epic 4 (TDAH Tooling):**
```json
"dependencies": ["4.1b.3", "4.2b.3", "4.3b.3", "4.4b.3", "4.5b.3", "4.6b.3"]  // Integration task
```

### **Dependency Types Identified**
1. **Sequential TDD:** `red → green → refactor`
2. **Parallel Completion:** Multiple tasks must finish before next starts
3. **Integration Points:** Task depends on multiple completed modules
4. **Analysis Dependencies:** Implementation depends on analysis completion

---

## 🏗️ Architecture Design

### **Core Components**

```python
class DependencyResolver:
    """
    Main dependency resolution engine
    """
    def validate_no_cycles(self, task_key: str, dependencies: List[str]) -> bool
    def get_executable_tasks(self, epic_id: Optional[int] = None) -> List[Task]
    def get_dependency_chain(self, task_key: str) -> DependencyChain
    def get_blocking_tasks(self, task_key: str) -> List[Task]
    def resolve_task_key(self, task_key: str) -> Optional[int]  # Convert key to ID
    def validate_dependency_integrity(self) -> ValidationResult

class DependencyChain:
    """
    Represents a full dependency tree for a task
    """
    task_key: str
    dependencies: List[str]
    resolved_dependencies: List[Task]
    depth: int
    is_executable: bool
    blocked_by: List[str]

class DependencyType(Enum):
    """
    Types of dependencies
    """
    BLOCKING = "blocking"      # Must complete before this task can start
    RELATED = "related"        # Related but not blocking
    OPTIONAL = "optional"      # Nice to have but not required
```

### **Database Integration**

**Table Structure (from schema_extensions_v4.sql):**
```sql
CREATE TABLE task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    depends_on_task_key VARCHAR(50) NOT NULL, -- "5.1a", "3.2b.2"
    depends_on_task_id INTEGER,               -- Resolved task ID
    dependency_type VARCHAR(20) DEFAULT 'blocking',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (task_id) REFERENCES framework_tasks(id),
    FOREIGN KEY (depends_on_task_id) REFERENCES framework_tasks(id),
    UNIQUE(task_id, depends_on_task_key)
);
```

**Key Resolution Strategy:**
```python
def resolve_task_key(self, task_key: str) -> Optional[int]:
    """
    Convert task key like "5.1a" to actual task ID
    
    Resolution Logic:
    1. Split task_key: "5.1a" -> epic_id="5", task_key="1a"
    2. Find epic by epic_key=epic_id  
    3. Find task by task_key within that epic
    4. Return framework_tasks.id
    """
    parts = task_key.split('.')
    if len(parts) < 2:
        return None
        
    epic_key = parts[0]
    task_part = '.'.join(parts[1:])  # Handle "1b.1" style keys
    
    # Query: SELECT t.id FROM framework_tasks t 
    #        JOIN framework_epics e ON t.epic_id = e.id
    #        WHERE e.epic_key = epic_key AND t.task_key = task_part
```

---

## 🔄 Dependency Resolution Algorithms

### **1. Cycle Detection (Tarjan's Algorithm)**

```python
def validate_no_cycles(self, task_key: str, dependencies: List[str]) -> bool:
    """
    Detect circular dependencies using DFS with color marking
    
    White: Unvisited
    Gray: Visiting (in current path)  
    Black: Visited (completed)
    """
    visited = {}  # task_key -> color
    
    def dfs(node: str, path: Set[str]) -> bool:
        if node in path:  # Gray node - cycle detected
            return False
            
        if visited.get(node) == 'black':  # Already processed
            return True
            
        path.add(node)
        visited[node] = 'gray'
        
        # Visit all dependencies
        deps = self.get_task_dependencies(node)
        for dep in deps:
            if not dfs(dep, path):
                return False
                
        path.remove(node)
        visited[node] = 'black'
        return True
    
    return dfs(task_key, set())
```

### **2. Executable Tasks Resolution**

```python
def get_executable_tasks(self, epic_id: Optional[int] = None) -> List[Task]:
    """
    Get tasks that can be executed (all dependencies satisfied)
    """
    query = """
    SELECT t.* FROM framework_tasks t
    WHERE t.status != 'completed'
    AND (%(epic_id)s IS NULL OR t.epic_id = %(epic_id)s)
    AND NOT EXISTS (
        SELECT 1 FROM task_dependencies d
        JOIN framework_tasks dep_task ON d.depends_on_task_id = dep_task.id
        WHERE d.task_id = t.id 
        AND d.dependency_type = 'blocking'
        AND dep_task.status != 'completed'
    )
    """
    
    return self.db.execute(query, {'epic_id': epic_id})
```

### **3. Dependency Chain Analysis**

```python
def get_dependency_chain(self, task_key: str) -> DependencyChain:
    """
    Build complete dependency tree for a task
    """
    def build_chain(task_key: str, visited: Set[str], depth: int = 0) -> dict:
        if task_key in visited:
            return {"error": "cycle_detected", "task_key": task_key}
            
        visited.add(task_key)
        
        dependencies = self.get_task_dependencies(task_key)
        dep_chains = []
        
        for dep in dependencies:
            dep_chain = build_chain(dep, visited.copy(), depth + 1)
            dep_chains.append(dep_chain)
            
        return {
            "task_key": task_key,
            "depth": depth,
            "dependencies": dependencies,
            "dependency_chains": dep_chains,
            "is_executable": len([d for d in dependencies 
                                if not self.is_task_completed(d)]) == 0
        }
    
    chain_data = build_chain(task_key, set())
    return DependencyChain.from_dict(chain_data)
```

---

## ⚡ Performance Optimizations

### **1. Dependency Caching**
```python
class DependencyCache:
    """
    Cache dependency resolution results
    """
    def __init__(self, ttl_seconds: int = 300):
        self._cache = {}
        self._ttl = ttl_seconds
        
    def get_executable_tasks(self, epic_id: Optional[int]) -> Optional[List[Task]]:
        cache_key = f"executable_{epic_id}"
        return self._get_cached(cache_key)
        
    def invalidate_epic(self, epic_id: int):
        """Invalidate cache when epic tasks change status"""
        keys_to_remove = [k for k in self._cache.keys() 
                         if k.startswith(f"epic_{epic_id}_")]
        for key in keys_to_remove:
            del self._cache[key]
```

### **2. Batch Dependency Resolution**
```python
def resolve_multiple_task_keys(self, task_keys: List[str]) -> Dict[str, int]:
    """
    Resolve multiple task keys in a single query for efficiency
    """
    # Build mapping of epic_key -> [task_keys] 
    epic_groups = defaultdict(list)
    for task_key in task_keys:
        epic_key = task_key.split('.')[0]
        task_part = '.'.join(task_key.split('.')[1:])
        epic_groups[epic_key].append((task_key, task_part))
    
    # Single query per epic instead of per task
    resolution_map = {}
    for epic_key, tasks in epic_groups.items():
        task_parts = [t[1] for t in tasks]
        query = """
        SELECT t.task_key, t.id FROM framework_tasks t
        JOIN framework_epics e ON t.epic_id = e.id  
        WHERE e.epic_key = %s AND t.task_key IN (%s)
        """ % (epic_key, ','.join(['?' for _ in task_parts]))
        
        results = self.db.execute(query, [epic_key] + task_parts)
        for task_key, task_id in results:
            full_key = f"{epic_key}.{task_key}"
            resolution_map[full_key] = task_id
            
    return resolution_map
```

---

## 🧪 Testing Strategy

### **1. Cycle Detection Tests**
```python
def test_detect_simple_cycle():
    # A -> B -> A
    deps = {"A": ["B"], "B": ["A"]}
    assert not resolver.validate_no_cycles("A", deps["A"])

def test_detect_complex_cycle():
    # A -> B -> C -> D -> B (cycle in middle)
    deps = {"A": ["B"], "B": ["C"], "C": ["D"], "D": ["B"]}
    assert not resolver.validate_no_cycles("A", deps["A"])

def test_no_cycle_complex_tree():
    # Complex but acyclic dependency tree
    deps = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
    assert resolver.validate_no_cycles("A", deps["A"])
```

### **2. Executable Tasks Tests**
```python
def test_executable_tasks_basic():
    # Task with no dependencies should be executable
    tasks = resolver.get_executable_tasks()
    no_dep_tasks = [t for t in tasks if not t.dependencies]
    assert len(no_dep_tasks) > 0

def test_executable_tasks_after_completion():
    # Complete a dependency, next task should become executable
    task_a_id = complete_task("5.1a")
    executable = resolver.get_executable_tasks()
    dependent_tasks = [t for t in executable if "5.1a" in t.dependencies]
    assert len(dependent_tasks) > 0
```

### **3. Real Epic Data Tests**
```python
def test_epic_5_dependencies():
    # Test actual dependencies from epico_5.json
    epic_5_deps = {
        "5.1b.1": [],
        "5.1b.2": ["5.1b.1"], 
        "5.1b.3": ["5.1b.2"],
        "5.2b.1": ["5.2a"],
        "5.2b.2": ["5.2b.1"],
        "5.3b.1": ["5.1b.2", "5.2b.2"]  # Convergence point
    }
    
    # All should be valid (no cycles)
    for task, deps in epic_5_deps.items():
        assert resolver.validate_no_cycles(task, deps)
        
    # Task 5.3b.1 should be blocked until 5.1b.2 and 5.2b.2 complete
    executable = resolver.get_executable_tasks()
    assert "5.3b.1" not in [t.task_key for t in executable]
```

---

## 🔧 Implementation Plan

### **Phase 1.3 Tasks:**
1. **Create DependencyResolver class** - Core resolution engine
2. **Implement cycle detection** - Tarjan's algorithm for cycle detection
3. **Build executable task queries** - SQL optimization for performance
4. **Create dependency chain analysis** - Full tree traversal
5. **Add caching layer** - Performance optimization
6. **Write comprehensive tests** - Cover all edge cases

### **Integration Points:**
- **DatabaseManager:** Add dependency-related methods
- **Task Migration:** Populate task_dependencies table from JSON data
- **Streamlit UI:** Display dependency chains and blocked tasks
- **Duration System:** Consider dependencies in timeline calculation

### **Performance Targets:**
- **Cycle Detection:** < 50ms for complex dependency trees
- **Executable Tasks Query:** < 100ms for full epic
- **Dependency Chain:** < 200ms for deep hierarchies
- **Cache Hit Ratio:** > 80% for repeated queries

---

## 📋 API Interface

### **Public Methods:**
```python
class DependencyResolver:
    def validate_no_cycles(self, task_key: str, dependencies: List[str]) -> bool:
        """Validate that adding dependencies won't create cycles"""
        
    def get_executable_tasks(self, epic_id: Optional[int] = None) -> List[Task]:
        """Get tasks that can be executed immediately"""
        
    def get_dependency_chain(self, task_key: str) -> DependencyChain:
        """Get full dependency tree for a task"""
        
    def get_blocking_tasks(self, task_key: str) -> List[Task]:
        """Get tasks that this task blocks (reverse dependencies)"""
        
    def resolve_task_key(self, task_key: str) -> Optional[int]:
        """Convert task key to database ID"""
        
    def add_dependency(self, task_key: str, depends_on: str, 
                      dep_type: DependencyType = DependencyType.BLOCKING) -> bool:
        """Add new dependency with validation"""
        
    def remove_dependency(self, task_key: str, depends_on: str) -> bool:
        """Remove dependency relationship"""
        
    def validate_dependency_integrity(self) -> ValidationResult:
        """Validate all dependencies in database"""
```

---

## ✅ Success Criteria

1. **Functional:**
   - ✅ Detect all circular dependencies
   - ✅ Correctly identify executable tasks
   - ✅ Build accurate dependency chains
   - ✅ Handle complex convergence patterns from real epics

2. **Performance:**
   - ✅ < 100ms for typical dependency operations
   - ✅ Cache frequently accessed dependency data
   - ✅ Efficient batch resolution for multiple tasks

3. **Data Integrity:**
   - ✅ All task keys resolve to valid tasks
   - ✅ No orphaned dependencies
   - ✅ Consistent dependency state across operations

4. **Integration:**
   - ✅ Seamless integration with Duration System
   - ✅ Support for all 9 real epic migration patterns
   - ✅ Compatible with existing TDD workflow

---

*Design completed: 2025-08-13*  
*Ready for Phase 2: Implementation*  
*Supports: All real epic dependency patterns*