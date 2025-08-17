# 🤖 CLAUDE.md - Data Migration System

**Module:** migration/  
**Purpose:** Comprehensive data migration and bidirectional synchronization system  
**Architecture:** Multi-layered sync strategy with JSON enrichment and schema migration  
**Last Updated:** 2025-08-17

---

## 🔄 **Migration System Overview**

Enterprise-grade data migration framework featuring:
- **Bidirectional Sync**: JSON ↔ Database synchronization with conflict resolution
- **JSON Enrichment**: 3-layer data enhancement strategy  
- **Schema Migration**: Versioned database schema evolution with rollback
- **Data Integrity**: Checksum validation and change tracking
- **Production Ready**: Transaction safety and comprehensive error handling

---

## 🏗️ **System Architecture**

### **Directory Structure**
```
migration/
├── __init__.py                   # 🔧 Module initialization
├── bidirectional_sync.py         # 🔄 Core bidirectional sync engine
├── json_enrichment.py           # ✨ JSON data enrichment
├── data_base_strategy.py        # 📊 Duration and date calculations  
├── schema_migrations.py         # 🗄️ Schema migration management
├── query_builder.py             # 🔍 Safe SQL query construction
├── cleanup_scripts.py           # 🧹 Data cleanup utilities
├── schema_migration_v7.py       # 📋 Version-specific migrations
└── migrations/                  # 📁 SQL migration files
    ├── 001_create_migration_table.sql
    ├── 001_rollback.sql
    ├── 002_enhance_framework_epics.sql
    ├── 002_rollback.sql
    ├── 003_add_performance_indexes.sql
    └── 003_rollback.sql
```

### **Core Components**

1. **Bidirectional Sync Engine**: JSON ↔ Database synchronization
2. **JSON Enrichment System**: Data enhancement without modification
3. **Schema Migration Manager**: Database evolution with rollback
4. **Data Strategy Calculator**: Duration and date calculation logic
5. **Query Builder**: Safe SQL construction and execution

---

## 🔄 **Bidirectional Sync Engine**

### **BidirectionalSync** (`bidirectional_sync.py`)

**Purpose**: Intelligent synchronization between JSON epic files and database

#### **3-Layer Sync Strategy**

**LAYER 1 - CORE DATA** (Bidirectional JSON ↔ Database):
```python
# Fields synchronized in both directions
core_fields = [
    "name",           # Epic name/title
    "summary",        # Epic description
    "goals",          # Epic objectives (JSON array)
    "definition_of_done",  # Completion criteria (JSON array)
    "labels",         # Epic tags/labels (JSON array)
    "tasks"           # Task list (JSON array)
]
```

**LAYER 2 - CALCULATED FIELDS** (Database → JSON only):
```python
# Fields calculated from database and added to JSON
calculated_fields = [
    "planned_start_date",     # Calculated from duration system
    "planned_end_date",       # Calculated from duration system
    "calculated_duration_days",  # Business day calculations
    "stats",                  # Task completion statistics
    "progress_percentage"     # Calculated progress
]
```

**LAYER 3 - SYSTEM FIELDS** (Database only):
```python
# Fields that remain in database only
system_fields = [
    "id",             # Database primary key
    "created_at",     # Timestamp fields
    "updated_at",     # Timestamp fields
    "assigned_to",    # User assignments
    "points_earned",  # Gamification data
    "github_*"        # GitHub integration fields
]
```

#### **Usage Examples**

##### **Basic Synchronization**
```python
from migration.bidirectional_sync import BidirectionalSync

# Initialize sync engine
sync = BidirectionalSync(
    db_path="framework.db",
    json_dir="epics/user_epics/",
    enable_enrichment=True
)

# Sync specific epic
result = sync.sync_epic_to_database("epico_1.json")
if result["success"]:
    print(f"Synced epic: {result['epic_name']}")

# Sync all epics
results = sync.sync_all_epics()
print(f"Synced {len(results)} epics")
```

##### **Conflict Resolution**
```python
# Enable conflict detection
sync = BidirectionalSync(
    db_path="framework.db",
    json_dir="epics/user_epics/",
    conflict_resolution="database_wins"  # or "json_wins", "manual"
)

# Handle conflicts during sync
result = sync.sync_epic_to_database("epico_1.json")
if result.get("conflicts"):
    for conflict in result["conflicts"]:
        print(f"Conflict in field: {conflict['field']}")
        print(f"JSON value: {conflict['json_value']}")
        print(f"DB value: {conflict['db_value']}")
```

