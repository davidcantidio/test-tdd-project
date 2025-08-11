# 🚨 Standardized Error Handling Guide

## 📋 Overview

The TDD project template uses a centralized error handling system for consistent error management, logging, and user feedback across all components.

## 🏗️ Architecture

### **Core Components**
- **`tdah_tools/error_handler.py`** - Central error handling system
- **Custom Exception Hierarchy** - Structured exception classes
- **Structured Logging** - Consistent log formatting
- **Error Analytics** - Error tracking and reporting

## 🔧 Usage Patterns

### **1. Import Error Handler**
```python
from tdah_tools.error_handler import (
    get_error_handler, handle_error, log_info, log_warning, log_error,
    ValidationError, ConfigurationError, DependencyError, ErrorSeverity
)
```

### **2. Basic Error Handling**
```python
try:
    # Some operation that might fail
    result = risky_operation()
except Exception as e:
    error_report = handle_error(
        exception=e,
        user_action="Check configuration and try again",
        context={"operation": "risky_operation", "param": value}
    )
    print(f"❌ {error_report.message}")
    return False
```

### **3. Specific Exception Types**
```python
try:
    validate_config(config_path)
except FileNotFoundError:
    raise ConfigurationError(
        "Configuration file not found",
        user_action="Create config file using template",
        context={"config_path": str(config_path)}
    )
```

### **4. Structured Logging**
```python
# Info logging
log_info("Setup completed successfully", {"duration": 120, "components": 5})

# Warning logging  
log_warning("Optional dependency missing", {"dependency": "plotly", "fallback": "basic_mode"})

# Error logging
log_error("Process failed", {"command": "poetry install", "exit_code": 1})
```

### **5. Decorator for Automatic Handling**
```python
@with_error_handling(user_action="Check input parameters")
def process_data(data_path: Path) -> Dict:
    # Function implementation
    # Exceptions automatically handled and logged
    pass
```

## 📊 Exception Categories

### **Available Categories**
- `VALIDATION` - Input/environment validation errors
- `CONFIGURATION` - Configuration-related errors
- `DEPENDENCY` - Missing or incompatible dependencies
- `FILE_SYSTEM` - File system operations
- `NETWORK` - Network connectivity issues
- `PROCESS` - External process execution
- `USER_INPUT` - User input validation
- `ANALYTICS` - Data processing and analytics
- `TEMPLATE` - Template processing errors
- `GIT` - Git operations
- `GITHUB` - GitHub API integration

### **Custom Exception Classes**
```python
# For validation errors
raise ValidationError("Invalid project structure", 
                     user_action="Run setup wizard to fix")

# For missing dependencies
raise DependencyError("Poetry not found",
                     user_action="Install Poetry: https://python-poetry.org")

# For process failures
raise ProcessError("Git command failed",
                  user_action="Check Git installation and permissions")
```

## 📝 Error Severity Levels

### **Severity Guidelines**
- `DEBUG` - Development information, trace data
- `INFO` - Normal operation messages
- `WARNING` - Non-critical issues, degraded functionality
- `ERROR` - Operation failures, user intervention needed
- `CRITICAL` - System failures, immediate attention required

### **Usage Examples**
```python
# Debug information
handle_error(exception, severity=ErrorSeverity.DEBUG)

# Non-critical warnings
handle_error(exception, severity=ErrorSeverity.WARNING, 
            user_action="Feature will work with reduced functionality")

# Critical failures
handle_error(exception, severity=ErrorSeverity.CRITICAL,
            user_action="Contact support immediately")
```

## 🔍 Error Context

### **Best Practices for Context**
```python
context = {
    "function": "setup_python_environment",
    "project_root": str(project_path),
    "python_version": "3.11",
    "use_poetry": True,
    "step": "dependency_installation"
}

handle_error(exception, context=context, user_action="Check Python setup")
```

### **Context Guidelines**
- Include relevant parameters and state
- Add operation being performed
- Include file paths when applicable
- Add step/phase information for multi-step processes

## 📈 Error Analytics

### **Error Report Export**
```python
# Get error handler instance
handler = get_error_handler()

# Export analytics report
handler.export_error_report(Path("error_analytics.json"))

# Get summary for display
summary = handler.get_error_summary()
print(f"Total errors: {summary['total']}")
```

