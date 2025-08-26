# 🤖 CLAUDE.md - Utility Scripts & Tools

**Module:** scripts/  
**Purpose:** Comprehensive utility scripts for maintenance, analysis, testing, and setup  
**Architecture:** Category-organized tools for development, operations, and system management  
**Last Updated:** 2025-08-22

---

## 🔧 **Scripts Overview**

Enterprise-grade utility toolkit featuring:
- **80+ Utility Scripts** organized by functional category
- **Maintenance Tools**: Database optimization, backup, health monitoring
- **Analysis Tools**: Code analysis, data structure examination, architecture auditing
- **Testing Tools**: Integration testing, performance validation, system certification
- **Setup Tools**: Environment initialization, data creation, system bootstrapping
- **Migration Tools**: Data migration, schema evolution, ETL processes

---

## 🏗️ **Scripts Architecture**

### **Directory Structure**
```
scripts/
├── __init__.py                    # 🔧 Module initialization
├── maintenance/                   # 🔧 System maintenance tools
│   ├── database_maintenance.py    # Complete database maintenance
│   ├── benchmark_database.py      # Performance benchmarking
│   └── simple_benchmark.py        # Quick performance checks
├── analysis/                      # 🔍 Code and data analysis tools
│   ├── analysis_type_hints.py     # Type hint coverage analysis
│   ├── audit_gap_analysis.py      # Architecture gap analysis
│   ├── audit_json_structure.py    # JSON structure validation
│   └── [10+ analysis tools]       # Comprehensive analysis suite
├── testing/                       # 🧪 System testing and validation
│   ├── comprehensive_integrity_test.py # Production certification
│   ├── test_database_integrity.py # Database validation
│   ├── performance_demo.py        # Performance testing
│   └── [25+ testing tools]        # Complete testing toolkit
├── migration/                     # 🔄 Data migration tools
│   ├── migrate_real_json_data.py  # JSON to database migration
│   ├── migrate_hierarchy_v6.py    # Schema evolution
│   ├── etl_migration_script_*.py  # ETL pipelines
│   └── [15+ migration tools]      # Migration management
├── setup/                         # 🛠️ System setup and initialization
│   ├── create_framework_db.py     # Database initialization
│   ├── create_realistic_data.py   # Test data generation
│   └── [setup utilities]          # Environment preparation
└── [root utilities]               # Core system utilities
    ├── cleanup_cache.py           # Cache management
    ├── generate_api_docs.py       # Documentation generation
    └── health_check.py            # System health validation
```

### **Script Categories**

1. **Maintenance Scripts**: Database optimization, backup, monitoring
2. **Analysis Scripts**: Code analysis, architecture auditing, data validation
3. **Testing Scripts**: Integration testing, performance validation, certification
4. **Migration Scripts**: Data migration, schema evolution, ETL processes
5. **Setup Scripts**: Environment initialization, data creation, bootstrapping

---

## 🔧 **Maintenance Scripts** (`maintenance/`)

### **Database Maintenance** (`database_maintenance.py`)

**Purpose**: Comprehensive database maintenance and optimization system

#### **Core Features**
- **Automated Backup**: Compressed backups with metadata
- **Health Checks**: Comprehensive database validation
- **Performance Optimization**: VACUUM, REINDEX, ANALYZE
- **Cleanup Operations**: Remove orphaned records and optimize storage
- **Monitoring**: Performance metrics and health reporting

#### **Usage Examples**

##### **Complete Maintenance**
```bash
# Run full maintenance (backup + cleanup + optimization)
python scripts/maintenance/database_maintenance.py

# Maintenance with custom retention
python scripts/maintenance/database_maintenance.py --retention-days 30
```

##### **Specific Operations**
```bash
# Health check only
python scripts/maintenance/database_maintenance.py health

# Backup only
python scripts/maintenance/database_maintenance.py backup

# Cleanup only
python scripts/maintenance/database_maintenance.py cleanup

# Optimization only
python scripts/maintenance/database_maintenance.py optimize
```

##### **Advanced Options**
```bash
# Custom backup directory
python scripts/maintenance/database_maintenance.py backup --backup-dir /custom/path

# Force optimization (even if not needed)
python scripts/maintenance/database_maintenance.py optimize --force

# Verbose output with detailed logging
python scripts/maintenance/database_maintenance.py --verbose
```