##### **Change Tracking**
```python
# Enable checksum-based change tracking
sync = BidirectionalSync(
    db_path="framework.db", 
    json_dir="epics/user_epics/",
    track_changes=True
)

# Get change summary
changes = sync.get_change_summary()
print(f"Modified epics: {changes['modified_count']}")
print(f"New epics: {changes['new_count']}")
print(f"Unchanged epics: {changes['unchanged_count']}")
```

#### **Advanced Features**

##### **Rollback Capability**
```python
# Create checkpoint before sync
checkpoint_id = sync.create_checkpoint("before_major_sync")

# Perform sync operations
sync.sync_all_epics()

# Rollback if needed
if validation_failed:
    sync.rollback_to_checkpoint(checkpoint_id)
```

##### **Batch Operations**
```python
# Batch sync with transaction safety
with sync.batch_operation() as batch:
    batch.sync_epic("epico_1.json")
    batch.sync_epic("epico_2.json")
    batch.sync_epic("epico_3.json")
    # All operations committed together or rolled back on error
```

##### **Validation and Integrity**
```python
# Validate data integrity
validation_result = sync.validate_data_integrity()
if not validation_result["valid"]:
    for error in validation_result["errors"]:
        print(f"Integrity error: {error}")

# Check sync status
status = sync.get_sync_status()
print(f"Last sync: {status['last_sync_time']}")
print(f"Total epics: {status['total_epics']}")
print(f"Sync conflicts: {status['conflict_count']}")
```

---

## ✨ **JSON Enrichment System**

### **JSONEnrichmentEngine** (`json_enrichment.py`)

**Purpose**: Enrich JSON files with calculated data without modifying original content

#### **Enrichment Strategy**
```python
# Output structure preserves original data
enriched_output = {
    "epic": {
        # Original JSON data unchanged
    },
    "calculated_fields": {
        "planned_start_date": "2025-08-18",
        "planned_end_date": "2025-08-20",
        "calculated_duration_days": 2.0,
        "task_completion_percentage": 75.0,
        "estimated_hours": 16.0,
        "last_calculated": "2025-08-17T10:30:00Z"
    },
    "metadata": {
        "version": "v1.0",
        "enriched_at": "2025-08-17T10:30:00Z",
        "calculation_strategy": "next_monday",
        "data_source": "database"
    }
}
```

#### **Usage Examples**

##### **Basic Enrichment**
```python
from migration.json_enrichment import JSONEnrichmentEngine

# Initialize enrichment engine
enricher = JSONEnrichmentEngine(db_path="framework.db")

# Enrich single epic
enriched_data = enricher.enrich_epic_json("epico_1.json")

# Save enriched version
enricher.save_enriched_epic(
    "epico_1.json", 
    output_dir="epics/enriched/"
)
```

##### **Batch Enrichment**
```python
# Enrich all epics
enricher.enrich_all_epics(
    input_dir="epics/user_epics/",
    output_dir="epics/enriched/"
)

# Enrich specific subset
epic_list = ["epico_1.json", "epico_2.json", "epico_3.json"]
enricher.enrich_epic_list(epic_list, output_dir="epics/enriched/")
```

##### **Custom Calculation Strategies**
```python
# Configure calculation strategy
enricher = JSONEnrichmentEngine(
    db_path="framework.db",
    calculation_strategy="next_monday",  # or "immediate", "next_workday"
    business_calendar=True,
    exclude_holidays=True
)

# Custom duration calculations
custom_calculator = DataBaseCalculator(
    strategy=DateBaseStrategy.IMMEDIATE,
    business_days_only=True
)
enricher.set_calculator(custom_calculator)
```

##### **Validation and Quality Control**
```python
# Validate enriched data
validation_result = enricher.validate_enrichment("epico_1.json")
if validation_result["valid"]:
    print("Enrichment successful")
else:
    for error in validation_result["errors"]:
        print(f"Validation error: {error}")

# Check calculation accuracy
accuracy_report = enricher.get_calculation_accuracy()
print(f"Calculation accuracy: {accuracy_report['accuracy_percentage']}%")
```

---

## 📊 **Data Strategy Calculator**

### **DataBaseCalculator** (`data_base_strategy.py`)

**Purpose**: Calculate planned dates and durations from epic text descriptions

#### **Calculation Strategies**

##### **DateBaseStrategy Enum**
```python
from migration.data_base_strategy import DateBaseStrategy

# Available strategies:
DateBaseStrategy.IMMEDIATE       # Start immediately
DateBaseStrategy.NEXT_MONDAY     # Start next Monday  
DateBaseStrategy.NEXT_WORKDAY    # Start next business day
DateBaseStrategy.CUSTOM_DATE     # User-specified start date
```