### **Error Report Structure**
```json
{
  "generated_at": "2025-01-09T10:30:00",
  "total_errors": 15,
  "by_category": {
    "dependency": 8,
    "process": 4,
    "validation": 3
  },
  "by_severity": {
    "warning": 10,
    "error": 4,
    "critical": 1
  },
  "errors": [
    {
      "timestamp": "2025-01-09T10:25:00",
      "severity": "error",
      "category": "dependency",
      "message": "Poetry not found",
      "user_action": "Install Poetry",
      "context": {"command": "poetry --version"}
    }
  ]
}
```

## 🛠️ Configuration

### **Error Handler Setup**
```python
# Development mode with full stack traces
handler = TDDErrorHandler(
    log_file=Path("logs/tdd_errors.log"),
    development_mode=True,
    console_level="DEBUG",
    file_level="DEBUG"
)

# Production mode
handler = TDDErrorHandler(
    log_file=Path("logs/tdd_errors.log"),
    development_mode=False,
    console_level="INFO", 
    file_level="WARNING"
)
```

### **Global Handler Access**
```python
# Get or create global handler
handler = get_error_handler(
    log_file=Path("custom_errors.log"),
    development_mode=True
)
```

## 🎯 Integration Examples

### **Setup Wizard Integration**
```python
class TDDProjectWizard:
    def __init__(self):
        # Initialize error handler for wizard
        self.error_handler = get_error_handler(
            log_file=Path("setup_errors.log"),
            development_mode=False
        )
    
    def run(self) -> bool:
        try:
            self._collect_project_info()
            self._setup_environment()
            return True
        except Exception as e:
            error_report = handle_error(
                exception=e,
                user_action="Check setup requirements and run again",
                context={"wizard_step": "main_execution"}
            )
            console.print(f"❌ Setup failed: {error_report.message}")
            return False
```

### **Analytics Integration**
```python
class TDDAHAnalytics:
    def load_session_data(self, days: int = 30) -> Any:
        try:
            # Data loading logic
            return data
        except sqlite3.OperationalError as e:
            raise AnalyticsError(
                "Database access failed",
                user_action="Check database file permissions and path", 
                context={"db_path": str(self.db_path), "days": days}
            )
```

## 🎨 User-Friendly Messages

### **Message Format Guidelines**
- Use emojis for visual clarity: 📦 🌐 ⚙️ 📁
- Provide specific, actionable guidance
- Include relevant context without technical jargon
- Suggest next steps for resolution

### **Good Message Examples**
```python
"📦 Missing dependency: Poetry not found"
"🌐 Network error: GitHub API unavailable" 
"⚙️ Configuration error: Invalid project type specified"
"📁 File system error: Unable to create project directory"
```

### **User Action Guidelines**
```python
# Specific and actionable
user_action="Install Poetry: https://python-poetry.org/docs/#installation"

# Include commands when helpful
user_action="Run: gh auth login to authenticate GitHub CLI"

# Reference documentation
user_action="Check troubleshooting guide: docs/TROUBLESHOOTING.md"
```

## 🔄 Migration Guide

### **Converting Existing Code**

**Before (inconsistent):**
```python
try:
    subprocess.run(["poetry", "install"], check=True)
except subprocess.CalledProcessError:
    print("Poetry installation failed")
    return False
```

**After (standardized):**
```python
try:
    subprocess.run(["poetry", "install"], check=True)
except subprocess.CalledProcessError as e:
    handle_error(
        ProcessError("Poetry installation failed",
                   user_action="Install Poetry: https://python-poetry.org"),
        context={"command": "poetry install", "cwd": str(project_root)}
    )
    return False
```

### **Step-by-Step Migration**
1. **Import error handler** at module level
2. **Replace generic exceptions** with specific error types  
3. **Add structured context** to error handling
4. **Include user actions** for resolution guidance
5. **Use structured logging** instead of print statements
6. **Test error scenarios** to verify consistent behavior

## 📊 Monitoring & Debugging

### **Log Analysis**
```bash
# View recent errors
tail -f logs/tdd_errors.log | grep ERROR

# Filter by category
grep "DEPENDENCY" logs/tdd_errors.log

# Count errors by type
grep -c "ProcessError" logs/tdd_errors.log
```

### **Error Dashboard Integration**
The error analytics can be integrated with monitoring dashboards to track:
- Error frequency trends
- Most common error categories  
- User action effectiveness
- System reliability metrics

---

**Last updated:** 2025-01-09  
**Status:** Implemented across core components  
**Next steps:** Expand to all template modules, add dashboard integration