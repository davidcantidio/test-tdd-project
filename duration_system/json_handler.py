"""
JSON Fields Handler for Duration System

Handles serialization, deserialization, and validation of JSON fields
for epic data structures including goals, definition_of_done, and labels.

Focus: FASE 3.1 - JSON Fields Handler
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class JsonFieldType(Enum):
    """Supported JSON field types in epic data"""
    GOALS = "goals"                    # List of goal strings
    DEFINITION_OF_DONE = "definition_of_done"  # List of completion criteria
    LABELS = "labels"                  # List of tag strings
    METADATA = "metadata"              # Generic metadata object
    TASK_SPECS = "task_specs"          # Task specification objects
    ACCEPTANCE_CRITERIA = "acceptance_criteria"  # Acceptance criteria objects


class JsonValidationError(Exception):
    """Custom exception for JSON validation errors"""
    pass


class JsonFieldHandler:
    """
    Core handler for JSON field operations in epic data.
    
    Provides:
    - Safe serialization/deserialization
    - Schema validation for epic JSON structures
    - Query-optimized JSON handling
    - Compatibility with real epic data formats
    """
    
    def __init__(self, strict_validation: bool = True, max_field_size: int = 10000):
        """
        Initialize JSON field handler.
        
        Args:
            strict_validation: Whether to enforce strict validation rules
            max_field_size: Maximum size in characters for JSON fields
        """
        self.strict_validation = strict_validation
        self.max_field_size = max_field_size
        
        # Define expected schemas for different field types
        self._field_schemas = {
            JsonFieldType.GOALS: {
                "type": "list",
                "items": {"type": "string", "min_length": 5, "max_length": 500},
                "min_items": 1,
                "max_items": 20
            },
            JsonFieldType.DEFINITION_OF_DONE: {
                "type": "list",
                "items": {"type": "string", "min_length": 10, "max_length": 1000},
                "min_items": 1,
                "max_items": 30
            },
            JsonFieldType.LABELS: {
                "type": "list",
                "items": {"type": "string", "pattern": "^[a-z0-9-_]+$", "max_length": 50},
                "min_items": 1,
                "max_items": 20
            },
            JsonFieldType.METADATA: {
                "type": "object",
                "properties": {
                    "created_by": {"type": "string"},
                    "created_at": {"type": "string"},
                    "tags": {"type": "object"},
                    "priority_level": {"type": "integer", "min": 1, "max": 5}
                }
            }
        }
    
    def serialize_field(self, data: Any, field_type: JsonFieldType) -> str:
        """
        Serialize data to JSON string with validation.
        
        Args:
            data: Data to serialize
            field_type: Type of field for validation
            
        Returns:
            JSON string representation
            
        Raises:
            JsonValidationError: If validation fails
        """
        if data is None:
            return "{}"
        
        try:
            # Validate data structure before serialization
            if self.strict_validation:
                self._validate_structure(data, field_type)
            
            # Serialize with consistent formatting
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
            
            # Check size limits
            if len(json_str) > self.max_field_size:
                raise JsonValidationError(
                    f"JSON field too large: {len(json_str)} chars (max {self.max_field_size})"
                )
            
            return json_str
            
        except (TypeError, ValueError) as e:
            raise JsonValidationError(f"Failed to serialize JSON: {e}")
        except Exception as e:
            raise JsonValidationError(f"Serialization error: {e}")
    
    def deserialize_field(self, json_str: str, field_type: JsonFieldType, 
                         default: Any = None) -> Any:
        """
        Deserialize JSON string with validation.
        
        Args:
            json_str: JSON string to deserialize
            field_type: Expected field type for validation
            default: Default value if deserialization fails
            
        Returns:
            Deserialized data structure
        """
        if not json_str or json_str.strip() in ['', '{}', '[]', 'null']:
            return default or self._get_default_value(field_type)
        
        try:
            data = json.loads(json_str)
            
            # Validate deserialized structure
            if self.strict_validation:
                self._validate_structure(data, field_type)
            
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to deserialize JSON: {e}")
            if self.strict_validation:
                raise JsonValidationError(f"Invalid JSON format: {e}")
            return default or self._get_default_value(field_type)
        except JsonValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.warning(f"Unexpected deserialization error: {e}")
            return default or self._get_default_value(field_type)
    
    def validate_epic_json_fields(self, epic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all JSON fields in an epic data structure.
        
        Args:
            epic_data: Epic data dictionary from JSON file
            
        Returns:
            Validation result with errors and warnings
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "validated_fields": {}
        }
        
        try:
            # Extract epic section
            epic = epic_data.get("epic", {})
            
            # Validate goals
            if "goals" in epic:
                try:
                    goals = epic["goals"]
                    if isinstance(goals, list):
                        self._validate_structure(goals, JsonFieldType.GOALS)
                        result["validated_fields"]["goals"] = len(goals)
                    else:
                        result["errors"].append("Goals field is not a list")
                        result["is_valid"] = False
                except JsonValidationError as e:
                    result["warnings"].append(f"Goals validation: {e}")
            
            # Validate definition_of_done
            if "definition_of_done" in epic:
                try:
                    dod = epic["definition_of_done"]
                    if isinstance(dod, list):
                        self._validate_structure(dod, JsonFieldType.DEFINITION_OF_DONE)
                        result["validated_fields"]["definition_of_done"] = len(dod)
                    else:
                        result["errors"].append("Definition_of_done field is not a list")
                        result["is_valid"] = False
                except JsonValidationError as e:
                    result["warnings"].append(f"Definition_of_done validation: {e}")
            
            # Validate labels
            if "labels" in epic:
                try:
                    labels = epic["labels"]
                    if isinstance(labels, list):
                        self._validate_structure(labels, JsonFieldType.LABELS)
                        result["validated_fields"]["labels"] = len(labels)
                    else:
                        result["errors"].append("Labels field is not a list")
                        result["is_valid"] = False
                except JsonValidationError as e:
                    result["warnings"].append(f"Labels validation: {e}")
            
            # Validate tasks if present
            if "tasks" in epic_data:
                task_count = len(epic_data["tasks"])
                result["validated_fields"]["tasks"] = task_count
                
                # Validate task structures
                for i, task in enumerate(epic_data["tasks"]):
                    if "test_specs" in task:
                        try:
                            self._validate_task_test_specs(task["test_specs"])
                        except JsonValidationError as e:
                            result["warnings"].append(f"Task {i+1} test_specs: {e}")
            
        except Exception as e:
            result["errors"].append(f"Epic validation error: {e}")
            result["is_valid"] = False
        
        return result
    
    def extract_searchable_text(self, json_data: Dict[str, Any]) -> List[str]:
        """
        Extract searchable text from JSON structures for indexing.
        
        Args:
            json_data: JSON data structure
            
        Returns:
            List of searchable text strings
        """
        searchable_texts = []
        
        def extract_strings(obj: Any, prefix: str = ""):
            """Recursively extract strings from nested structures"""
            if isinstance(obj, str):
                if len(obj.strip()) > 2:  # Skip very short strings
                    searchable_texts.append(f"{prefix}:{obj}" if prefix else obj)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_strings(item, f"{prefix}[{i}]" if prefix else f"item_{i}")
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    extract_strings(value, new_prefix)
        
        extract_strings(json_data)
        return searchable_texts
    
    def merge_json_fields(self, field1: str, field2: str, 
                         field_type: JsonFieldType) -> str:
        """
        Merge two JSON fields of the same type.
        
        Args:
            field1: First JSON field string
            field2: Second JSON field string
            field_type: Type of fields being merged
            
        Returns:
            Merged JSON string
        """
        try:
            data1 = self.deserialize_field(field1, field_type, default=[])
            data2 = self.deserialize_field(field2, field_type, default=[])
            
            if field_type in [JsonFieldType.GOALS, JsonFieldType.DEFINITION_OF_DONE, 
                             JsonFieldType.LABELS]:
                # For list types, merge and deduplicate
                if isinstance(data1, list) and isinstance(data2, list):
                    merged = list(dict.fromkeys(data1 + data2))  # Preserve order, remove duplicates
                    return self.serialize_field(merged, field_type)
            
            elif field_type == JsonFieldType.METADATA:
                # For object types, merge dictionaries
                if isinstance(data1, dict) and isinstance(data2, dict):
                    merged = {**data1, **data2}
                    return self.serialize_field(merged, field_type)
            
            # Fallback: return first non-empty field
            return field1 if field1 and field1.strip() not in ['{}', '[]'] else field2
            
        except Exception as e:
            logger.warning(f"Failed to merge JSON fields: {e}")
            return field1 or field2 or "{}"
    
    def create_database_json_query(self, field_name: str, search_term: str, 
                                  query_type: str = "contains") -> Tuple[str, List[Any]]:
        """
        Create optimized database query for JSON field search.
        
        Args:
            field_name: Name of JSON column in database
            search_term: Term to search for
            query_type: Type of query ("contains", "exact", "starts_with")
            
        Returns:
            Tuple of (SQL query, parameters)
        """
        if query_type == "contains":
            # Use JSON_EXTRACT for efficient searching
            query = f"JSON_EXTRACT({field_name}, '$') LIKE ?"
            params = [f"%{search_term}%"]
        elif query_type == "exact":
            query = f"JSON_EXTRACT({field_name}, '$[*]') = ?"
            params = [search_term]
        elif query_type == "starts_with":
            query = f"JSON_EXTRACT({field_name}, '$') LIKE ?"
            params = [f"{search_term}%"]
        else:
            raise ValueError(f"Unsupported query type: {query_type}")
        
        return query, params
    
    def _validate_structure(self, data: Any, field_type: JsonFieldType) -> None:
        """Validate data structure against field type schema"""
        if field_type not in self._field_schemas:
            return  # No schema defined, skip validation
        
        schema = self._field_schemas[field_type]
        
        # Validate based on expected type
        if schema["type"] == "list":
            if not isinstance(data, list):
                raise JsonValidationError(f"Expected list for {field_type.value}")
            
            # Check list constraints (allow empty lists in non-strict mode)
            min_items = schema.get("min_items", 0)
            if len(data) < min_items and (self.strict_validation or len(data) == 0):
                if len(data) == 0 and not self.strict_validation:
                    pass  # Allow empty lists in lenient mode
                else:
                    raise JsonValidationError(
                        f"{field_type.value} must have at least {min_items} items"
                    )
            
            if len(data) > schema.get("max_items", float('inf')):
                raise JsonValidationError(
                    f"{field_type.value} cannot have more than {schema['max_items']} items"
                )
            
            # Validate list items
            item_schema = schema.get("items", {})
            for i, item in enumerate(data):
                self._validate_item(item, item_schema, f"{field_type.value}[{i}]")
        
        elif schema["type"] == "object":
            if not isinstance(data, dict):
                raise JsonValidationError(f"Expected object for {field_type.value}")
            
            # Validate object properties if defined
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                if prop_name in data:
                    self._validate_item(data[prop_name], prop_schema, 
                                      f"{field_type.value}.{prop_name}")
    
    def _validate_item(self, item: Any, schema: Dict[str, Any], field_path: str) -> None:
        """Validate individual item against schema"""
        expected_type = schema.get("type", "string")
        
        if expected_type == "string":
            if not isinstance(item, str):
                raise JsonValidationError(f"{field_path} must be a string")
            
            if len(item) < schema.get("min_length", 0):
                raise JsonValidationError(
                    f"{field_path} must be at least {schema['min_length']} characters"
                )
            
            if len(item) > schema.get("max_length", float('inf')):
                raise JsonValidationError(
                    f"{field_path} cannot exceed {schema['max_length']} characters"
                )
            
            # Pattern validation for labels
            if "pattern" in schema:
                import re
                if not re.match(schema["pattern"], item):
                    raise JsonValidationError(f"{field_path} does not match required pattern")
        
        elif expected_type == "integer":
            if not isinstance(item, int):
                raise JsonValidationError(f"{field_path} must be an integer")
            
            if item < schema.get("min", float('-inf')):
                raise JsonValidationError(f"{field_path} must be at least {schema['min']}")
            
            if item > schema.get("max", float('inf')):
                raise JsonValidationError(f"{field_path} cannot exceed {schema['max']}")
    
    def _validate_task_test_specs(self, test_specs: Any) -> None:
        """Validate task test specifications structure"""
        if not isinstance(test_specs, dict):
            raise JsonValidationError("Test specs must be an object")
        
        required_fields = ["red_phase", "green_phase", "refactor_phase"]
        for field in required_fields:
            if field not in test_specs:
                raise JsonValidationError(f"Test specs missing required field: {field}")
            
            if not isinstance(test_specs[field], str) or len(test_specs[field]) < 10:
                raise JsonValidationError(f"Test specs {field} must be descriptive string")
    
    def _get_default_value(self, field_type: JsonFieldType) -> Any:
        """Get default value for field type"""
        if field_type in [JsonFieldType.GOALS, JsonFieldType.DEFINITION_OF_DONE, 
                         JsonFieldType.LABELS]:
            return []
        elif field_type in [JsonFieldType.METADATA, JsonFieldType.TASK_SPECS, 
                           JsonFieldType.ACCEPTANCE_CRITERIA]:
            return {}
        else:
            return None


# Convenience functions for common operations

def serialize_goals(goals: List[str]) -> str:
    """Serialize goals list to JSON string"""
    handler = JsonFieldHandler()
    return handler.serialize_field(goals, JsonFieldType.GOALS)


def deserialize_goals(json_str: str) -> List[str]:
    """Deserialize goals from JSON string"""
    handler = JsonFieldHandler()
    return handler.deserialize_field(json_str, JsonFieldType.GOALS, default=[])


def serialize_definition_of_done(dod: List[str]) -> str:
    """Serialize definition of done list to JSON string"""
    handler = JsonFieldHandler()
    return handler.serialize_field(dod, JsonFieldType.DEFINITION_OF_DONE)


def deserialize_definition_of_done(json_str: str) -> List[str]:
    """Deserialize definition of done from JSON string"""
    handler = JsonFieldHandler()
    return handler.deserialize_field(json_str, JsonFieldType.DEFINITION_OF_DONE, default=[])


def serialize_labels(labels: List[str]) -> str:
    """Serialize labels list to JSON string"""
    handler = JsonFieldHandler()
    return handler.serialize_field(labels, JsonFieldType.LABELS)


def deserialize_labels(json_str: str) -> List[str]:
    """Deserialize labels from JSON string"""
    handler = JsonFieldHandler()
    return handler.deserialize_field(json_str, JsonFieldType.LABELS, default=[])


def validate_epic_data(epic_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate complete epic data structure"""
    handler = JsonFieldHandler()
    return handler.validate_epic_json_fields(epic_data)


