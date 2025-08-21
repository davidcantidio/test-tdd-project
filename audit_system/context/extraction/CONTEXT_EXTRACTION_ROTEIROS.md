# 🗺️ CONTEXT EXTRACTION ROTEIROS - Sétima Camada
**Status:** Systematic Context Mapping for Automated Audit  
**Mission:** 100% functional context extraction for line-by-line analysis  
**Created:** 2025-08-19  

---

## 🎯 **OVERVIEW**

### **Purpose**
Systematic roteiros (scripts/guides) for extracting comprehensive context from existing documentation for each project folder, enabling intelligent automated audit with full contextual awareness.

### **Architecture Changes Required**
- ✅ INDEX.md enhancement with context mapping
- ✅ New context routing files for each major folder
- ✅ Cross-reference documentation matrix
- ✅ Integration points with systematic_file_auditor.py

---

## 📋 **FOLDER-BY-FOLDER CONTEXT ROTEIROS**

### **🏠 ROOT LEVEL CONTEXT (`/`)**
```bash
# ROTEIRO: Root Context Extraction
echo "📋 ROOT CONTEXT EXTRACTION"

# 1. Project Mission & Architecture
cat CLAUDE.md | grep -A 20 "Project Overview"
cat README.md | grep -A 10 "Enterprise TDD Framework"
cat STATUS.md | grep -A 15 "Current Status"

# 2. Navigation & Component Mapping  
cat NAVIGATION.md | grep -A 30 "Project Map"
cat INDEX.md | grep -A 50 "Architecture"

# 3. Critical System Files
cat TROUBLESHOOTING.md | grep -A 10 "Common Problems"
ls -la *.db | head -5  # Database files context
ls -la *.md | head -10 # Documentation inventory

# 4. Environment & Configuration
python config/environment.py 2>/dev/null || echo "Config status: needs check"
cat pyproject.toml 2>/dev/null | head -20 || echo "Dependencies: check requirements.txt"

# CONTEXT OUTPUT: Root system understanding, project mission, architecture overview
```

### **📱 STREAMLIT_EXTENSION CONTEXT (`streamlit_extension/`)**
```bash
# ROTEIRO: Streamlit Extension Context Extraction  
echo "📱 STREAMLIT EXTENSION CONTEXT EXTRACTION"

# 1. Module Overview & TDD Integration
cat streamlit_extension/CLAUDE.md | grep -A 30 "TDD + TDAH INTEGRATION"
cat streamlit_extension/CLAUDE.md | grep -A 20 "Enterprise Features"

# 2. Service Layer Architecture (CRITICAL)
cat streamlit_extension/services/CLAUDE.md | grep -A 40 "Service Architecture for TDD"
ls streamlit_extension/services/*.py | head -10

# 3. Database Layer Understanding (CRITICAL)  
cat streamlit_extension/database/CLAUDE.md | grep -A 30 "Hybrid API Design"
cat streamlit_extension/database/CLAUDE.md | grep -A 20 "Performance Layer"

# 4. Component System (UI Patterns)
cat streamlit_extension/components/CLAUDE.md | grep -A 25 "Component Patterns"
ls streamlit_extension/components/*.py | head -10

# 5. Authentication & Security Context
cat streamlit_extension/auth/CLAUDE.md 2>/dev/null | grep -A 20 "Authentication Architecture" || echo "Auth docs: needs creation"
ls streamlit_extension/auth/*.py | head -5

# 6. Page Structure & Routes
ls streamlit_extension/pages/*.py | head -10
cat streamlit_extension/streamlit_app.py | grep -A 10 "import.*pages" 2>/dev/null || echo "Main app: analyze imports"

# 7. Utils & Core Infrastructure
ls streamlit_extension/utils/*.py | head -15
cat streamlit_extension/utils/database.py | head -50 2>/dev/null || echo "Database utils: analyze structure"

# CONTEXT OUTPUT: Complete Streamlit architecture, TDD integration patterns, service/component structure
```

