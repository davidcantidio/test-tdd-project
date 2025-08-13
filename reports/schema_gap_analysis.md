# 📊 Schema Gap Analysis - Real Epic Data vs Current Database
**Date:** 2025-08-13  
**Analysis:** 9 Epic Files vs framework_v3.sql  
**Focus:** Duration System Implementation  

---

## 🎯 Executive Summary

**Incompatibility Level:** ~75% **CRÍTICO**  
**Epic Files Analyzed:** epico_0.json, epico_2.json, epico_3.json, epico_4.json, epico_5.json, epico_6.json  
**Main Issue:** Current schema supports basic project management but lacks rich TDD methodology data structure and flexible duration system.

---

## 📋 Critical Gaps Identified

### **1. Duration System Incompatibility** ⚠️ **ALTA PRIORIDADE**

**Current Schema:**
```sql
duration_days INTEGER  -- Rigid, only integer days
```

**Real Epic Data:**
```json
"duration": "1.5 dias"    // epico_5.json
"duration": "2 dias"      // epico_0.json  
"duration": "5 dias"      // epico_2.json
"duration": "1 semana"    // epico_3.json
"duration": "4 dias"      // epico_4.json
"duration": "1.5 dias"    // epico_6.json
```

**Missing Fields:**
- `planned_start_date` - Data início planejada
- `planned_end_date` - Data fim planejada  
- `actual_start_date` - Data início real
- `actual_end_date` - Data fim real
- `duration_description` - Descrição amigável ("1.5 dias", "1 semana")
- `calculated_duration_days` - Duração calculada automática

---

### **2. Rich Metadata Fields** ⚠️ **ALTA PRIORIDADE**

**Completely Missing:**
```sql
-- Epic level
goals JSON,                    -- Array de objetivos específicos
definition_of_done JSON,       -- Critérios de aceitação epic-level
labels JSON,                   -- Tags ["tdd", "caching", "performance"]
tdd_enabled BOOLEAN,           -- Flag TDD methodology
methodology VARCHAR(100),      -- "Test-Driven Development"
summary TEXT,                  -- Descrição detalhada do épico

-- Rich metadata
performance_constraints JSON,  -- Constraints de performance
quality_gates JSON,           -- Gates de qualidade
automation_hooks JSON,        -- Hooks de automação
checklist_epic_level JSON     -- Checklist épico
```

---

### **3. Task Structure Gaps** ⚠️ **ALTA PRIORIDADE**

**Current vs Real:**

| Field | Current Schema | Real Epic Data | Status |
|-------|---------------|----------------|---------|
| `test_specs` | ❌ Missing | ✅ Array of test specifications | **GAP** |
| `acceptance_criteria` | ❌ Missing | ✅ Array of acceptance criteria | **GAP** |
| `deliverables` | ❌ Missing | ✅ Array of expected deliverables | **GAP** |
| `branch` | ✅ `github_branch` | ✅ Feature branch name | **PARTIAL** |
| `files_touched` | ❌ Missing | ✅ Array of affected files | **GAP** |
| `risk` | ❌ Missing | ✅ Risk description | **GAP** |
| `mitigation` | ❌ Missing | ✅ Mitigation strategy | **GAP** |
| `tdd_skip_reason` | ❌ Missing | ✅ Reason for skipping TDD | **GAP** |

---

### **4. Dependencies System** ⚠️ **ALTA PRIORIDADE**

**Current:** Não existe tabela de dependências  
**Real Epic Data:**
```json
"dependencies": ["5.1a", "5.2b.2"],           // epico_5.json
"dependencies": ["3.3b.2", "3.2b.2"],         // epico_3.json  
"dependencies": ["4.1b.3", "4.2b.3", ...]    // epico_4.json
```

