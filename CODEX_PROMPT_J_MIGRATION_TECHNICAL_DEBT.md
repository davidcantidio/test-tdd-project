# 🔧 CODEX PROMPT J: Migration Scripts & Technical Debt Resolution

## 🎯 **OBJETIVO**
Resolver technical debt identificado no report.md: "Create migration scripts for missing columns", "Replace ad-hoc SQL strings with query builders", "Remove .streamlit_cache from repository".

## 📁 **ARQUIVOS ALVO (ISOLADOS - SEM INTERSEÇÃO)**
```
migration/                                         # Novo diretório
migration/__init__.py                              # Package init
migration/schema_migrations.py                     # Scripts de migração
migration/query_builder.py                         # Query builder system
migration/cleanup_scripts.py                       # Scripts de limpeza
migration/migrations/                               # Arquivos de migração
migration/migrations/001_add_missing_columns.sql   # Migração de colunas
migration/migrations/002_add_indexes.sql           # Migração de índices
migration/migrations/003_cleanup_data.sql          # Limpeza de dados
scripts/cleanup_cache.py                           # Script de limpeza de cache
scripts/validate_migrations.py                     # Validação de migrações
tests/test_migrations.py                           # Testes de migração
tests/test_query_builder.py                        # Testes do query builder
```

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. migration/schema_migrations.py**
```python
# MigrationManager class:
# - get_current_version()
# - apply_migrations()
# - rollback_migration()
# - validate_schema()

# Migration class:
# - execute()
# - rollback()
# - validate()
# - get_dependencies()

# SchemaValidator class:
# - validate_tables()
# - validate_columns()
# - validate_indexes()
# - validate_constraints()
```

### **2. migration/query_builder.py**
```python
# QueryBuilder class:
# - select()
# - insert()
# - update()
# - delete()
# - join()
# - where()
# - order_by()
# - limit()

# SQLBuilder class:
# - build_select_query()
# - build_insert_query()
# - build_update_query()
# - build_delete_query()
# - sanitize_params()

# QueryExecutor class:
# - execute_query()
# - execute_transaction()
# - batch_execute()
```

### **3. migration/cleanup_scripts.py**
```python
# CacheCleanup class:
# - remove_streamlit_cache()
# - clean_temp_files()
# - update_gitignore()
# - validate_cleanup()

# DataCleanup class:
# - remove_orphaned_records()
# - normalize_data()
# - fix_inconsistencies()
# - vacuum_database()

# RepositoryCleanup class:
# - clean_git_history()
# - remove_large_files()
# - optimize_repository()
```

## 🗃️ **MIGRAÇÕES DE SCHEMA OBRIGATÓRIAS**

### **1. migration/migrations/001_add_missing_columns.sql**
```sql
-- Adicionar colunas identificadas no report.md
ALTER TABLE framework_epics ADD COLUMN points_value INTEGER DEFAULT 0;
ALTER TABLE framework_epics ADD COLUMN due_date DATE;
ALTER TABLE framework_epics ADD COLUMN icon VARCHAR(50) DEFAULT 'default';
ALTER TABLE framework_epics ADD COLUMN priority INTEGER DEFAULT 1;
ALTER TABLE framework_epics ADD COLUMN estimated_hours DECIMAL(10,2);

-- Adicionar colunas para auditing
ALTER TABLE framework_epics ADD COLUMN created_by VARCHAR(100);
ALTER TABLE framework_epics ADD COLUMN updated_by VARCHAR(100);
ALTER TABLE framework_epics ADD COLUMN version INTEGER DEFAULT 1;

-- Adicionar soft delete
ALTER TABLE framework_epics ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE framework_tasks ADD COLUMN deleted_at TIMESTAMP NULL;
```

### **2. migration/migrations/002_add_indexes.sql**
```sql
-- Índices para performance
CREATE INDEX idx_epics_status ON framework_epics(status);
CREATE INDEX idx_epics_priority ON framework_epics(priority);
CREATE INDEX idx_epics_due_date ON framework_epics(due_date);
CREATE INDEX idx_epics_deleted_at ON framework_epics(deleted_at);

CREATE INDEX idx_tasks_epic_id ON framework_tasks(epic_id);
CREATE INDEX idx_tasks_status ON framework_tasks(status);
CREATE INDEX idx_tasks_deleted_at ON framework_tasks(deleted_at);

-- Índices compostos
CREATE INDEX idx_epics_status_priority ON framework_epics(status, priority);
CREATE INDEX idx_tasks_epic_status ON framework_tasks(epic_id, status);
```