### **⏱️ DURATION_SYSTEM CONTEXT (`duration_system/`)**
```bash
# ROTEIRO: Duration System Context Extraction
echo "⏱️ DURATION SYSTEM CONTEXT EXTRACTION"

# 1. Module Overview & Core Purpose
cat duration_system/CLAUDE.md | grep -A 25 "TDD + TDAH INTEGRATION"
cat duration_system/CLAUDE.md | grep -A 20 "Core Features"

# 2. Duration Calculation Engine
ls duration_system/*calculator*.py | head -5
ls duration_system/*business*.py | head -5

# 3. Security Stack Analysis  
ls duration_system/*security*.py | head -10
ls duration_system/*cache*.py | head -5

# 4. Utility & Helper Functions
ls duration_system/*.py | grep -v "__pycache__" | head -15

# CONTEXT OUTPUT: Duration calculation patterns, security utilities, business logic context
```

### **🧪 TESTS CONTEXT (`tests/`)**
```bash
# ROTEIRO: Tests Context Extraction
echo "🧪 TESTS CONTEXT EXTRACTION"

# 1. Testing Framework Overview
cat tests/CLAUDE.md | grep -A 30 "Testing Framework Integration"
cat tests/CLAUDE.md | grep -A 20 "Test Categories"

# 2. Test Structure Analysis
ls tests/test_*.py | head -15
ls tests/integration/*.py 2>/dev/null | head -10 || echo "Integration tests: check structure"
ls tests/performance/*.py 2>/dev/null | head -10 || echo "Performance tests: check structure"

# 3. Test Configuration
cat tests/conftest.py | head -30 2>/dev/null || echo "Conftest: analyze fixtures"
cat pytest.ini | head -20 2>/dev/null || echo "Pytest config: check settings"

# CONTEXT OUTPUT: Test patterns, framework understanding, coverage expectations
```

### **🔄 MIGRATION CONTEXT (`migration/`)**
```bash
# ROTEIRO: Migration Context Extraction
echo "🔄 MIGRATION CONTEXT EXTRACTION"

# 1. Migration Framework Overview
cat migration/CLAUDE.md | grep -A 25 "Bidirectional Sync Architecture"
cat migration/CLAUDE.md | grep -A 20 "Data Migration Patterns"

# 2. Migration Scripts & Schema
ls migration/migrations/*.sql 2>/dev/null | head -10 || echo "SQL migrations: check directory"
ls migration/*.py | head -10

# 3. Bidirectional Sync Understanding
cat migration/bidirectional_sync.py | head -50 2>/dev/null || echo "Sync module: analyze structure"

# CONTEXT OUTPUT: Migration patterns, schema evolution, data sync understanding
```

### **🔧 SCRIPTS CONTEXT (`scripts/`)**
```bash
# ROTEIRO: Scripts Context Extraction  
echo "🔧 SCRIPTS CONTEXT EXTRACTION"

# 1. Scripts Framework Overview
cat scripts/CLAUDE.md | grep -A 30 "Utility Scripts Architecture"
cat scripts/CLAUDE.md | grep -A 20 "Script Categories"

# 2. Maintenance Scripts Context
ls scripts/maintenance/*.py | head -10
echo "Key maintenance tools identified"

# 3. Analysis Scripts Context  
ls scripts/analysis/*.py | head -10
echo "Analysis tools inventory complete"

# 4. Testing Scripts Context
ls scripts/testing/*.py | head -15
echo "Testing utilities mapped"

# 5. Setup & Migration Scripts
ls scripts/setup/*.py | head -5
ls scripts/migration/*.py | head -5

# CONTEXT OUTPUT: Utility patterns, maintenance procedures, analysis capabilities
```

### **📊 MONITORING CONTEXT (`monitoring/`)**
```bash
# ROTEIRO: Monitoring Context Extraction
echo "📊 MONITORING CONTEXT EXTRACTION"

# 1. Monitoring Framework Overview
cat monitoring/CLAUDE.md 2>/dev/null | grep -A 25 "Observability Architecture" || echo "Monitoring docs: needs creation"

# 2. Monitoring Configuration
ls monitoring/*.yml 2>/dev/null | head -5 || echo "Monitoring configs: check structure"
ls monitoring/*.py 2>/dev/null | head -10 || echo "Monitoring scripts: inventory needed"

# CONTEXT OUTPUT: Observability patterns, monitoring setup, alerting configuration
```

