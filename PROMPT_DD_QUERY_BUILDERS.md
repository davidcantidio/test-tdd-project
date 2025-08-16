# 🤖 PROMPT DD: QUERY BUILDER IMPLEMENTATION

## 🎯 OBJECTIVE
Replace ad-hoc SQL strings with secure query builders to address report.md requirement: "Replace ad-hoc SQL strings with query builders or ORM models" in the Technical Debt Registry.

## 📁 FILES TO CREATE

### 1. duration_system/query_builders.py (NEW FILE)

Create a comprehensive query builder system that eliminates SQL injection risks and improves maintainability.

```python
#!/usr/bin/env python3
"""
Secure Query Builder System
Replaces ad-hoc SQL strings with parameterized, secure query builders.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
import sqlite3


class QueryType(Enum):
    """Query operation types."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class JoinType(Enum):
    """SQL join types."""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN" 
    RIGHT = "RIGHT JOIN"
    FULL = "FULL OUTER JOIN"


@dataclass
class QueryCondition:
    """Represents a WHERE condition."""
    field: str
    operator: str  # =, !=, >, <, >=, <=, LIKE, IN, NOT IN
    value: Any
    logical_op: str = "AND"  # AND, OR
    
    def to_sql(self) -> Tuple[str, Any]:
        """Convert condition to SQL with parameter."""
        if self.operator == "IN":
            placeholders = ",".join("?" for _ in self.value)
            return f"{self.field} IN ({placeholders})", self.value
        elif self.operator == "NOT IN":
            placeholders = ",".join("?" for _ in self.value)
            return f"{self.field} NOT IN ({placeholders})", self.value
        else:
            return f"{self.field} {self.operator} ?", [self.value]


@dataclass 
class QueryJoin:
    """Represents a table join."""
    table: str
    join_type: JoinType
    on_condition: str
    

class SecureQueryBuilder:
    """Secure SQL query builder with parameter binding."""
    
    def __init__(self, table: str):
        """Initialize query builder for specific table."""
        self.table = table
        self.query_type: Optional[QueryType] = None
        self.select_fields: List[str] = []
        self.conditions: List[QueryCondition] = []
        self.joins: List[QueryJoin] = []
        self.order_by: List[str] = []
        self.group_by: List[str] = []
        self.limit_value: Optional[int] = None
        self.offset_value: Optional[int] = None
        self.insert_data: Dict[str, Any] = {}
        self.update_data: Dict[str, Any] = {}
        
    def select(self, *fields: str) -> 'SecureQueryBuilder':
        """Add SELECT fields."""
        self.query_type = QueryType.SELECT
        if fields:
            self.select_fields.extend(fields)
        else:
            self.select_fields = ["*"]
        return self
        
    def insert(self, data: Dict[str, Any]) -> 'SecureQueryBuilder':
        """Set INSERT data."""
        self.query_type = QueryType.INSERT
        self.insert_data = data
        return self
        
    def update(self, data: Dict[str, Any]) -> 'SecureQueryBuilder':
        """Set UPDATE data."""
        self.query_type = QueryType.UPDATE
        self.update_data = data
        return self
        
    def delete(self) -> 'SecureQueryBuilder':
        """Set DELETE operation."""
        self.query_type = QueryType.DELETE
        return self
        
    def where(self, field: str, operator: str, value: Any, logical_op: str = "AND") -> 'SecureQueryBuilder':
        """Add WHERE condition."""
        condition = QueryCondition(field, operator, value, logical_op)
        self.conditions.append(condition)
        return self
        
    def where_in(self, field: str, values: List[Any]) -> 'SecureQueryBuilder':
        """Add WHERE IN condition."""
        return self.where(field, "IN", values)
        
    def where_like(self, field: str, pattern: str) -> 'SecureQueryBuilder':
        """Add WHERE LIKE condition."""
        return self.where(field, "LIKE", pattern)
        
    def join(self, table: str, on_condition: str, join_type: JoinType = JoinType.INNER) -> 'SecureQueryBuilder':
        """Add table join."""
        join = QueryJoin(table, join_type, on_condition)
        self.joins.append(join)
        return self
        
    def left_join(self, table: str, on_condition: str) -> 'SecureQueryBuilder':
        """Add LEFT JOIN."""
        return self.join(table, on_condition, JoinType.LEFT)
        
    def order_by(self, field: str, direction: str = "ASC") -> 'SecureQueryBuilder':
        """Add ORDER BY clause."""
        self.order_by.append(f"{field} {direction}")
        return self
        
    def group_by(self, field: str) -> 'SecureQueryBuilder':
        """Add GROUP BY clause."""
        self.group_by.append(field)
        return self
        
    def limit(self, count: int) -> 'SecureQueryBuilder':
        """Add LIMIT clause."""
        self.limit_value = count
        return self
        
    def offset(self, count: int) -> 'SecureQueryBuilder':
        """Add OFFSET clause."""
        self.offset_value = count
        return self
        
    def build(self) -> Tuple[str, List[Any]]:
        """Build final SQL query with parameters."""
        if self.query_type == QueryType.SELECT:
            return self._build_select()
        elif self.query_type == QueryType.INSERT:
            return self._build_insert()
        elif self.query_type == QueryType.UPDATE:
            return self._build_update()
        elif self.query_type == QueryType.DELETE:
            return self._build_delete()
        else:
            raise ValueError("Query type not set")
            
    def _build_select(self) -> Tuple[str, List[Any]]:
        """Build SELECT query."""
        query_parts = [f"SELECT {', '.join(self.select_fields)}"]
        query_parts.append(f"FROM {self.table}")
        params = []
        
        # Add JOINs
        for join in self.joins:
            query_parts.append(f"{join.join_type.value} {join.table} ON {join.on_condition}")
            
        # Add WHERE conditions
        if self.conditions:
            where_parts = []
            for i, condition in enumerate(self.conditions):
                sql_part, condition_params = condition.to_sql()
                if i > 0:
                    where_parts.append(condition.logical_op)
                where_parts.append(sql_part)
                params.extend(condition_params if isinstance(condition_params, list) else [condition_params])
            query_parts.append("WHERE " + " ".join(where_parts))
            
        # Add GROUP BY
        if self.group_by:
            query_parts.append(f"GROUP BY {', '.join(self.group_by)}")
            
        # Add ORDER BY  
        if self.order_by:
            query_parts.append(f"ORDER BY {', '.join(self.order_by)}")
            
        # Add LIMIT/OFFSET
        if self.limit_value:
            query_parts.append(f"LIMIT {self.limit_value}")
            if self.offset_value:
                query_parts.append(f"OFFSET {self.offset_value}")
                
        return " ".join(query_parts), params
        
    def _build_insert(self) -> Tuple[str, List[Any]]:
        """Build INSERT query."""
        fields = list(self.insert_data.keys())
        placeholders = ",".join("?" for _ in fields)
        query = f"INSERT INTO {self.table} ({', '.join(fields)}) VALUES ({placeholders})"
        params = list(self.insert_data.values())
        return query, params
        
    def _build_update(self) -> Tuple[str, List[Any]]:
        """Build UPDATE query."""
        set_parts = [f"{field} = ?" for field in self.update_data.keys()]
        query_parts = [f"UPDATE {self.table}", f"SET {', '.join(set_parts)}"]
        params = list(self.update_data.values())
        
        # Add WHERE conditions
        if self.conditions:
            where_parts = []
            for i, condition in enumerate(self.conditions):
                sql_part, condition_params = condition.to_sql()
                if i > 0:
                    where_parts.append(condition.logical_op)
                where_parts.append(sql_part)
                params.extend(condition_params if isinstance(condition_params, list) else [condition_params])
            query_parts.append("WHERE " + " ".join(where_parts))
            
        return " ".join(query_parts), params
        
    def _build_delete(self) -> Tuple[str, List[Any]]:
        """Build DELETE query."""
        query_parts = [f"DELETE FROM {self.table}"]
        params = []
        
        # Add WHERE conditions
        if self.conditions:
            where_parts = []
            for i, condition in enumerate(self.conditions):
                sql_part, condition_params = condition.to_sql()
                if i > 0:
                    where_parts.append(condition.logical_op)
                where_parts.append(sql_part)
                params.extend(condition_params if isinstance(condition_params, list) else [condition_params])
            query_parts.append("WHERE " + " ".join(where_parts))
            
        return " ".join(query_parts), params


class EpicQueryBuilder(SecureQueryBuilder):
    """Specialized query builder for epics with common operations."""
    
    def __init__(self):
        super().__init__("framework_epics")
        
    def with_client_info(self) -> 'EpicQueryBuilder':
        """Join with client information."""
        self.left_join("framework_clients", "framework_epics.client_id = framework_clients.id")
        return self
        
    def with_project_info(self) -> 'EpicQueryBuilder':
        """Join with project information."""
        self.left_join("framework_projects", "framework_epics.project_id = framework_projects.id")
        return self
        
    def active_only(self) -> 'EpicQueryBuilder':
        """Filter to active epics only."""
        self.where("status", "!=", "archived")
        return self
        
    def by_client(self, client_id: int) -> 'EpicQueryBuilder':
        """Filter by client ID."""
        self.where("client_id", "=", client_id)
        return self
        
    def with_points_range(self, min_points: int, max_points: int) -> 'EpicQueryBuilder':
        """Filter by points range."""
        self.where("points_value", ">=", min_points)
        self.where("points_value", "<=", max_points)
        return self


class TaskQueryBuilder(SecureQueryBuilder):
    """Specialized query builder for tasks."""
    
    def __init__(self):
        super().__init__("framework_tasks")
        
    def with_epic_info(self) -> 'TaskQueryBuilder':
        """Join with epic information."""
        self.left_join("framework_epics", "framework_tasks.epic_id = framework_epics.id")
        return self
        
    def by_tdd_phase(self, phase: str) -> 'TaskQueryBuilder':
        """Filter by TDD phase."""
        self.where("tdd_phase", "=", phase)
        return self
        
    def by_status(self, status: str) -> 'TaskQueryBuilder':
        """Filter by task status."""
        self.where("status", "=", status)
        return self
        
    def recent_tasks(self, days: int = 7) -> 'TaskQueryBuilder':
        """Filter to recent tasks."""
        self.where("created_at", ">=", f"datetime('now', '-{days} days')")
        return self


# Factory functions for convenience
def query_epics() -> EpicQueryBuilder:
    """Create epic query builder."""
    return EpicQueryBuilder()

def query_tasks() -> TaskQueryBuilder:
    """Create task query builder."""
    return TaskQueryBuilder()

def query_table(table_name: str) -> SecureQueryBuilder:
    """Create generic query builder for any table."""
    return SecureQueryBuilder(table_name)


# Export main components
__all__ = [
    'SecureQueryBuilder',
    'EpicQueryBuilder', 
    'TaskQueryBuilder',
    'QueryType',
    'JoinType',
    'QueryCondition',
    'query_epics',
    'query_tasks', 
    'query_table'
]
```