#### **Maintenance Features**
```python
# Programmatic usage
from scripts.maintenance.database_maintenance import DatabaseMaintenance

# Initialize maintenance system
maintenance = DatabaseMaintenance(
    framework_db="framework.db",
    timer_db="task_timer.db"
)

# Health check
health_result = maintenance.run_health_check()
print(f"Health Status: {health_result['status']}")
print(f"Issues Found: {health_result['issues_count']}")

# Automated backup
backup_result = maintenance.create_backup()
print(f"Backup Created: {backup_result['backup_file']}")
print(f"Backup Size: {backup_result['size_mb']} MB")

# Performance optimization
optimization_result = maintenance.optimize_performance()
print(f"Performance Gain: {optimization_result['improvement_percentage']}%")
```

### **Database Benchmarking** (`benchmark_database.py`)

**Purpose**: Performance benchmarking and query optimization analysis

#### **Usage Examples**
```bash
# Standard benchmark
python scripts/maintenance/benchmark_database.py

# Extended benchmark with load testing
python scripts/maintenance/benchmark_database.py --extended

# Benchmark specific operations
python scripts/maintenance/benchmark_database.py --operations crud,query,transaction
```

#### **Benchmark Categories**
- **CRUD Operations**: Insert, Update, Delete, Select performance
- **Query Performance**: Complex queries, joins, aggregations
- **Transaction Performance**: ACID compliance and concurrency
- **Index Effectiveness**: Index usage and optimization recommendations
- **Connection Pool Performance**: Pool efficiency and scalability

### **Simple Benchmark** (`simple_benchmark.py`)

**Purpose**: Quick performance validation for development

#### **Usage Examples**
```bash
# Quick 30-second benchmark
python scripts/maintenance/simple_benchmark.py

# Custom duration
python scripts/maintenance/simple_benchmark.py --duration 60
```

---

## 🔍 **Analysis Scripts** (`analysis/`)

### **Type Hints Analysis** (`analysis_type_hints.py`)

**Purpose**: Comprehensive type hint coverage analysis for code quality

#### **Usage Examples**
```bash
# Analyze DatabaseManager type hints
python scripts/analysis/analysis_type_hints.py

# Analyze specific module
python scripts/analysis/analysis_type_hints.py --module streamlit_extension.utils.database

# Generate type hint improvement report
python scripts/analysis/analysis_type_hints.py --report
```

#### **Analysis Features**
- **Coverage Metrics**: Function-level type hint coverage percentage
- **Missing Annotations**: Identify functions missing return type hints
- **Complex Type Analysis**: Suggest improvements for complex types
- **Quality Scoring**: Grade A-F for type safety implementation

### **Architecture Gap Analysis** (`audit_gap_analysis.py`)

**Purpose**: Identify architectural gaps and improvement opportunities

#### **Usage Examples**
```bash
# Complete architecture audit
python scripts/analysis/audit_gap_analysis.py

# Focus on specific components
python scripts/analysis/audit_gap_analysis.py --components database,security,auth

# Generate improvement roadmap
python scripts/analysis/audit_gap_analysis.py --roadmap
```

#### **Analysis Categories**
- **Security Architecture**: Authentication, authorization, input validation
- **Performance Architecture**: Caching, connection pooling, optimization
- **Code Organization**: Module structure, separation of concerns
- **Documentation Coverage**: API documentation, architectural documentation
- **Testing Coverage**: Unit, integration, performance, security testing

### **JSON Structure Analysis** (`audit_json_structure.py`)

**Purpose**: Validate and analyze JSON data structure consistency

#### **Usage Examples**
```bash
# Analyze epic JSON structure
python scripts/analysis/audit_json_structure.py

# Validate specific JSON files
python scripts/analysis/audit_json_structure.py --files epics/user_epics/

# Generate schema documentation
python scripts/analysis/audit_json_structure.py --generate-schema
```

### **Data Structure Comparison** (`compare_structures.py`)

**Purpose**: Compare data structures between JSON and database

