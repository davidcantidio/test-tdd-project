"""
🔍 Configuration and Data Validators

Validation utilities for Streamlit extension with:
- Configuration validation
- Database schema validation
- Input sanitization
- Error reporting
- Project data validation
"""

from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import re
import json
from datetime import datetime
from email.utils import parseaddr

VALID_METHODS = {"agile", "waterfall", "kanban", "scrum", "lean", "hybrid"}

# Graceful imports
try:
    from ..config import StreamlitConfig
except ImportError:
    StreamlitConfig = None


class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Refactored method with extracted responsibilities."""
    validate_config_business_logic()
    validate_config_ui_interaction()
    validate_config_validation()
    validate_config_error_handling()
    validate_config_configuration()
    validate_config_networking()
    validate_config_formatting()
    validate_config_caching()
    pass  # TODO: Integrate extracted method results # Tracked: 2025-08-21


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




def validate_project_data(project: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    📁 Validate project data structure and business rules.
    
    Args:
        project: Project dictionary to validate
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    required_fields = ["project_key", "name", "status", "planned_start_date", "planned_end_date"]
    for field in required_fields:
        if field not in project or project[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate project_key format
    project_key = project.get("project_key", "")
    if project_key:
        if not re.match(r'^[a-z0-9_]{2,50}$', project_key):
            errors.append("Project key must be lowercase, contain only letters, numbers, underscores (2-50 chars)")
    
    # Validate name length
    name = project.get("name", "")
    if len(name) > 255:
        errors.append(f"Project name too long ({len(name)} characters, max 255)")
    if len(name.strip()) == 0:
        errors.append("Project name cannot be empty")
    
    # Validate status
    valid_statuses = ["planning", "in_progress", "completed", "on_hold", "cancelled"]
    status = project.get("status", "").lower()
    if status and status not in valid_statuses:
        errors.append(f"Invalid status '{status}'. Valid options: {', '.join(valid_statuses)}")
    
    # Validate project type
    valid_types = ["development", "maintenance", "consulting", "research", "support"]
    project_type = project.get("project_type", "development")
    if project_type and project_type not in valid_types:
        errors.append(f"Invalid project type '{project_type}'. Valid options: {', '.join(valid_types)}")
    
    # Validate methodology
    valid_methodologies = list(VALID_METHODS)
    methodology = project.get("methodology", "agile")
    if methodology and methodology not in valid_methodologies:
        errors.append(f"Invalid methodology '{methodology}'. Valid options: {', '.join(valid_methodologies)}")
    
    # Validate dates
    try:
        planned_start = project.get("planned_start_date")
        planned_end = project.get("planned_end_date")
        
        if planned_start and planned_end:
            # Convert to datetime if they're strings
            if isinstance(planned_start, str):
                try:
                    planned_start = datetime.fromisoformat(planned_start.replace('Z', '+00:00'))
                except ValueError:
                    errors.append(f"Invalid planned start date format: {planned_start}")
                    planned_start = None
            
            if isinstance(planned_end, str):
                try:
                    planned_end = datetime.fromisoformat(planned_end.replace('Z', '+00:00'))
                except ValueError:
                    errors.append(f"Invalid planned end date format: {planned_end}")
                    planned_end = None
            
            # Check date logic
            if planned_start and planned_end:
                if planned_end <= planned_start:
                    errors.append("Planned end date must be after planned start date")
    except Exception as e:
        errors.append(f"Error validating dates: {str(e)}")
    
    # Validate priority
    priority = project.get("priority")
    if priority is not None:
        try:
            priority_int = int(priority)
            if priority_int < 1 or priority_int > 10:
                errors.append(f"Priority {priority_int} outside valid range (1-10)")
        except (ValueError, TypeError):
            errors.append(f"Invalid priority value: {priority}")
    
    # Validate health status
    valid_health = ["green", "yellow", "red"]
    health = project.get("health_status", "green")
    if health and health not in valid_health:
        errors.append(f"Invalid health status '{health}'. Valid options: {', '.join(valid_health)}")
    
    # Validate budget amount
    budget = project.get("budget_amount")
    if budget is not None:
        try:
            budget_float = float(budget)
            if budget_float < 0:
                errors.append("Budget amount cannot be negative")
            if budget_float > 10000000:  # 10M limit
                errors.append(f"Budget amount {budget_float} seems unreasonably high")
        except (ValueError, TypeError):
            errors.append(f"Invalid budget amount value: {budget}")
    
    # Validate estimated hours
    estimated_hours = project.get("estimated_hours")
    if estimated_hours is not None:
        try:
            hours_float = float(estimated_hours)
            if hours_float < 0:
                errors.append("Estimated hours cannot be negative")
            if hours_float > 10000:  # 10k hours limit
                errors.append(f"Estimated hours {hours_float} seems unreasonably high")
        except (ValueError, TypeError):
            errors.append(f"Invalid estimated hours value: {estimated_hours}")
    
    # Validate completion percentage
    completion = project.get("completion_percentage")
    if completion is not None:
        try:
            completion_float = float(completion)
            if completion_float < 0 or completion_float > 100:
                errors.append(f"Completion percentage {completion_float} outside valid range (0-100)")
        except (ValueError, TypeError):
            errors.append(f"Invalid completion percentage value: {completion}")
    
    return len(errors) == 0, errors




def validate_project_key_uniqueness(project_key: str, existing_projects: List[Dict[str, Any]], exclude_project_id: Optional[int] = None) -> bool:
    """
    🔑 Check if project key is unique across all projects.
    
    Args:
        project_key: Project key to check
        existing_projects: List of existing project dictionaries
        exclude_project_id: Project ID to exclude from check (for updates)
    
    Returns:
        True if project key is unique, False otherwise
    """
    if not project_key:
        return True
    
    for project in existing_projects:
        if exclude_project_id and project.get("id") == exclude_project_id:
            continue

        if project.get("project_key", "").lower() == project_key.lower():
            return False

    return True


def is_valid_email(email: str) -> bool:
    """Loose e-mail validation without regex pitfalls."""
    if not email:
        return False
    _, addr = parseaddr(email)
    return "@" in addr and "." in addr.split("@")[-1]