### 2. Update Files to Use Query Builders

Create examples of how to replace existing SQL strings:

**Before (SQL injection risk):**
```python
# DANGEROUS - SQL injection risk
def get_epics_by_client(self, client_id: int):
    query = f"SELECT * FROM framework_epics WHERE client_id = {client_id}"
    return self.cursor.execute(query).fetchall()
```

**After (Secure query builder):**
```python
# SECURE - Parameter binding
def get_epics_by_client(self, client_id: int):
    query, params = (query_epics()
                    .select()
                    .with_client_info()
                    .by_client(client_id)
                    .active_only()
                    .order_by("created_at", "DESC")
                    .build())
    return self.cursor.execute(query, params).fetchall()
```

## 📋 IMPLEMENTATION AREAS

### 1. Epic Operations
Replace SQL strings in:
- `get_epics()`, `get_epics_paginated()`, `get_epics_by_client()`
- `create_epic()`, `update_epic()`, `delete_epic()`
- Epic analytics and filtering operations

### 2. Task Operations  
Replace SQL strings in:
- `get_tasks()`, `get_tasks_paginated()`, `get_tasks_by_epic()`
- `create_task()`, `update_task()`, `delete_task()`
- TDD phase filtering and status updates

### 3. Analytics Queries
Replace complex SQL in:
- `get_epic_analytics()`, `get_dashboard_analytics()`
- `get_productivity_metrics()`, `get_tdd_metrics()`
- Time tracking and session queries

