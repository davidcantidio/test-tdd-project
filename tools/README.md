# 🔧 Tools - Maintenance and Utility Scripts

**Purpose:** Standalone utility scripts for system maintenance, cleanup, and validation.

## 📋 Contents

### **🧹 Cleanup Tools**
- `cleanup_cache.py` - Cache artifact cleanup utility
  ```bash
  # Preview cleanup (dry run)
  python tools/cleanup_cache.py --dry-run
  
  # Execute cleanup
  python tools/cleanup_cache.py
  ```

### **✅ Validation Tools**  
- `validate_gitignore.py` - Verify .gitignore patterns and repository health
  ```bash
  # Validate ignore patterns
  python tools/validate_gitignore.py
  ```

## 🚀 Quick Commands

### **System Maintenance**
```bash
# Full cache cleanup
python tools/cleanup_cache.py

# Repository health check
python tools/validate_gitignore.py

# Combined maintenance
python tools/cleanup_cache.py && python tools/validate_gitignore.py
```

## 🔧 Tool Features

### **cleanup_cache.py**
- **Safe Operation**: Dry-run preview before cleanup
- **Comprehensive**: Removes .streamlit/, __pycache__, .pytest_cache, temp files
- **Selective**: Preserves important cache files and databases
- **Logging**: Detailed output of cleanup actions

### **validate_gitignore.py**
- **Pattern Validation**: Ensures .gitignore patterns are effective
- **Repository Health**: Identifies tracked files that should be ignored
- **Performance Check**: Validates repository size and artifact control
- **Compliance**: Ensures enterprise repository standards

## 📊 Integration

These tools complement the main system utilities in:
- `scripts/maintenance/` - Advanced database and system maintenance
- `scripts/testing/` - Testing and validation utilities
- `monitoring/` - Health monitoring and alerts

**🎯 Purpose**: Provide quick, standalone utilities for common maintenance tasks without requiring the full framework setup.