#### **Usage Examples**
```bash
# Compare JSON and database schemas
python scripts/analysis/compare_structures.py

# Generate migration recommendations
python scripts/analysis/compare_structures.py --migration-plan

# Validate data consistency
python scripts/analysis/compare_structures.py --validate-consistency
```

### **Additional Analysis Tools**

#### **Temporal Fields Analysis** (`analyze_temporal_fields.py`)
```bash
# Analyze date/time field usage
python scripts/analysis/analyze_temporal_fields.py
```

#### **Unique Fields Catalog** (`catalog_unique_fields.py`)
```bash
# Catalog unique constraints and keys
python scripts/analysis/catalog_unique_fields.py
```

#### **Epic-Task Hierarchy Mapping** (`map_epic_task_hierarchy.py`)
```bash
# Map complete epic-task relationships
python scripts/analysis/map_epic_task_hierarchy.py
```

#### **Invalid Data Identification** (`identify_invalid_data.py`)
```bash
# Find data integrity issues
python scripts/analysis/identify_invalid_data.py
```

#### **Normalization Planning** (`generate_normalization_plan.py`)
```bash
# Generate database normalization recommendations
python scripts/analysis/generate_normalization_plan.py
```

#### **Diagram Generation** (`generate_all_diagrams.py`)
```bash
# Generate architecture and data flow diagrams
python scripts/analysis/generate_all_diagrams.py
```

---

## 🧪 **Testing Scripts** (`testing/`)

### **Comprehensive Integrity Test** (`comprehensive_integrity_test.py`)

**Purpose**: Production certification with complete system validation

#### **Certification Categories**
- **Referential Integrity**: Foreign key consistency, orphaned record detection
- **JSON Consistency**: JSON-database synchronization validation
- **Performance Benchmarks**: Query performance, transaction throughput
- **Bidirectional Sync**: JSON ↔ Database synchronization accuracy
- **Data Consistency**: Cross-table validation, constraint checking

#### **Usage Examples**
```bash
# Complete production certification
python scripts/testing/comprehensive_integrity_test.py

# Quick integrity check
python scripts/testing/comprehensive_integrity_test.py --quick

# Detailed report generation
python scripts/testing/comprehensive_integrity_test.py --detailed-report
```

#### **Certification Output**
```
🔍 COMPREHENSIVE INTEGRITY VALIDATION RESULTS
==============================================

✅ Referential Integrity: PASSED (100% consistency)
✅ JSON Consistency: PASSED (9/9 epics synchronized)
✅ Performance Benchmarks: PASSED (all queries < 10ms)
✅ Bidirectional Sync: PASSED (zero data loss)
✅ Data Consistency: PASSED (zero constraint violations)

🎯 CERTIFICATION: PRODUCTION READY ✅
   Grade: A+ (98.7% overall score)
   Zero critical issues detected
```

### **Database Integrity Testing** (`test_database_integrity.py`)

**Purpose**: Database-specific integrity validation

#### **Usage Examples**
```bash
# Database integrity validation
python scripts/testing/test_database_integrity.py

# Foreign key constraint testing
python scripts/testing/test_database_integrity.py --foreign-keys

# Performance threshold validation
python scripts/testing/test_database_integrity.py --performance
```

### **Performance Testing Suite**

#### **Performance Demo** (`performance_demo.py`)
```bash
# Interactive performance demonstration
python scripts/testing/performance_demo.py

# Load testing simulation
python scripts/testing/performance_demo.py --load-test
```

#### **Connection Pool Debug** (`test_connection_pool_debug.py`)
```bash
# Debug connection pool performance
python scripts/testing/test_connection_pool_debug.py

# Stress test connection pool
python scripts/testing/test_connection_pool_debug.py --stress
```

### **Feature Testing Tools**

#### **Environment Configuration Testing** (`test_environment_config.py`)
```bash
# Test multi-environment configuration
python scripts/testing/test_environment_config.py

# Validate environment variables
python scripts/testing/test_environment_config.py --validate-env
```

#### **Form Components Testing** (`test_form_components.py`)
```bash
# Test reusable form components
python scripts/testing/test_form_components.py

# Validate form security
python scripts/testing/test_form_components.py --security
```

#### **Health Check Testing** (`test_health_check.py`)
```bash
# Test health monitoring system
python scripts/testing/test_health_check.py

# Validate Kubernetes probes
python scripts/testing/test_health_check.py --k8s-probes
```