##### **Duration Parsing**
```python
from migration.data_base_strategy import DataBaseCalculator

calculator = DataBaseCalculator(strategy=DateBaseStrategy.NEXT_MONDAY)

# Parse duration from text
duration_days = calculator.parse_duration_from_text(
    "This epic should take about 2 weeks to complete"
)
# Returns: 14.0

# Calculate planned dates
planned_dates = calculator.calculate_planned_dates(
    duration_text="1.5 semanas",
    start_strategy=DateBaseStrategy.NEXT_MONDAY
)
print(f"Start: {planned_dates.start_date}")
print(f"End: {planned_dates.end_date}")
print(f"Duration: {planned_dates.duration_days} days")
```

##### **Business Calendar Integration**
```python
# Enable business day calculations
calculator = DataBaseCalculator(
    strategy=DateBaseStrategy.NEXT_WORKDAY,
    business_days_only=True,
    exclude_holidays=True,
    country_code="BR"  # Brazilian holidays
)

# Calculate with holidays excluded
business_dates = calculator.calculate_business_dates(
    start_date="2025-08-18",
    duration_days=5
)
# Automatically excludes weekends and Brazilian holidays
```

##### **Multi-Language Duration Support**
```python
# Supports Portuguese and English duration formats
duration_examples = [
    "2 dias",           # Portuguese: 2 days
    "1.5 semanas",      # Portuguese: 1.5 weeks  
    "3 weeks",          # English: 3 weeks
    "1 mês",            # Portuguese: 1 month
    "2.5 months"        # English: 2.5 months
]

for duration_text in duration_examples:
    days = calculator.parse_duration_from_text(duration_text)
    print(f"'{duration_text}' = {days} days")
```

---

## 🗄️ **Schema Migration System**

### **Schema Migration Manager** (`schema_migrations.py`)

**Purpose**: Version-controlled database schema evolution with rollback support

#### **Migration Class Structure**
```python
from migration.schema_migrations import Migration

# Define migration
migration = Migration(
    version="002",
    sql="""
        ALTER TABLE framework_epics 
        ADD COLUMN planned_start_date TEXT;
        
        ALTER TABLE framework_epics 
        ADD COLUMN planned_end_date TEXT;
    """,
    rollback_sql="""
        ALTER TABLE framework_epics 
        DROP COLUMN planned_start_date;
        
        ALTER TABLE framework_epics 
        DROP COLUMN planned_end_date;
    """,
    dependencies=["001"]
)
```

#### **Usage Examples**

##### **Apply Migrations**
```python
from migration.schema_migrations import MigrationRunner

# Initialize migration runner
runner = MigrationRunner(db_path="framework.db")

# Apply all pending migrations
runner.apply_migrations()

# Apply specific migration
runner.apply_migration("002_enhance_framework_epics.sql")

# Check migration status
status = runner.get_migration_status()
print(f"Applied migrations: {status['applied_count']}")
print(f"Pending migrations: {status['pending_count']}")
```

##### **Rollback Operations**
```python
# Rollback last migration
runner.rollback_last_migration()

# Rollback to specific version
runner.rollback_to_version("001")

# Rollback multiple versions
runner.rollback_migrations(count=3)
```

##### **Migration Validation**
```python
# Validate migration integrity
validation_result = runner.validate_migrations()
if not validation_result["valid"]:
    for error in validation_result["errors"]:
        print(f"Migration error: {error}")

# Check for dependency conflicts
dependency_check = runner.check_dependencies()
if dependency_check["conflicts"]:
    for conflict in dependency_check["conflicts"]:
        print(f"Dependency conflict: {conflict}")
```

### **SQL Migration Files** (`migrations/`)

#### **Migration File Structure**
```sql
-- migrations/002_enhance_framework_epics.sql
-- Migration 002: Enhance framework_epics table with calculated fields

ALTER TABLE framework_epics 
ADD COLUMN planned_start_date TEXT;

ALTER TABLE framework_epics 
ADD COLUMN planned_end_date TEXT;

ALTER TABLE framework_epics 
ADD COLUMN calculated_duration_days REAL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_framework_epics_planned_dates 
ON framework_epics(planned_start_date, planned_end_date);
```

#### **Rollback File Structure**
```sql
-- migrations/002_rollback.sql
-- Rollback 002: Remove enhanced fields from framework_epics

ALTER TABLE framework_epics DROP COLUMN planned_start_date;
ALTER TABLE framework_epics DROP COLUMN planned_end_date;
ALTER TABLE framework_epics DROP COLUMN calculated_duration_days;

DROP INDEX IF EXISTS idx_framework_epics_planned_dates;
```