### **⚙️ CONFIG CONTEXT (`config/`)**
```bash
# ROTEIRO: Configuration Context Extraction
echo "⚙️ CONFIG CONTEXT EXTRACTION"

# 1. Configuration Framework Overview
cat config/CLAUDE.md | grep -A 25 "Multi-Environment Architecture"
cat config/CLAUDE.md | grep -A 20 "Configuration Patterns"

# 2. Environment Configuration
ls config/environments/*.yaml 2>/dev/null | head -5 || echo "Environment configs: check structure"
cat config/environment.py | head -30 2>/dev/null || echo "Environment module: analyze structure"

# 3. Feature Flags & Settings
ls config/*.py | head -10

# CONTEXT OUTPUT: Configuration patterns, environment management, feature flag system
```

### **📚 DOCS CONTEXT (`docs/`)**
```bash
# ROTEIRO: Documentation Context Extraction
echo "📚 DOCS CONTEXT EXTRACTION"

# 1. Documentation Structure
ls docs/*/ | head -10
ls docs/*.md | head -15

# 2. Architecture Documentation
ls docs/architecture/*.md 2>/dev/null | head -5 || echo "Architecture docs: check availability"

# 3. Development Guides
ls docs/development/*.md 2>/dev/null | head -10 || echo "Development docs: inventory needed"

# 4. User Guides
ls docs/user*/*.md 2>/dev/null | head -5 || echo "User guides: check structure"

# CONTEXT OUTPUT: Documentation hierarchy, guide availability, knowledge structure
```

---

## 🔧 **INDEX.MD ENHANCEMENTS REQUIRED**

### **New Sections to Add**
```markdown
## 🗺️ **Context Extraction Routes**

### **📋 Context Roteiros by Folder**
| Folder | Context Roteiro | Key Documentation | Critical Files |
|--------|----------------|-------------------|----------------|
| `/` | `scripts/automated_audit/context_root.sh` | CLAUDE.md, STATUS.md, INDEX.md | *.db, pyproject.toml |
| `streamlit_extension/` | `scripts/automated_audit/context_streamlit.sh` | CLAUDE.md, services/, database/ | streamlit_app.py |
| `duration_system/` | `scripts/automated_audit/context_duration.sh` | CLAUDE.md | *calculator*.py, *security*.py |
| `tests/` | `scripts/automated_audit/context_tests.sh` | CLAUDE.md | conftest.py, test_*.py |
| `migration/` | `scripts/automated_audit/context_migration.sh` | CLAUDE.md | bidirectional_sync.py |
| `scripts/` | `scripts/automated_audit/context_scripts.sh` | CLAUDE.md | maintenance/, analysis/ |
| `monitoring/` | `scripts/automated_audit/context_monitoring.sh` | CLAUDE.md | *.yml, *.py |
| `config/` | `scripts/automated_audit/context_config.sh` | CLAUDE.md | environment.py |
| `docs/` | `scripts/automated_audit/context_docs.sh` | README.md | architecture/, development/ |

### **🧠 Context Cross-Reference Matrix**
| Context Type | Primary Source | Secondary Sources | Integration Points |
|--------------|----------------|-------------------|-------------------|
| **TDD Workflow** | streamlit_extension/services/CLAUDE.md | PROJECT_MISSION.md, TDD_WORKFLOW_PATTERNS.md | TaskService, EpicService |
| **TDAH Optimization** | streamlit_extension/components/CLAUDE.md | TDAH_OPTIMIZATION_GUIDE.md | TimerService, UI components |
| **Database Architecture** | streamlit_extension/database/CLAUDE.md | Hybrid architecture docs | connection.py, health.py |
| **Security Patterns** | duration_system/CLAUDE.md | Security documentation | *security*.py files |
| **Testing Framework** | tests/CLAUDE.md | Test documentation | conftest.py, test patterns |
```