### **Validation Tools**

#### **API Equivalence Validation** (`api_equivalence_validation.py`) **⭐ NEW**
**Purpose**: Test functional equivalence between legacy DatabaseManager and modular database API

```bash
# Full validation suite  
python scripts/testing/api_equivalence_validation.py

# Quick validation (essential tests only)
python scripts/testing/api_equivalence_validation.py --quick

# Performance comparison only
python scripts/testing/api_equivalence_validation.py --performance-only

# Detailed report generation
python scripts/testing/api_equivalence_validation.py --detailed-report

# Save report to file
python scripts/testing/api_equivalence_validation.py --save-report validation_report.json
```

**Features:**
- **Functional Equivalence**: Verifies both APIs produce identical results
- **Performance Comparison**: Measures speed differences between APIs
- **Breaking Changes Detection**: Identifies API incompatibilities  
- **Data Integrity**: Validates data consistency across APIs
- **Comprehensive Reporting**: Detailed analysis with recommendations

#### **Sync Results Validation** (`validate_sync_results.py`)
```bash
# Validate bidirectional sync accuracy
python scripts/testing/validate_sync_results.py

# Check for data loss during sync
python scripts/testing/validate_sync_results.py --data-loss-check
```

#### **Constants Usage Validation** (`validate_constants_usage.py`)
```bash
# Validate constants and enums usage
python scripts/testing/validate_constants_usage.py

# Check for hardcoded strings
python scripts/testing/validate_constants_usage.py --hardcoded-strings
```

### **Demo and Showcase Tools**

#### **Feature Flags Demo** (`feature_flags_demo.py`)
```bash
# Demonstrate feature flag system
python scripts/testing/feature_flags_demo.py
```

#### **Monitoring Demo** (`monitoring_demo.py`)
```bash
# Demonstrate monitoring and observability
python scripts/testing/monitoring_demo.py
```

#### **Secrets Vault Demo** (`secrets_vault_demo.py`)
```bash
# Demonstrate secrets management
python scripts/testing/secrets_vault_demo.py
```

---

## 🔄 **Migration Scripts** (`migration/`)

### **Real JSON Data Migration** (`migrate_real_json_data.py`)

**Purpose**: Migrate epic data from JSON files to database

#### **Usage Examples**
```bash
# Migrate all epic JSON files
python scripts/migration/migrate_real_json_data.py

# Migrate specific files
python scripts/migration/migrate_real_json_data.py --files epico_1.json,epico_2.json

# Dry run (validate without changes)
python scripts/migration/migrate_real_json_data.py --dry-run
```

### **Hierarchy Migration** (`migrate_hierarchy_v6.py`)

**Purpose**: Migrate to new Client-Project-Epic hierarchy

#### **Usage Examples**
```bash
# Migrate to hierarchy v6
python scripts/migration/migrate_hierarchy_v6.py

# Rollback hierarchy migration
python scripts/migration/rollback_hierarchy_v6.py

# Validate hierarchy consistency
python scripts/migration/migrate_hierarchy_v6.py --validate
```

### **ETL Migration Scripts**

#### **ETL Pipeline** (`etl_migration_script_*.py`)
```bash
# Run ETL pipeline with timestamp
python scripts/migration/etl_migration_script_20250812_003350.py

# Custom ETL configuration
python scripts/migration/etl_migration_script_*.py --config custom_config.json
```

### **Epic-Client Assignment** (`assign_epics_to_client_project.py`)

**Purpose**: Assign epics to client-project hierarchy

#### **Usage Examples**
```bash
# Assign epics to David/ETL SEBRAE structure
python scripts/migration/assign_epics_to_client_project.py

# Custom client-project assignment
python scripts/migration/assign_epics_to_client_project.py --client "Custom Client" --project "Custom Project"
```

### **Migration Utilities**

#### **Migration Utility** (`migration_utility.py`)
```bash
# General migration operations
python scripts/migration/migration_utility.py

# Schema migration tools
python scripts/migration/migration_utility.py --schema-update
```

#### **Column Migration** (`migrate_missing_columns.py`)
```bash
# Migrate missing database columns
python scripts/migration/migrate_missing_columns.py

# Validate column consistency
python scripts/migration/migrate_missing_columns.py --validate
```