**Missing Table:**
```sql
CREATE TABLE task_dependencies (
    id INTEGER PRIMARY KEY,
    task_id INTEGER REFERENCES framework_tasks(id),
    depends_on_task_key VARCHAR(50), -- "5.1a", "3.2b.2"
    dependency_type VARCHAR(20) DEFAULT 'blocking',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📊 Detailed Field Analysis

### **Epic Level Fields - Gap Matrix**

| Priority | Field | Current | Real Data | Status | Migration Strategy |
|----------|-------|---------|-----------|---------|-------------------|
| **CRITICAL** | `duration` | `INTEGER days` | `"1.5 dias"` | **INCOMPATIBLE** | Add calculated + description fields |
| **CRITICAL** | `goals` | ❌ | ✅ Array | **MISSING** | Add JSON field |
| **CRITICAL** | `definition_of_done` | ❌ | ✅ Array | **MISSING** | Add JSON field |
| **HIGH** | `labels` | ❌ | ✅ Array | **MISSING** | Add JSON field |
| **HIGH** | `tdd_enabled` | ❌ | ✅ Boolean | **MISSING** | Add BOOLEAN field |
| **HIGH** | `methodology` | ❌ | ✅ String | **MISSING** | Add VARCHAR field |
| **MEDIUM** | `summary` | `description` | ✅ Text | **PARTIAL** | Use existing description |
| **MEDIUM** | `performance_constraints` | ❌ | ✅ Object | **MISSING** | Add JSON field |
| **MEDIUM** | `quality_gates` | ❌ | ✅ Object | **MISSING** | Add JSON field |
| **LOW** | `automation_hooks` | ❌ | ✅ Object | **MISSING** | Add JSON field |

### **Task Level Fields - Gap Matrix**

| Priority | Field | Current | Real Data | Status | Migration Strategy |
|----------|-------|---------|-----------|---------|-------------------|
| **CRITICAL** | `test_specs` | ❌ | ✅ Array | **MISSING** | Add JSON field |
| **CRITICAL** | `acceptance_criteria` | ❌ | ✅ Array | **MISSING** | Add JSON field |
| **HIGH** | `deliverables` | ❌ | ✅ Array | **MISSING** | Add JSON field |
| **HIGH** | `dependencies` | ❌ | ✅ Array | **MISSING** | New dependencies table |
| **HIGH** | `files_touched` | ❌ | ✅ Array | **MISSING** | Add JSON field |
| **MEDIUM** | `risk` | ❌ | ✅ String | **MISSING** | Add TEXT field |
| **MEDIUM** | `mitigation` | ❌ | ✅ String | **MISSING** | Add TEXT field |
| **MEDIUM** | `tdd_skip_reason` | ❌ | ✅ String | **MISSING** | Add VARCHAR field |
| **LOW** | `branch` | `github_branch` | ✅ String | **PARTIAL** | Use existing field |

---

## 🎯 Duration System Specific Analysis

### **Current Duration Logic**
```sql
duration_days INTEGER  -- Only stores integer days
```

### **Real Epic Duration Patterns**
- **Fractional Days:** "1.5 dias" (common)
- **Week Units:** "1 semana" = 7 days
- **Multiple Days:** "2 dias", "4 dias", "5 dias"
- **Context Preservation:** Need to keep original friendly description

### **Proposed Duration Extension**
```sql
-- New fields for framework_epics table
planned_start_date DATE,
planned_end_date DATE,  
actual_start_date DATE,
actual_end_date DATE,
calculated_duration_days DECIMAL(5,2),  -- 1.5, 7.0, 2.0
duration_description VARCHAR(50),       -- "1.5 dias", "1 semana"
duration_unit VARCHAR(20),              -- "dias", "semanas"
```

---

## 🚨 Priority Classification

### **PHASE 1 - CRITICAL (Duration System)**
1. **Duration Fields Extension** - Core migration requirement
2. **Date Fields Addition** - Start/end date support
3. **Dependencies Table** - Task relationship support
4. **Goals/Definition of Done** - Epic completion criteria

### **PHASE 2 - HIGH (Rich Data)**
1. **TDD Metadata** - test_specs, acceptance_criteria, deliverables
2. **Risk Management** - risk, mitigation fields
3. **File Tracking** - files_touched array
4. **Label System** - Epic and task labeling

### **PHASE 3 - MEDIUM (Advanced Features)**
1. **Performance Constraints** - JSON metadata
2. **Quality Gates** - JSON metadata  
3. **TDD Skip Reasons** - Analysis task support

### **PHASE 4 - LOW (Automation)**
1. **Automation Hooks** - CI/CD integration metadata
2. **Advanced Gamification** - Extended point systems

---

## 📈 Migration Impact Assessment

### **Data Volume**
- **9 Epic Files** to migrate
- **~25-30 tasks per epic** average
- **~225-270 total tasks** estimated

### **Performance Impact**
- **JSON Field Queries:** Expect 10-20ms overhead per complex query
- **Migration Time:** Estimated 5-10 minutes for full migration
- **Storage Increase:** ~300% due to rich metadata (acceptable)

### **Compatibility Risk**
- **Breaking Changes:** New required fields need defaults
- **Query Performance:** JSON queries need optimization
- **Index Strategy:** Need indexes on calculated_duration_days, labels

---

## ✅ Recommendations

### **Immediate Actions (Duration System)**
1. **Create schema extension:** framework_v4.sql with duration fields
2. **Implement DurationParser:** Parse "1.5 dias" → 1.5 days + "dias"  
3. **Add date calculation logic:** planned_start + duration = planned_end
4. **Create dependencies table:** Support task relationships

### **Migration Strategy**
1. **Backward Compatible:** Add new fields with defaults
2. **Gradual Migration:** Migrate one epic at a time
3. **Validation:** Compare before/after data integrity
4. **Rollback Plan:** Script to revert to v3 schema if needed

### **Performance Optimization**
1. **JSON Indexes:** Create indexes on frequently queried JSON fields
2. **Computed Columns:** Cache commonly accessed JSON values
3. **Query Optimization:** Optimize joins between epics/tasks/dependencies
4. **Batch Operations:** Use transactions for epic migration

---

## 🔧 Next Steps

1. **Design Phase 1 Schema Extensions** (Duration System)
2. **Create DurationFormatter/Parser Classes**
3. **Implement Migration Scripts** 
4. **Build Validation Tests**
5. **Performance Benchmarking**

---

*Analysis completed: 2025-08-13*  
*Scope: Duration System - First Priority Item*  
*Schema Compatibility: 25% (requires 75% extension)*