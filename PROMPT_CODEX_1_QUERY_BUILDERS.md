# PROMPT CODEX 1: SQL Query Builders Implementation

## TASK
Implementar query builders seguros para substituir SQL strings ad-hoc em DatabaseManager

## PATTERN
Criar classes QueryBuilder para cada tipo de operação SQL com parameter binding e validação

## FILES
- `streamlit_extension/utils/query_builders.py` (NOVO)
- `streamlit_extension/utils/database.py` (refatorar métodos específicos)

## CONTEXT
Report.md item 91: "Replace ad-hoc SQL strings with query builders or ORM models"
Prevenir SQL injection e melhorar manutenibilidade

## IMPLEMENTATION

### 1. Criar QueryBuilder Base (streamlit_extension/utils/query_builders.py)
```python
from typing import Dict, List, Any, Optional, Union
import sqlite3

class BaseQueryBuilder:
    def __init__(self):
        self.query_parts = []
        self.parameters = []
        
    def build(self) -> tuple[str, List[Any]]:
        """Retorna (query_string, parameters)"""
        return " ".join(self.query_parts), self.parameters
        
    def add_where_condition(self, condition: str, *params):
        """Adiciona condição WHERE com parameters"""
        if params:
            self.parameters.extend(params)
        return self

class SelectQueryBuilder(BaseQueryBuilder):
    def __init__(self, table: str):
        super().__init__()
        self.query_parts = ["SELECT"]
        self.table = table
        
    def columns(self, *cols: str):
        self.query_parts.append(", ".join(cols))
        return self
        
    def from_table(self):
        self.query_parts.extend(["FROM", self.table])
        return self
        
    def where(self, condition: str, *params):
        if "WHERE" not in self.query_parts:
            self.query_parts.append("WHERE")
        else:
            self.query_parts.append("AND")
        self.add_where_condition(condition, *params)
        return self
        
    def limit(self, count: int, offset: Optional[int] = None):
        self.query_parts.append(f"LIMIT {count}")
        if offset:
            self.query_parts.append(f"OFFSET {offset}")
        return self

class InsertQueryBuilder(BaseQueryBuilder):
    def __init__(self, table: str):
        super().__init__()
        self.table = table
        self.columns_list = []
        self.values_list = []
        
    def values(self, **kwargs):
        self.columns_list = list(kwargs.keys())
        self.values_list = list(kwargs.values())
        self.parameters.extend(self.values_list)
        return self
        
    def build(self) -> tuple[str, List[Any]]:
        placeholders = ", ".join(["?" for _ in self.columns_list])
        columns_str = ", ".join(self.columns_list)
        query = f"INSERT INTO {self.table} ({columns_str}) VALUES ({placeholders})"
        return query, self.parameters

class UpdateQueryBuilder(BaseQueryBuilder):
    def __init__(self, table: str):
        super().__init__()
        self.table = table
        self.set_clauses = []
        
    def set(self, **kwargs):
        for key, value in kwargs.items():
            self.set_clauses.append(f"{key} = ?")
            self.parameters.append(value)
        return self
        
    def where(self, condition: str, *params):
        self.add_where_condition(condition, *params)
        return self
        
    def build(self) -> tuple[str, List[Any]]:
        set_clause = ", ".join(self.set_clauses)
        query_parts = [f"UPDATE {self.table} SET {set_clause}"]
        
        if any("WHERE" in part for part in self.query_parts):
            where_conditions = []
            for i, part in enumerate(self.query_parts):
                if i > 0:  # Skip primeira parte
                    where_conditions.append(part)
            if where_conditions:
                query_parts.append("WHERE " + " ".join(where_conditions))
                
        return " ".join(query_parts), self.parameters

class DeleteQueryBuilder(BaseQueryBuilder):
    def __init__(self, table: str):
        super().__init__()
        self.table = table
        
    def where(self, condition: str, *params):
        self.add_where_condition(condition, *params)
        return self
        
    def build(self) -> tuple[str, List[Any]]:
        query_parts = [f"DELETE FROM {self.table}"]
        
        if self.query_parts:
            query_parts.append("WHERE " + " ".join(self.query_parts))
            
        return " ".join(query_parts), self.parameters

# Factory Functions
def select_from(table: str) -> SelectQueryBuilder:
    return SelectQueryBuilder(table)

def insert_into(table: str) -> InsertQueryBuilder:
    return InsertQueryBuilder(table)

def update_table(table: str) -> UpdateQueryBuilder:
    return UpdateQueryBuilder(table)

def delete_from(table: str) -> DeleteQueryBuilder:
    return DeleteQueryBuilder(table)
```

### 2. Refatorar DatabaseManager específicos métodos (database.py)

Substituir APENAS estes métodos com query builders (não tocar no resto):

```python
# NO MÉTODO get_clients()
def get_clients(self, limit: Optional[int] = None, offset: Optional[int] = 0) -> List[Dict]:
    from .query_builders import select_from
    
    query, params = (select_from("framework_clients")
                    .columns("*")
                    .from_table()
                    .limit(limit or 1000, offset)
                    .build())
    
    return self.execute_query(query, params, fetch_all=True)

# NO MÉTODO create_client()  
def create_client(self, client_data: Dict[str, Any]) -> Optional[int]:
    from .query_builders import insert_into
    
    query, params = (insert_into("framework_clients")
                    .values(**client_data)
                    .build())
    
    return self.execute_query(query, params, return_id=True)

# NO MÉTODO update_client()
def update_client(self, client_id: int, client_data: Dict[str, Any]) -> bool:
    from .query_builders import update_table
    
    query, params = (update_table("framework_clients")
                    .set(**client_data)
                    .where("id = ?", client_id)
                    .build())
    
    return self.execute_query(query, params) is not None

# NO MÉTODO delete_client()
def delete_client(self, client_id: int) -> bool:
    from .query_builders import delete_from
    
    query, params = (delete_from("framework_clients")
                    .where("id = ?", client_id)
                    .build())
    
    return self.execute_query(query, params) is not None
```

## VERIFICATION
1. Query builders geram SQL válido com parameter binding
2. Métodos do DatabaseManager funcionam com query builders
3. Nenhuma SQL string hardcoded nos métodos refatorados
4. Testes existentes continuam passando

## NOTES
- Focar APENAS nos métodos listados - não mexer em outros
- Manter compatibilidade com API existente
- Parameter binding obrigatório para prevenir SQL injection