#### **Trigger Fixes** (`fix_triggers.py`)
```bash
# Fix database triggers
python scripts/migration/fix_triggers.py

# Validate trigger functionality
python scripts/migration/fix_triggers.py --test-triggers
```

### **Migration Testing**

#### **Test Migration System** (`test_migration_system.py`)
```bash
# Test migration system functionality
python scripts/migration/test_migration_system.py

# Validate migration rollback
python scripts/migration/test_migration_system.py --test-rollback
```

#### **Demo Migration System** (`demo_migration_system.py`)
```bash
# Demonstrate migration capabilities
python scripts/migration/demo_migration_system.py
```

### **Rollback Tools**

#### **Migration Rollback** (`rollback_migration_v7.py`)
```bash
# Rollback migration v7
python scripts/migration/rollback_migration_v7.py

# Partial rollback with validation
python scripts/migration/rollback_migration_v7.py --partial --validate
```

---

## 🛠️ **Setup Scripts** (`setup/`)

### **Framework Database Creation** (`create_framework_db.py`)

**Purpose**: Initialize framework database with complete schema

#### **Usage Examples**
```bash
# Create framework database
python scripts/setup/create_framework_db.py

# Create with sample data
python scripts/setup/create_framework_db.py --with-data

# Create minimal schema
python scripts/setup/create_framework_db.py --minimal
```

### **Realistic Data Creation** (`create_realistic_data.py`)

**Purpose**: Generate realistic test data for development

#### **Usage Examples**
```bash
# Create realistic test data
python scripts/setup/create_realistic_data.py

# Generate specific data volume
python scripts/setup/create_realistic_data.py --clients 5 --projects 10 --epics 25

# Create data with specific patterns
python scripts/setup/create_realistic_data.py --pattern enterprise
```

#### **Data Generation Features**
- **Client Data**: Realistic company names, contacts, business types
- **Project Data**: Project names, descriptions, budgets, timelines
- **Epic Data**: Development epics with tasks, goals, definitions of done
- **Task Data**: Realistic task descriptions, estimates, dependencies
- **Timer Data**: Focus sessions with TDAH-relevant metrics

### **Task Timer Stub Creation** (`create_task_timer_stub.py`)

**Purpose**: Create task timer database with sample sessions

#### **Usage Examples**
```bash
# Create timer database
python scripts/setup/create_task_timer_stub.py

# Create with specific session patterns
python scripts/setup/create_task_timer_stub.py --pattern productivity

# Generate TDAH-focused data
python scripts/setup/create_task_timer_stub.py --tdah-optimized
```

### **Audit Report Creation** (`create_audit_report.py`)

**Purpose**: Generate comprehensive system audit reports

#### **Usage Examples**
```bash
# Create complete audit report
python scripts/setup/create_audit_report.py

# Focus on specific areas
python scripts/setup/create_audit_report.py --areas security,performance,architecture

# Generate executive summary
python scripts/setup/create_audit_report.py --executive-summary
```

---

## 🔧 **Root Utilities**

### **Cache Cleanup** (`cleanup_cache.py`)

**Purpose**: Comprehensive cache management and cleanup

#### **Usage Examples**
```bash
# Preview cleanup operations
python scripts/cleanup_cache.py --dry-run

# Clean all cache types
python scripts/cleanup_cache.py

# Clean specific cache types
python scripts/cleanup_cache.py --types streamlit,python,database

# Aggressive cleanup
python scripts/cleanup_cache.py --aggressive
```

#### **Cache Categories**
- **Streamlit Cache**: Session state, component cache, data cache
- **Python Cache**: `__pycache__`, `.pyc` files, bytecode cache
- **Database Cache**: SQLite WAL/SHM files, temporary tables
- **Application Cache**: Custom application caches
- **Build Cache**: Build artifacts, temporary files

### **API Documentation Generation** (`generate_api_docs.py`)

**Purpose**: Generate comprehensive API documentation

#### **Usage Examples**
```bash
# Generate complete API docs
python scripts/generate_api_docs.py

# Generate docs for specific modules
python scripts/generate_api_docs.py --modules streamlit_extension,duration_system

# Generate with examples
python scripts/generate_api_docs.py --include-examples
```

