"""
🔍 Configuration and Data Validators

Validation utilities for Streamlit extension with:
- Configuration validation
- Database schema validation
- Input sanitization
- Error reporting
"""

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import re
import json

# Graceful imports
try:
    from ..config import StreamlitConfig
except ImportError:
    StreamlitConfig = None


class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Validate required fields
    required_fields = [
        "streamlit_port",
        "database_url",
        "timezone"
    ]
    
    for field in required_fields:
        if field not in config or config[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate port range
    port = config.get("streamlit_port")
    if port is not None:
        try:
            port_int = int(port)
            if not (1024 <= port_int <= 65535):
                errors.append(f"Port {port_int} outside valid range (1024-65535)")
        except (ValueError, TypeError):
            errors.append(f"Invalid port value: {port}")
    
    # Validate session durations
    duration_fields = [
        ("focus_session_duration", 5, 120),
        ("short_break_duration", 1, 30),
        ("long_break_duration", 5, 60)
    ]
    
    for field, min_val, max_val in duration_fields:
        duration = config.get(field)
        if duration is not None:
            try:
                duration_int = int(duration)
                if not (min_val <= duration_int <= max_val):
                    errors.append(f"{field} {duration_int} outside valid range ({min_val}-{max_val} minutes)")
            except (ValueError, TypeError):
                errors.append(f"Invalid {field} value: {duration}")
    
    # Validate database URLs
    database_fields = ["database_url", "timer_database_url", "test_database_url"]
    for field in database_fields:
        db_url = config.get(field)
        if db_url and not (db_url.startswith("sqlite:///") or db_url.startswith("postgresql://") or db_url.startswith("mysql://")):
            errors.append(f"Unsupported database URL format in {field}: {db_url}")
    
    # Validate timezone
    timezone = config.get("timezone")
    if timezone:
        try:
            import pytz
            pytz.timezone(timezone)
        except ImportError:
            # pytz not available - skip validation
            pass
        except Exception:
            errors.append(f"Invalid timezone: {timezone}")
    
    # Validate GitHub configuration consistency
    github_fields = ["github_token", "github_repo_owner", "github_repo_name"]
    github_values = [config.get(field) for field in github_fields]
    
    if any(github_values) and not all(github_values):
        missing_github = [field for field, value in zip(github_fields, github_values) if not value]
        errors.append(f"Incomplete GitHub configuration. Missing: {', '.join(missing_github)}")
    
    # Validate numeric ranges
    numeric_validations = [
        ("analytics_retention_days", 1, 365),
        ("cache_ttl_seconds", 60, 3600),
        ("session_timeout", 30, 1440),
        ("github_api_calls_per_hour", 100, 5000),
        ("rate_limit_buffer", 10, 1000)
    ]
    
    for field, min_val, max_val in numeric_validations:
        value = config.get(field)
        if value is not None:
            try:
                value_int = int(value)
                if not (min_val <= value_int <= max_val):
                    errors.append(f"{field} {value_int} outside valid range ({min_val}-{max_val})")
            except (ValueError, TypeError):
                errors.append(f"Invalid {field} value: {value}")
    
    return len(errors) == 0, errors


def validate_streamlit_config(config: 'StreamlitConfig') -> Tuple[bool, List[str]]:
    """
    Validate StreamlitConfig object.
    
    Args:
        config: StreamlitConfig instance
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    if not StreamlitConfig:
        return False, ["StreamlitConfig class not available"]
    
    return validate_config(config.to_dict())


def validate_database_paths(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate database file paths exist and are accessible.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    warnings = []
    
    # Extract database paths from URLs
    db_configs = [
        ("database_url", "Framework database"),
        ("timer_database_url", "Timer database")
    ]
    
    for url_field, description in db_configs:
        db_url = config.get(url_field)
        if db_url and db_url.startswith("sqlite:///"):
            db_path = Path(db_url.replace("sqlite:///", ""))
            
            if not db_path.exists():
                warnings.append(f"{description} not found at {db_path}")
            elif not db_path.is_file():
                errors.append(f"{description} path is not a file: {db_path}")
            else:
                # Check if file is readable
                try:
                    with open(db_path, 'r'):
                        pass
                except PermissionError:
                    errors.append(f"{description} is not readable: {db_path}")
                except Exception as e:
                    errors.append(f"Error accessing {description}: {e}")
    
    # Return warnings as part of error list (they're not critical)
    return len(errors) == 0, errors + warnings


def validate_github_token(token: str) -> Tuple[bool, List[str]]:
    """
    Validate GitHub token format.
    
    Args:
        token: GitHub personal access token
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not token:
        errors.append("GitHub token is empty")
        return False, errors
    
    # Check token format
    if not token.startswith(("ghp_", "github_pat_")):
        errors.append("GitHub token format appears invalid (should start with ghp_ or github_pat_)")
    
    # Check length (GitHub tokens are typically 40+ characters)
    if len(token) < 40:
        errors.append(f"GitHub token appears too short ({len(token)} characters)")
    
    # Check for suspicious patterns
    if token.count("*") > len(token) * 0.5:
        errors.append("GitHub token appears to be masked/redacted")
    
    return len(errors) == 0, errors


def validate_task_data(task: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate task data structure.
    
    Args:
        task: Task dictionary
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    required_fields = ["title", "epic_id"]
    for field in required_fields:
        if field not in task or not task[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate title
    title = task.get("title", "")
    if len(title) > 255:
        errors.append(f"Task title too long ({len(title)} characters, max 255)")
    if len(title.strip()) == 0:
        errors.append("Task title cannot be empty")
    
    # Validate status
    valid_statuses = ["todo", "in_progress", "completed", "cancelled"]
    status = task.get("status", "").lower()
    if status and status not in valid_statuses:
        errors.append(f"Invalid status '{status}'. Valid options: {', '.join(valid_statuses)}")
    
    # Validate TDD phase
    valid_tdd_phases = ["red", "green", "refactor", None]
    tdd_phase = task.get("tdd_phase")
    if tdd_phase and tdd_phase not in valid_tdd_phases:
        errors.append(f"Invalid TDD phase '{tdd_phase}'. Valid options: {', '.join(str(p) for p in valid_tdd_phases if p)}")
    
    # Validate estimate
    estimate = task.get("estimate_minutes")
    if estimate is not None:
        try:
            estimate_int = int(estimate)
            if estimate_int < 1 or estimate_int > 480:  # 8 hours max
                errors.append(f"Estimate {estimate_int} minutes outside valid range (1-480)")
        except (ValueError, TypeError):
            errors.append(f"Invalid estimate value: {estimate}")
    
    # Validate priority
    priority = task.get("priority")
    if priority is not None:
        try:
            priority_int = int(priority)
            if priority_int < 1 or priority_int > 5:
                errors.append(f"Priority {priority_int} outside valid range (1-5)")
        except (ValueError, TypeError):
            errors.append(f"Invalid priority value: {priority}")
    
    return len(errors) == 0, errors


def validate_epic_data(epic: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate epic data structure.
    
    Args:
        epic: Epic dictionary
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    required_fields = ["name", "epic_key"]
    for field in required_fields:
        if field not in epic or not epic[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate name
    name = epic.get("name", "")
    if len(name) > 255:
        errors.append(f"Epic name too long ({len(name)} characters, max 255)")
    if len(name.strip()) == 0:
        errors.append("Epic name cannot be empty")
    
    # Validate epic_key format
    epic_key = epic.get("epic_key", "")
    if epic_key:
        if not re.match(r'^[A-Z][A-Z0-9_]{2,49}$', epic_key):
            errors.append("Epic key must be uppercase, start with letter, contain only letters, numbers, underscores (3-50 chars)")
    
    # Validate status
    valid_statuses = ["planning", "in_progress", "completed", "on_hold", "cancelled"]
    status = epic.get("status", "").lower()
    if status and status not in valid_statuses:
        errors.append(f"Invalid status '{status}'. Valid options: {', '.join(valid_statuses)}")
    
    # Validate difficulty level
    valid_difficulties = ["trivial", "easy", "medium", "hard", "epic"]
    difficulty = epic.get("difficulty_level", "").lower()
    if difficulty and difficulty not in valid_difficulties:
        errors.append(f"Invalid difficulty '{difficulty}'. Valid options: {', '.join(valid_difficulties)}")
    
    return len(errors) == 0, errors


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input text.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Remove or replace dangerous characters
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    # Strip whitespace
    text = text.strip()
    
    return text


def validate_json_structure(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate JSON data against a simple schema.
    
    Args:
        data: Data to validate
        schema: Schema definition
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    def validate_field(field_name: str, field_value: Any, field_schema: Any, path: str = ""):
        current_path = f"{path}.{field_name}" if path else field_name
        
        if isinstance(field_schema, dict):
            if "type" in field_schema:
                expected_type = field_schema["type"]
                if expected_type == "string" and not isinstance(field_value, str):
                    errors.append(f"{current_path}: Expected string, got {type(field_value).__name__}")
                elif expected_type == "number" and not isinstance(field_value, (int, float)):
                    errors.append(f"{current_path}: Expected number, got {type(field_value).__name__}")
                elif expected_type == "boolean" and not isinstance(field_value, bool):
                    errors.append(f"{current_path}: Expected boolean, got {type(field_value).__name__}")
                elif expected_type == "array" and not isinstance(field_value, list):
                    errors.append(f"{current_path}: Expected array, got {type(field_value).__name__}")
                elif expected_type == "object" and not isinstance(field_value, dict):
                    errors.append(f"{current_path}: Expected object, got {type(field_value).__name__}")
            
            if "required" in field_schema and field_schema["required"]:
                if field_value is None or field_value == "":
                    errors.append(f"{current_path}: Required field is missing or empty")
            
            if "min_length" in field_schema and isinstance(field_value, str):
                if len(field_value) < field_schema["min_length"]:
                    errors.append(f"{current_path}: String too short (min {field_schema['min_length']} chars)")
            
            if "max_length" in field_schema and isinstance(field_value, str):
                if len(field_value) > field_schema["max_length"]:
                    errors.append(f"{current_path}: String too long (max {field_schema['max_length']} chars)")
    
    # Validate required top-level fields
    if "required" in schema:
        for required_field in schema["required"]:
            if required_field not in data:
                errors.append(f"Missing required field: {required_field}")
    
    # Validate each field
    if "properties" in schema:
        for field_name, field_schema in schema["properties"].items():
            if field_name in data:
                validate_field(field_name, data[field_name], field_schema)
    
    return len(errors) == 0, errors


def generate_validation_report(validations: List[Tuple[str, bool, List[str]]]) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report.
    
    Args:
        validations: List of (name, is_valid, errors) tuples
    
    Returns:
        Validation report dictionary
    """
    total_checks = len(validations)
    passed_checks = sum(1 for _, is_valid, _ in validations if is_valid)
    
    report = {
        "timestamp": "2025-08-12T10:00:00",  # Would use actual timestamp
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "success_rate": (passed_checks / total_checks * 100) if total_checks > 0 else 0,
        "status": "PASS" if passed_checks == total_checks else "FAIL",
        "details": []
    }
    
    for name, is_valid, errors in validations:
        report["details"].append({
            "check": name,
            "status": "PASS" if is_valid else "FAIL",
            "errors": errors
        })
    
    return report