---

## 📝 **NEW FILES REQUIRED FOR 100% FUNCTIONAL MAPPING**

### **1. Context Extraction Scripts** (`scripts/automated_audit/context_extractors/`)
```bash
# Create context extraction scripts for each folder
mkdir -p scripts/automated_audit/context_extractors/

# Individual context extractors (based on roteiros above)
touch scripts/automated_audit/context_extractors/context_root.sh
touch scripts/automated_audit/context_extractors/context_streamlit.sh  
touch scripts/automated_audit/context_extractors/context_duration.sh
touch scripts/automated_audit/context_extractors/context_tests.sh
touch scripts/automated_audit/context_extractors/context_migration.sh
touch scripts/automated_audit/context_extractors/context_scripts.sh
touch scripts/automated_audit/context_extractors/context_monitoring.sh
touch scripts/automated_audit/context_extractors/context_config.sh
touch scripts/automated_audit/context_extractors/context_docs.sh
```

### **2. Context Integration Map** (`scripts/automated_audit/CONTEXT_INTEGRATION_MAP.md`)
- Cross-reference matrix for all documentation
- Context dependency graph
- Integration points mapping
- Context precedence rules

### **3. Missing CLAUDE.md Files** (Remaining 4/9)
```bash
# Complete the TDD+TDAH context documentation
streamlit_extension/auth/CLAUDE.md         # Authentication with TDD session context
streamlit_extension/utils/CLAUDE.md        # Utilities with TDD/TDAH integration  
streamlit_extension/endpoints/CLAUDE.md    # API endpoints with health monitoring
streamlit_extension/models/CLAUDE.md       # Data models with TDD/TDAH structures
```

### **4. Advanced Context Files**
```bash
scripts/automated_audit/CONTEXT_VALIDATION_RULES.md    # Rules for context completeness
scripts/automated_audit/CONTEXT_DEPENDENCY_GRAPH.md    # Visual dependency mapping
scripts/automated_audit/CONTEXT_PRECEDENCE_MATRIX.md   # Priority rules for conflicting info
```

---

## 🎯 **INTEGRATION WITH SYSTEMATIC_FILE_AUDITOR.PY**

### **Enhanced Context Loading Method**
```python
def load_comprehensive_context(self, file_path: str) -> dict:
    """
    Load comprehensive context for file using roteiros and documentation
    """
    context = {}
    
    # 1. Determine folder context
    folder_type = self.determine_folder_type(file_path)
    
    # 2. Execute appropriate context roteiro
    context_script = f"scripts/automated_audit/context_extractors/context_{folder_type}.sh"
    context['folder_context'] = self.execute_context_roteiro(context_script)
    
    # 3. Load relevant CLAUDE.md documentation
    claude_docs = self.load_relevant_claude_docs(file_path)
    context['technical_context'] = claude_docs
    
    # 4. Load consultation documents
    consultation_docs = self.load_consultation_docs(folder_type)
    context['mission_context'] = consultation_docs
    
    # 5. Apply context integration rules
    context['integrated_context'] = self.integrate_context_sources(context)
    
    return context
```

---

## ✅ **IMPLEMENTATION PRIORITY**

### **Phase 1: Core Infrastructure** (IMMEDIATE)
1. ✅ Create context extraction roteiros (this document)
2. ✅ Enhance INDEX.md with context mapping sections
3. ✅ Create missing CLAUDE.md files (4 remaining)
4. ✅ Create context integration map

### **Phase 2: Script Implementation** (NEXT)
1. Create individual context extraction shell scripts
2. Implement context integration logic in systematic_file_auditor.py
3. Create context validation rules
4. Test end-to-end context extraction

### **Phase 3: Advanced Features** (LATER)
1. Context dependency graph visualization
2. Dynamic context precedence rules
3. Context completeness validation
4. Automated context update mechanisms

---

*Context extraction roteiros for 100% functional automated audit with complete contextual awareness*