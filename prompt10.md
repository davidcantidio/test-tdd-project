# PROMPT 10: Query Builder Implementation

## 🎯 OBJETIVO
Implementar query builder para resolver item do report.md: "Replace ad-hoc SQL strings with query builders or ORM models."

## 📁 ARQUIVOS ALVO (SEM INTERSEÇÃO)
- `streamlit_extension/utils/query_builder.py` (NOVO)
- `streamlit_extension/utils/query_executor.py` (NOVO)
- `tests/test_query_builder.py` (NOVO)

## 🚀 DELIVERABLES

### 1. Query Builder (`streamlit_extension/utils/query_builder.py`)

```python
"""
🔧 SQL Query Builder - Type-Safe Database Operations

Replaces ad-hoc SQL strings with structured query building:
- Fluent interface for query construction
- SQL injection prevention
- Type safety
- Query optimization
- Debug logging
- Performance metrics
"""

class QueryBuilder:
    """Fluent interface SQL query builder."""
    
    def __init__(self, table_name):
        """Initialize query builder for specific table."""
        self.table = table_name
        self.query_type = None
        self.columns = []
        self.conditions = []
        self.joins = []
        self.order_by = []
        self.group_by = []
        self.having = []
        self.limit_value = None
        self.offset_value = None
        self.values = {}
        self.parameters = []
    
    def select(self, *columns):
        """Add SELECT columns."""
        self.query_type = "SELECT"
        self.columns.extend(columns)
        return self
    
    def where(self, condition, *params):
        """Add WHERE condition with parameters."""
        self.conditions.append(condition)
        self.parameters.extend(params)
        return self
    
    def join(self, table, on_condition):
        """Add INNER JOIN."""
        self.joins.append(f"INNER JOIN {table} ON {on_condition}")
        return self
    
    def left_join(self, table, on_condition):
        """Add LEFT JOIN."""
        self.joins.append(f"LEFT JOIN {table} ON {on_condition}")
        return self
    
    def order_by(self, column, direction="ASC"):
        """Add ORDER BY clause."""
        self.order_by.append(f"{column} {direction}")
        return self
    
    def limit(self, count):
        """Add LIMIT clause."""
        self.limit_value = count
        return self
    
    def offset(self, count):
        """Add OFFSET clause."""
        self.offset_value = count
        return self
    
    def insert(self, **values):
        """Build INSERT query."""
        self.query_type = "INSERT"
        self.values = values
        return self
    
    def update(self, **values):
        """Build UPDATE query."""
        self.query_type = "UPDATE"
        self.values = values
        return self
    
    def delete(self):
        """Build DELETE query."""
        self.query_type = "DELETE"
        return self
    
    def build(self):
        """Build final SQL query with parameters."""
        if self.query_type == "SELECT":
            return self._build_select()
        elif self.query_type == "INSERT":
            return self._build_insert()
        elif self.query_type == "UPDATE":
            return self._build_update()
        elif self.query_type == "DELETE":
            return self._build_delete()
        else:
            raise ValueError("No query type specified")
    
    def _build_select(self):
        """Build SELECT query."""
        columns = ", ".join(self.columns) if self.columns else "*"
        query = f"SELECT {columns} FROM {self.table}"
        
        if self.joins:
            query += " " + " ".join(self.joins)
        
        if self.conditions:
            query += " WHERE " + " AND ".join(self.conditions)
        
        if self.group_by:
            query += " GROUP BY " + ", ".join(self.group_by)
        
        if self.having:
            query += " HAVING " + " AND ".join(self.having)
        
        if self.order_by:
            query += " ORDER BY " + ", ".join(self.order_by)
        
        if self.limit_value:
            query += f" LIMIT {self.limit_value}"
        
        if self.offset_value:
            query += f" OFFSET {self.offset_value}"
        
        return query, tuple(self.parameters)

class ClientQueryBuilder(QueryBuilder):
    """Specialized query builder for clients."""
    
    def __init__(self):
        super().__init__("framework_clients")
    
    def active_only(self):
        """Filter only active clients."""
        return self.where("status = ?", "active")
    
    def by_tier(self, tier):
        """Filter by client tier."""
        return self.where("client_tier = ?", tier)
    
    def search_by_name(self, search_term):
        """Search clients by name."""
        return self.where("name LIKE ?", f"%{search_term}%")
    
    def with_project_count(self):
        """Include project count in results."""
        return self.left_join(
            "framework_projects p", 
            "framework_clients.id = p.client_id"
        ).select(
            "framework_clients.*",
            "COUNT(p.id) as project_count"
        ).group_by("framework_clients.id")

class ProjectQueryBuilder(QueryBuilder):
    """Specialized query builder for projects."""
    
    def __init__(self):
        super().__init__("framework_projects")
    
    def for_client(self, client_id):
        """Filter projects for specific client."""
        return self.where("client_id = ?", client_id)
    
    def active_only(self):
        """Filter only active projects."""
        return self.where("status = ?", "active")
    
    def with_client_info(self):
        """Include client information."""
        return self.left_join(
            "framework_clients c",
            "framework_projects.client_id = c.id"
        ).select(
            "framework_projects.*",
            "c.name as client_name",
            "c.industry as client_industry"
        )
    
    def with_epic_stats(self):
        """Include epic statistics."""
        return self.left_join(
            "framework_epics e",
            "framework_projects.id = e.project_id"
        ).select(
            "framework_projects.*",
            "COUNT(e.id) as epic_count",
            "SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END) as completed_epics"
        ).group_by("framework_projects.id")

class EpicQueryBuilder(QueryBuilder):
    """Specialized query builder for epics."""
    
    def __init__(self):
        super().__init__("framework_epics")
    
    def for_project(self, project_id):
        """Filter epics for specific project."""
        return self.where("project_id = ?", project_id)
    
    def by_status(self, status):
        """Filter by status."""
        return self.where("status = ?", status)
    
    def with_task_stats(self):
        """Include task statistics."""
        return self.left_join(
            "framework_tasks t",
            "framework_epics.id = t.epic_id"
        ).select(
            "framework_epics.*",
            "COUNT(t.id) as task_count",
            "SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks"
        ).group_by("framework_epics.id")

class TaskQueryBuilder(QueryBuilder):
    """Specialized query builder for tasks."""
    
    def __init__(self):
        super().__init__("framework_tasks")
    
    def for_epic(self, epic_id):
        """Filter tasks for specific epic."""
        return self.where("epic_id = ?", epic_id)
    
    def by_status(self, status):
        """Filter by status."""
        return self.where("status = ?", status)
    
    def by_tdd_phase(self, phase):
        """Filter by TDD phase."""
        return self.where("tdd_phase = ?", phase)
    
    def with_epic_info(self):
        """Include epic information."""
        return self.left_join(
            "framework_epics e",
            "framework_tasks.epic_id = e.id"
        ).select(
            "framework_tasks.*",
            "e.name as epic_name",
            "e.project_id as project_id"
        )
```