#### **Migration Tracking**
```sql
-- Automatic tracking in schema_migrations table
SELECT version, applied_at, applied_by 
FROM schema_migrations 
ORDER BY applied_at DESC;

-- Example output:
-- 003 | 2025-08-17 10:30:00 | system
-- 002 | 2025-08-17 09:15:00 | system  
-- 001 | 2025-08-17 08:00:00 | system
```

---

## 🔍 **Query Builder System**

### **SafeQueryBuilder** (`query_builder.py`)

**Purpose**: Safe SQL query construction with injection prevention

#### **Usage Examples**

##### **Basic Query Construction**
```python
from migration.query_builder import SafeQueryBuilder

builder = SafeQueryBuilder()

# Build SELECT query
query = builder.select("framework_epics") \
              .where("status", "=", "active") \
              .where("assigned_to", "IN", ["user1", "user2"]) \
              .order_by("created_at", "DESC") \
              .limit(10) \
              .build()

# Execute with parameters safely bound
results = builder.execute(query)
```

##### **Complex Queries with Joins**
```python
# Build JOIN query
query = builder.select("e.name, t.title") \
              .from_table("framework_epics e") \
              .join("framework_tasks t", "t.epic_id = e.id") \
              .where("e.status", "=", "active") \
              .where("t.status", "!=", "completed") \
              .build()

results = builder.execute(query)
```

##### **Insert and Update Operations**
```python
# Safe INSERT
insert_query = builder.insert("framework_epics") \
                     .values({
                         "name": "New Epic",
                         "status": "active",
                         "created_at": "2025-08-17T10:30:00"
                     }) \
                     .build()

# Safe UPDATE
update_query = builder.update("framework_epics") \
                     .set({"status": "completed"}) \
                     .where("id", "=", epic_id) \
                     .build()
```

##### **Security Features**
```python
# Automatic parameter binding prevents SQL injection
unsafe_input = "'; DROP TABLE framework_epics; --"

# This is safe - parameters are properly bound
query = builder.select("framework_epics") \
              .where("name", "=", unsafe_input) \
              .build()
# Results in: SELECT * FROM framework_epics WHERE name = ?
# Parameters: ["'; DROP TABLE framework_epics; --"]
```

---

## 🧹 **Data Cleanup System**

### **CleanupScripts** (`cleanup_scripts.py`)

**Purpose**: Data maintenance and cleanup utilities

#### **Usage Examples**

##### **Database Cleanup**
```python
from migration.cleanup_scripts import DatabaseCleanup

cleanup = DatabaseCleanup(db_path="framework.db")

# Remove orphaned records
cleanup.remove_orphaned_tasks()
cleanup.remove_orphaned_timer_sessions()

# Clean up old data
cleanup.archive_old_records(days_old=90)

# Vacuum database
cleanup.vacuum_database()
```

##### **JSON File Cleanup**
```python
# Clean up JSON files
json_cleanup = JSONCleanup(json_dir="epics/user_epics/")

# Remove duplicate JSON files
json_cleanup.remove_duplicates()

# Validate JSON structure
validation_results = json_cleanup.validate_all_json_files()

# Fix common JSON issues
json_cleanup.fix_common_issues()
```

##### **Cache Cleanup**
```python
# Clear migration caches
cache_cleanup = CacheCleanup()

# Clear temporary migration files
cache_cleanup.clear_temp_files()

# Reset migration checksums
cache_cleanup.reset_checksums()
```

---

## 🚀 **Integration Workflows**

### **Complete Migration Workflow**

#### **Initial Setup**
```python
from migration.bidirectional_sync import BidirectionalSync
from migration.schema_migrations import MigrationRunner
from migration.json_enrichment import JSONEnrichmentEngine

# 1. Apply schema migrations
runner = MigrationRunner(db_path="framework.db")
runner.apply_migrations()

# 2. Initialize sync engine
sync = BidirectionalSync(
    db_path="framework.db",
    json_dir="epics/user_epics/"
)

# 3. Sync existing data
sync.sync_all_epics()

# 4. Enrich JSON files
enricher = JSONEnrichmentEngine(db_path="framework.db")
enricher.enrich_all_epics(
    input_dir="epics/user_epics/",
    output_dir="epics/enriched/"
)
```

#### **Regular Sync Operations**
```python
# Daily sync workflow
def daily_sync_workflow():
    # 1. Check for conflicts
    conflicts = sync.check_for_conflicts()
    if conflicts:
        handle_conflicts(conflicts)
    
    # 2. Sync JSON to database
    json_results = sync.sync_json_to_database()
    
    # 3. Sync database to JSON
    db_results = sync.sync_database_to_json()
    
    # 4. Update enriched files
    enricher.update_enriched_files()
    
    # 5. Generate sync report
    report = sync.generate_sync_report()
    return report
```