### 4. Cascade Operations
Replace SQL in cascade transactions:
- `duration_system/cascade_transactions.py`
- Safe table relationship queries
- Hierarchical delete operations

## ✅ SECURITY IMPROVEMENTS

### 1. SQL Injection Prevention
```python
# Before: Vulnerable to injection
query = f"SELECT * FROM tasks WHERE status = '{user_input}'"

# After: Safe parameter binding  
query, params = (query_tasks()
                .select()
                .by_status(user_input)
                .build())
```

### 2. Input Validation
```python
class SecureQueryBuilder:
    def where(self, field: str, operator: str, value: Any):
        # Validate field names against whitelist
        if field not in self._allowed_fields:
            raise ValueError(f"Field {field} not allowed")
        
        # Validate operators
        if operator not in ["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN", "NOT IN"]:
            raise ValueError(f"Operator {operator} not allowed")
            
        return self
```

### 3. Query Complexity Limits
```python
def build(self) -> Tuple[str, List[Any]]:
    # Prevent overly complex queries
    if len(self.joins) > 5:
        raise ValueError("Too many joins in query")
    
    if len(self.conditions) > 20:
        raise ValueError("Too many conditions in query")
        
    return self._build_query()
```

## ✅ REQUIREMENTS

1. **Create secure query builder system** in new file
2. **Replace ALL ad-hoc SQL strings** with query builders
3. **Maintain 100% functionality** - All queries work identically  
4. **Improve security** - Eliminate SQL injection vectors
5. **Add specialized builders** for epics and tasks
6. **Include comprehensive examples** in docstrings
7. **Add input validation** for field names and operators

## 🚫 WHAT NOT TO CHANGE
- Query result formats or data structures
- Method signatures in DatabaseManager
- Import statements in existing files
- Functionality or performance
- Database schema or table structure

## ✅ VERIFICATION CHECKLIST
- [ ] All SQL strings replaced with query builders
- [ ] No SQL injection vulnerabilities remain
- [ ] All existing functionality preserved
- [ ] Query builders handle all existing query patterns
- [ ] Specialized builders for epics and tasks created
- [ ] Input validation implemented
- [ ] Comprehensive docstrings included
- [ ] Performance equivalent or better than original

## 🎯 CONTEXT
This addresses report.md requirement: "Replace ad-hoc SQL strings with query builders or ORM models" in the Technical Debt Registry.

The goal is to eliminate SQL injection risks while improving code maintainability and readability.