### 2. Query Executor (`streamlit_extension/utils/query_executor.py`)

```python
"""
⚡ Query Executor - Safe Database Operations

Executes queries built by QueryBuilder with:
- Parameter binding
- Connection management
- Transaction support
- Error handling
- Performance logging
"""

class QueryExecutor:
    """Executes database queries safely."""
    
    def __init__(self, db_manager):
        """Initialize with database manager."""
        
    def execute_query(self, query_builder):
        """Execute query built by QueryBuilder."""
        
    def execute_select(self, query_builder):
        """Execute SELECT query and return results."""
        
    def execute_insert(self, query_builder):
        """Execute INSERT query and return new ID."""
        
    def execute_update(self, query_builder):
        """Execute UPDATE query and return affected rows."""
        
    def execute_delete(self, query_builder):
        """Execute DELETE query and return affected rows."""
        
    def execute_transaction(self, query_builders):
        """Execute multiple queries in transaction."""
```

### 3. Test Suite (`tests/test_query_builder.py`)

```python
"""Test query builder implementation."""

class TestQueryBuilder:
    def test_select_query_building(self):
        """Test SELECT query construction."""
        
    def test_insert_query_building(self):
        """Test INSERT query construction."""
        
    def test_update_query_building(self):
        """Test UPDATE query construction."""
        
    def test_delete_query_building(self):
        """Test DELETE query construction."""
        
    def test_join_operations(self):
        """Test JOIN query construction."""
        
    def test_parameter_binding(self):
        """Test safe parameter binding."""
        
    def test_specialized_builders(self):
        """Test specialized query builders."""
```

## 🔧 REQUISITOS TÉCNICOS

1. **Fluent Interface**: Chainable method calls
2. **SQL Injection Prevention**: Parameter binding
3. **Type Safety**: Validated query construction
4. **Performance**: Optimized query generation
5. **Flexibility**: Support for complex queries
6. **Debugging**: Query logging and analysis

## 📊 SUCCESS CRITERIA

- [ ] Fluent interface query builder implementado
- [ ] SQL injection prevention via parameter binding
- [ ] Specialized builders para clients/projects/epics/tasks
- [ ] Query executor com transaction support
- [ ] Performance logging implementado
- [ ] Ad-hoc SQL strings substituídos