#### **Data Validation Workflow**
```python
# Comprehensive data validation
def validate_data_integrity():
    validation_results = {}
    
    # 1. Validate sync integrity
    validation_results["sync"] = sync.validate_data_integrity()
    
    # 2. Validate enrichment accuracy
    validation_results["enrichment"] = enricher.validate_all_enrichments()
    
    # 3. Validate database schema
    validation_results["schema"] = runner.validate_schema_integrity()
    
    # 4. Generate validation report
    return generate_validation_report(validation_results)
```

### **Backup and Recovery**

#### **Backup Procedures**
```python
from migration.backup_manager import BackupManager

backup_manager = BackupManager(db_path="framework.db")

# Create full backup
backup_id = backup_manager.create_full_backup()

# Create incremental backup
incremental_id = backup_manager.create_incremental_backup(since=backup_id)

# Backup JSON files
json_backup_id = backup_manager.backup_json_files("epics/")
```

#### **Recovery Procedures**
```python
# Restore from backup
recovery_result = backup_manager.restore_from_backup(backup_id)

# Point-in-time recovery
recovery_result = backup_manager.restore_to_timestamp("2025-08-17T10:00:00")

# Validate restored data
validation_result = validate_data_integrity()
```

---

## 📊 **Migration Metrics & Monitoring**

### **Performance Metrics**
```python
# Get migration performance metrics
metrics = sync.get_performance_metrics()

print(f"Average sync time: {metrics['avg_sync_time_ms']}ms")
print(f"Records processed: {metrics['records_processed']}")
print(f"Conflict rate: {metrics['conflict_rate']}%")
print(f"Success rate: {metrics['success_rate']}%")
```

### **Data Quality Metrics**
```python
# Get data quality metrics
quality_metrics = sync.get_data_quality_metrics()

print(f"Data consistency: {quality_metrics['consistency_score']}%")
print(f"Completeness: {quality_metrics['completeness_score']}%")
print(f"Accuracy: {quality_metrics['accuracy_score']}%")
```

### **Migration Status Dashboard**
```python
# Get comprehensive status
status = {
    "schema_version": runner.get_current_version(),
    "last_sync": sync.get_last_sync_time(),
    "pending_migrations": runner.get_pending_migrations(),
    "sync_conflicts": sync.get_unresolved_conflicts(),
    "data_integrity": sync.validate_data_integrity()
}

print(f"System Status: {status}")
```

---

## 🔧 **Development Guidelines**

### **Adding New Migrations**
1. Create SQL migration file: `migrations/XXX_description.sql`
2. Create rollback file: `migrations/XXX_rollback.sql`
3. Test migration on development database
4. Validate rollback functionality
5. Update migration documentation

### **Extending Sync Logic**
1. Add new fields to appropriate layer (Core/Calculated/System)
2. Update sync mapping in `bidirectional_sync.py`
3. Add validation logic for new fields
4. Update enrichment engine if needed
5. Write tests for new functionality

### **Performance Optimization**
- Use connection pooling for database operations
- Implement batch operations for large datasets
- Add indexes for frequently queried fields
- Monitor query performance and optimize as needed
- Use checksums to avoid unnecessary operations

### **Error Handling Standards**
- Always use transaction safety for critical operations
- Implement comprehensive logging for debugging
- Provide detailed error messages with context
- Include rollback procedures for failed operations
- Validate data integrity after major operations

---

## 🔗 **Integration Points**

### **With Streamlit Extension**
```python
# Use in Streamlit pages
from migration.bidirectional_sync import BidirectionalSync

@st.cache_data
def get_enriched_epic_data(epic_id):
    sync = BidirectionalSync(db_path="framework.db")
    return sync.get_enriched_epic(epic_id)
```

### **With Duration System**
```python
# Integration with duration calculations
from duration_system.duration_calculator import DurationCalculator
from migration.data_base_strategy import DataBaseCalculator

# Use duration system in migrations
calculator = DurationCalculator()
migration_calculator = DataBaseCalculator(duration_calculator=calculator)
```

### **With Database Manager**
```python
# Integration with DatabaseManager
from streamlit_extension.utils.database import DatabaseManager
from migration.bidirectional_sync import BidirectionalSync

# Ensure compatibility
db_manager = DatabaseManager(db_path="framework.db")
sync = BidirectionalSync(db_manager=db_manager)
```

---

*This migration system provides enterprise-grade data synchronization with comprehensive integrity validation, rollback capabilities, and performance optimization for production deployment.*