### **3. migration/migrations/003_cleanup_data.sql**
```sql
-- Limpeza de dados inconsistentes
UPDATE framework_epics SET points_value = 0 WHERE points_value IS NULL;
UPDATE framework_epics SET priority = 1 WHERE priority IS NULL;

-- Normalização de status
UPDATE framework_epics SET status = 'pending' WHERE status = '';
UPDATE framework_tasks SET status = 'pending' WHERE status = '';

-- Remove registros órfãos (se existirem)
DELETE FROM framework_tasks WHERE epic_id NOT IN (SELECT id FROM framework_epics);
```

## 🔧 **QUERY BUILDER IMPLEMENTATION**

### **Exemplo de Uso:**
```python
# Substituir SQL ad-hoc:
# OLD: "SELECT * FROM framework_epics WHERE status = ?"
# NEW:
query = QueryBuilder() \
    .select("*") \
    .from_table("framework_epics") \
    .where("status", "=", "active") \
    .order_by("priority", "DESC") \
    .limit(10)

result = query.execute()
```

### **Tipos de Query Suportados:**
```python
# SELECT com joins
query = QueryBuilder() \
    .select("e.title", "t.description") \
    .from_table("framework_epics e") \
    .join("framework_tasks t", "e.id = t.epic_id") \
    .where("e.status", "=", "active")

# INSERT com validação
query = QueryBuilder() \
    .insert_into("framework_epics") \
    .values({
        "title": "New Epic",
        "status": "pending",
        "priority": 1
    })

# UPDATE com condições
query = QueryBuilder() \
    .update("framework_epics") \
    .set("status", "completed") \
    .where("id", "=", epic_id)

# DELETE com soft delete
query = QueryBuilder() \
    .update("framework_epics") \
    .set("deleted_at", "CURRENT_TIMESTAMP") \
    .where("id", "=", epic_id)
```

## 🧹 **CLEANUP SCRIPTS**

### **Cache Cleanup:**
```python
def cleanup_streamlit_cache():
    """Remove .streamlit_cache directory and update .gitignore"""
    cache_dirs = [
        ".streamlit_cache/",
        "__pycache__/",
        "*.pyc",
        ".pytest_cache/"
    ]
    
    for cache_dir in cache_dirs:
        # Remove directory/files
        # Update .gitignore
        pass
```

### **Repository Cleanup:**
```python
def cleanup_large_files():
    """Remove large files from git history"""
    large_files = [
        "*.db-journal",
        "*.log",
        "logs/*.log"
    ]
    
    # Add to .gitignore
    # Remove from git history if needed
```

## 🧪 **CASOS DE TESTE OBRIGATÓRIOS**

### **Migration Tests:**
```python
def test_apply_migration():
    # Aplicar migração e verificar schema
    
def test_rollback_migration():
    # Rollback de migração
    
def test_migration_dependencies():
    # Verificar dependências entre migrações
    
def test_migration_validation():
    # Validar schema após migração
```

### **Query Builder Tests:**
```python
def test_select_query_builder():
    # Construção de query SELECT
    
def test_insert_query_builder():
    # Construção de query INSERT
    
def test_query_parameter_sanitization():
    # Sanitização de parâmetros
    
def test_complex_join_queries():
    # Queries com múltiplos joins
```

### **Cleanup Tests:**
```python
def test_cache_cleanup():
    # Limpeza de cache
    
def test_gitignore_update():
    # Atualização de .gitignore
    
def test_data_cleanup():
    # Limpeza de dados inconsistentes
```

## 📊 **MIGRATION TRACKING**

### **Migration Table:**
```sql
CREATE TABLE schema_migrations (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100),
    rollback_sql TEXT,
    checksum VARCHAR(64)
);
```

### **Migration Status:**
```python
def get_migration_status():
    return {
        "current_version": "003",
        "pending_migrations": [],
        "applied_migrations": [
            "001_add_missing_columns",
            "002_add_indexes", 
            "003_cleanup_data"
        ]
    }
```

## 🎯 **CRITÉRIOS DE SUCESSO**
1. **3 migrações** de schema aplicadas com sucesso
2. **Query builder** substitui 100% do SQL ad-hoc
3. **.streamlit_cache** completamente removido
4. **.gitignore** atualizado para prevenir cache files
5. **15+ testes** cobrindo todos os cenários
6. **Rollback capability** para todas as migrações
7. **Data integrity** mantida após cleanup

## 🔗 **INTEGRAÇÃO**
```python
# Aplicar migrações:
migration_manager = MigrationManager()
migration_manager.apply_pending_migrations()

# Usar query builder:
from migration.query_builder import QueryBuilder
query = QueryBuilder().select("*").from_table("framework_epics")
```

---

**🎯 RESULTADO ESPERADO:** Sistema completo de migrações e query builder que resolve technical debt do report.md: "migration scripts for missing columns", "replace ad-hoc SQL strings" e "remove .streamlit_cache", mantendo integridade de dados e melhorando qualidade do código.