### **System Health Check** (`health_check.py`)

**Purpose**: Quick system health validation

#### **Usage Examples**
```bash
# Quick health check
python scripts/health_check.py

# Detailed health report
python scripts/health_check.py --detailed

# Health check with metrics
python scripts/health_check.py --metrics
```

### **Docstring Validation** (`validate_docstrings.py`)

**Purpose**: Validate docstring coverage and quality

#### **Usage Examples**
```bash
# Validate all docstrings
python scripts/validate_docstrings.py

# Generate docstring coverage report
python scripts/validate_docstrings.py --coverage-report

# Check specific modules
python scripts/validate_docstrings.py --modules duration_system
```

---

## 🚀 **Workflow Integration**

### **Development Workflow**

#### **Daily Development Routine**
```bash
# 1. Health check
python scripts/health_check.py

# 2. Run integrity tests
python scripts/testing/comprehensive_integrity_test.py --quick

# 3. Performance validation
python scripts/maintenance/simple_benchmark.py

# 4. Clean cache if needed
python scripts/cleanup_cache.py --dry-run
```

#### **Feature Development Workflow**
```bash
# 1. Create realistic test data
python scripts/setup/create_realistic_data.py --pattern feature-test

# 2. Run integration tests
python scripts/testing/test_database_integrity.py

# 3. Validate form components
python scripts/testing/test_form_components.py

# 4. Generate documentation
python scripts/generate_api_docs.py --modules new_feature
```

### **Maintenance Workflow**

#### **Weekly Maintenance**
```bash
# 1. Complete database maintenance
python scripts/maintenance/database_maintenance.py

# 2. Performance benchmarking
python scripts/maintenance/benchmark_database.py

# 3. Architecture analysis
python scripts/analysis/audit_gap_analysis.py

# 4. Type hint analysis
python scripts/analysis/analysis_type_hints.py
```

#### **Monthly Operations**
```bash
# 1. Comprehensive audit
python scripts/setup/create_audit_report.py

# 2. Migration validation
python scripts/testing/validate_sync_results.py

# 3. Performance optimization
python scripts/analysis/generate_normalization_plan.py

# 4. Security validation
python scripts/testing/test_environment_config.py --security
```

### **Deployment Workflow**

#### **Pre-Deployment Validation**
```bash
# 1. Production certification
python scripts/testing/comprehensive_integrity_test.py

# 2. Performance validation
python scripts/maintenance/benchmark_database.py --production

# 3. Security validation
python scripts/testing/test_form_components.py --security

# 4. Migration validation
python scripts/migration/test_migration_system.py
```

#### **Post-Deployment Monitoring**
```bash
# 1. Health monitoring
python scripts/testing/test_health_check.py

# 2. Performance monitoring
python scripts/testing/performance_demo.py --monitor

# 3. Data integrity validation
python scripts/testing/test_database_integrity.py

# 4. System metrics
python scripts/testing/monitoring_demo.py
```

---

## 📊 **Script Categories Summary**

### **Maintenance Scripts** (3 scripts)
- **Database maintenance**: Backup, cleanup, optimization
- **Performance benchmarking**: Query optimization, load testing
- **Quick validation**: Development-time health checks

### **Analysis Scripts** (10+ scripts)
- **Code analysis**: Type hints, architecture, documentation
- **Data analysis**: JSON structure, database schema, consistency
- **Architecture analysis**: Gap analysis, improvement recommendations

### **Testing Scripts** (26+ scripts)
- **Integration testing**: Cross-module functionality validation
- **Performance testing**: Load testing, stress testing, benchmarks
- **Certification testing**: Production readiness validation
- **API Equivalence testing**: Legacy vs Modular API validation (NEW)
- **Component testing**: Individual component validation
- **Demo scripts**: Feature demonstration and showcasing

### **Migration Scripts** (15+ scripts)
- **Data migration**: JSON to database, schema evolution
- **ETL pipelines**: Extract, transform, load operations
- **Hierarchy migration**: Client-project-epic structure
- **Rollback tools**: Migration rollback and recovery

### **Setup Scripts** (4 scripts)
- **Database initialization**: Schema creation, sample data
- **Environment setup**: Configuration, realistic data generation
- **Audit setup**: Report generation, compliance checking