# Preset handlers for different validation levels
class EpicJsonHandler:
    """Preset handlers for epic JSON data compatibility"""
    
    @staticmethod
    def strict() -> JsonFieldHandler:
        """Strict validation handler for production data"""
        return JsonFieldHandler(strict_validation=True, max_field_size=8000)
    
    @staticmethod
    def lenient() -> JsonFieldHandler:
        """Lenient handler for development/migration"""
        return JsonFieldHandler(strict_validation=False, max_field_size=15000)
    
    @staticmethod
    def migration() -> JsonFieldHandler:
        """Special handler for data migration tasks"""
        return JsonFieldHandler(strict_validation=False, max_field_size=20000)


if __name__ == "__main__":
    # Quick demonstration
    handler = JsonFieldHandler()
    
    # Test with real epic data format
    sample_goals = [
        "Implementar captura de warnings em tempo real",
        "Criar interface interativa para decisões do usuário",
        "Persistir decisões em SQLite com propriedades ACID"
    ]
    
    # Serialize and deserialize
    goals_json = handler.serialize_field(sample_goals, JsonFieldType.GOALS)
    print(f"Serialized goals: {goals_json}")
    
    deserialized_goals = handler.deserialize_field(goals_json, JsonFieldType.GOALS)
    print(f"Deserialized goals: {deserialized_goals}")
    
    print(f"Round-trip successful: {sample_goals == deserialized_goals}")