### **Root Utilities** (4 scripts)
- **Cache management**: Cleanup, optimization
- **Documentation**: API docs, docstring validation
- **Health monitoring**: System health, quick validation

---

## 🔧 **Script Development Guidelines**

### **Creating New Scripts**

#### **Script Structure Template**
```python
#!/usr/bin/env python3
"""
🔧 [CATEGORY] - [Script Name]

[Brief description of purpose and functionality]

Usage:
    python scripts/[category]/[script_name].py [options]

Features:
- [Feature 1]
- [Feature 2]
- [Feature 3]
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(description="[Script description]")
    
    # Add command line arguments
    parser.add_argument("--option", help="Option description")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Script logic here
    result = perform_operation(args)
    
    if args.verbose:
        print(f"Operation completed: {result}")

if __name__ == "__main__":
    main()
```

#### **Category Guidelines**
- **maintenance/**: System maintenance, optimization, monitoring
- **analysis/**: Code analysis, data analysis, architecture review
- **testing/**: Testing, validation, certification, demonstration
- **migration/**: Data migration, schema evolution, ETL
- **setup/**: Environment setup, initialization, configuration

### **Integration Standards**
- Use consistent logging format across all scripts
- Implement `--verbose` and `--dry-run` options where appropriate
- Follow error handling patterns with proper exit codes
- Include help text and usage examples
- Use type hints for function signatures

### **Documentation Requirements**
- Clear docstring with purpose and usage
- Command-line interface documentation
- Integration points with other scripts
- Example usage patterns
- Error handling and troubleshooting

---

## 📋 **COMMIT PROCESS FOR SCRIPTS**

### 🎯 **MANDATORY PRE-COMMIT CHECKLIST**

#### **1. Script File Analysis (OBRIGATÓRIO)**
Antes de comitar mudanças em scripts, SEMPRE execute:

```bash
# Lista arquivos modificados
git status --porcelain

# Para scripts modificados, teste funcionalidade:
python scripts/[category]/[modified_script].py --help
python scripts/[category]/[modified_script].py --dry-run  # se disponível
```

#### **2. Script-Specific Validation**
Para cada script modificado:

- **✅ Sintaxe validada**: `python -m py_compile script.py`
- **✅ Help funcional**: `--help` retorna informação útil
- **✅ Dry-run testado**: `--dry-run` funciona sem efeitos colaterais
- **✅ Logging configurado**: Output claro e informativo
- **✅ Error handling**: Trata exceções adequadamente

#### **3. Integration Testing**
```bash
# Teste integração com sistema
python scripts/testing/api_equivalence_validation.py --quick
python scripts/maintenance/database_maintenance.py health
python scripts/testing/comprehensive_integrity_test.py --quick
```

#### **4. Script Commit Template**
```bash
git commit -m "$(cat <<'EOF'
scripts: <descrição da mudança no script>

<detalhes da funcionalidade alterada/adicionada>

📊 **SCRIPTS ALTERADOS:**
- MODIFICADOS: scripts/[categoria]/[arquivo].py
- CRIADOS: scripts/[categoria]/[novo_arquivo].py
- REMOVIDOS: scripts/[categoria]/[arquivo_obsoleto].py

🎯 **FUNCIONALIDADE:**
- <nova funcionalidade ou correção>
- <impacto nos workflows existentes>
- <compatibilidade backward>

✅ **VALIDAÇÃO:**
- Sintaxe: OK
- Help: OK  
- Dry-run: OK
- Integration: OK

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

#### **5. Script Documentation Update**
Sempre que adicionar/modificar scripts significativamente:

- **Atualizar CLAUDE.md**: Documentar nova funcionalidade
- **Atualizar contadores**: Ajustar "26+ scripts" se necessário
- **Atualizar examples**: Incluir novos exemplos de uso
- **Atualizar categories**: Se criar nova categoria

#### **6. Post-Commit Verification**
```bash
# Verificar script commitado funciona
git checkout HEAD~1 -- scripts/[script].py  # versão anterior
python scripts/[script].py --help  # teste versão anterior
git checkout HEAD -- scripts/[script].py   # versão atual  
python scripts/[script].py --help  # teste versão atual

# Confirmar melhoria/correção
```

### 🔍 **Script-Specific Guidelines**

#### **Testing Scripts**: Extra validation required
- **Todos os testes passam** antes do commit
- **Performance não degradou** em scripts críticos
- **Relatórios gerados** corretamente

#### **Migration Scripts**: Critical safety checks
- **Dry-run obrigatório** antes de qualquer commit
- **Rollback testado** se aplicável
- **Backup validado** antes de operações destrutivas

#### **Maintenance Scripts**: Production safety
- **Sem efeitos colaterais** em dry-run
- **Health checks** passam após execução
- **Monitoring** não afetado por mudanças

---

*This comprehensive script toolkit provides enterprise-grade utilities for all aspects of system management, from development through production deployment and ongoing maintenance.*

---

## 📋 **FILE TRACKING PROTOCOL - SCRIPTS MODULE**

### **🎯 TRACKING OBRIGATÓRIO PARA SCRIPTS**

**Sempre que modificar scripts, use este template pós-execução:**

```
📊 **SCRIPTS - ARQUIVOS MODIFICADOS:**

**Maintenance Scripts:**
- scripts/maintenance/[arquivo].py - [mudança específica e impacto]

**Analysis Scripts:**
- scripts/analysis/[arquivo].py - [mudança específica e impacto]

**Testing Scripts:**
- scripts/testing/[arquivo].py - [mudança específica e impacto]

**Migration Scripts:**
- scripts/migration/[arquivo].py - [mudança específica e impacto]

**Setup Scripts:**
- scripts/setup/[arquivo].py - [mudança específica e impacto]

**Root Utilities:**
- scripts/[arquivo].py - [mudança específica e impacto]

**Status:** Pronto para revisão manual
**Validation:** [Descrição dos testes executados]
**Impact:** [Impacto nos workflows existentes]
```

### **🔧 CHECKLIST PRÉ-MODIFICAÇÃO SCRIPTS**
- [ ] Backup de scripts críticos
- [ ] Teste --help em scripts existentes
- [ ] Verificação de dependências
- [ ] Validação de argumentos de linha de comando

### **✅ CHECKLIST PÓS-MODIFICAÇÃO SCRIPTS**
- [ ] Lista completa de scripts modificados gerada
- [ ] Teste de sintaxe (py_compile) executado
- [ ] Teste --help funcional
- [ ] Teste --dry-run (se aplicável)
- [ ] Validação de integração com sistema
- [ ] Documentação atualizada conforme necessário
- [ ] Aprovação para próxima etapa

### **🚨 VALIDAÇÃO ESPECÍFICA POR CATEGORIA**

#### **Testing Scripts**
- [ ] Todos os testes passam
- [ ] Performance não degradou
- [ ] Relatórios gerados corretamente

#### **Migration Scripts**  
- [ ] Dry-run obrigatório executado
- [ ] Rollback testado
- [ ] Backup validado

#### **Maintenance Scripts**
- [ ] Sem efeitos colaterais em dry-run
- [ ] Health checks passam
- [ ] Monitoring não afetado

**Regra Absoluta:** Nunca commitar scripts sem completar checklist e gerar lista de arquivos modificados.

---

## 🔗 **See Also - Related Documentation**

**Main Project Documentation:**
- **📜 [Root CLAUDE.md](../CLAUDE.md)** - Complete system overview, essential commands
- **📊 [Project README](../README.md)** - Quick start, installation, basic maintenance commands

**System Integration:**
- **🧪 [Testing](../tests/CLAUDE.md)** - Test execution, validation scripts, coverage analysis
- **📱 [Streamlit Extension](../streamlit_extension/CLAUDE.md)** - Application architecture, debugging tools
- **⏱️ [Duration System](../duration_system/CLAUDE.md)** - Security utilities, performance tools

**Operations & Maintenance:**
- **⚙️ [Config](../config/CLAUDE.md)** - Environment configuration, deployment scripts
- **📊 [Monitoring](../monitoring/CLAUDE.md)** - Health monitoring, observability tools
- **🔄 [Migration](../migration/CLAUDE.md)** - Data migration tools, schema management

---

*Comprehensive utility toolkit for development, operations, and system management with enterprise-grade automation and validation.*