# 🔗 TaskExecutionPlanner API Documentation

## Overview

The TaskExecutionPlanner API is integrated into the Streamlit application using query parameters. This provides a REST-like API interface without requiring a separate Flask server.

## Base URL

```
http://localhost:8501/?api=<endpoint>
```

## Authentication

API requests use the same authentication as the Streamlit UI:
- **Session Authentication**: Must be logged in through Streamlit UI
- **API Key Authentication**: Optional - use `api_key` parameter

## API Endpoints

### 1. Execution Planning

Plan task execution order with topological sorting and prioritization.

**Endpoint:** `/?api=execution`

**Parameters:**
- `epic_id` (required): Epic ID to plan execution for
- `preset` (optional): Scoring preset - one of: `balanced`, `critical_path`, `tdd_workflow`, `business_value`
- `custom_weights` (optional): JSON string with custom scoring weights

**Example:**
```
/?api=execution&epic_id=1&preset=balanced
```

**Response:**
```json
{
  "success": true,
  "data": {
    "epic_id": 1,
    "execution_order": ["TASK_001", "TASK_002", "TASK_003"],
    "task_scores": {
      "TASK_001": 8.5,
      "TASK_002": 7.2,
      "TASK_003": 6.8
    },
    "critical_path": ["TASK_001", "TASK_003"],
    "execution_metrics": {
      "total_tasks": 3,
      "total_estimated_hours": 24.5,
      "avg_score": 7.5
    },
    "dag_validation": {
      "is_valid": true,
      "graph_metrics": {...}
    },
    "created_at": "2025-01-15T14:30:00Z"
  },
  "timestamp": "2025-01-15T14:30:00Z"
}
```

### 2. Epic Validation

Validate epic dependencies and DAG structure.

**Endpoint:** `/?api=validate`

**Parameters:**
- `epic_id` (required): Epic ID to validate

**Example:**
```
/?api=validate&epic_id=1
```

**Response:**
```json
{
  "success": true,
  "data": {
    "epic_id": 1,
    "is_valid": true,
    "dependency_count": 5,
    "cycle_check": {
      "has_cycles": false,
      "cycles_found": []
    },
    "orphan_tasks": [],
    "validation_warnings": []
  },
  "timestamp": "2025-01-15T14:30:00Z"
}
```

### 3. Scoring Analysis

Analyze task scoring with different presets.

**Endpoint:** `/?api=scoring`

**Parameters:**
- `epic_id` (required): Epic ID to analyze
- `preset` (optional): Scoring preset (default: balanced)

**Example:**
```
/?api=scoring&epic_id=1&preset=tdd_workflow
```

**Response:**
```json
{
  "success": true,
  "data": {
    "epic_id": 1,
    "preset_used": "tdd_workflow",
    "task_scores": {
      "TASK_001": {
        "total_score": 8.5,
        "priority_score": 5.0,
        "tdd_bonus_score": 3.0,
        "value_density_score": 2.2
      }
    },
    "score_distribution": {
      "min": 4.2,
      "max": 8.5,
      "avg": 6.8,
      "std_dev": 1.2
    },
    "preset_weights": {
      "priority": 6.0,
      "tdd_bonus": 8.0,
      "value_density": 3.0
    }
  },
  "timestamp": "2025-01-15T14:30:00Z"
}
```

### 4. Execution Summary

Get execution summary for an epic.

**Endpoint:** `/?api=summary`

**Parameters:**
- `epic_id` (required): Epic ID to summarize
- `preset` (optional): Scoring preset (default: balanced)

**Example:**
```
/?api=summary&epic_id=1
```

**Response:**
```json
{
  "success": true,
  "data": {
    "epic_id": 1,
    "total_tasks": 15,
    "estimated_duration": {
      "hours": 120,
      "minutes": 7200
    },
    "critical_path": {
      "tasks": ["TASK_001", "TASK_005", "TASK_012"],
      "length": 3
    },
    "complexity_indicators": {
      "dependencies": 23,
      "avg_score": 7.2,
      "tdd_phases": 3
    },
    "execution_ready": true,
    "recommendations": [
      "Start with TASK_001 (highest priority)",
      "Monitor critical path tasks closely",
      "Consider parallel execution for independent tasks"
    ]
  },
  "timestamp": "2025-01-15T14:30:00Z"
}
```

### 5. Scoring Presets

List available scoring presets.

**Endpoint:** `/?api=presets`

**Parameters:** None

**Example:**
```
/?api=presets
```

**Response:**
```json
{
  "success": true,
  "data": {
    "presets": {
      "balanced": "Configuração balanceada para uso geral",
      "critical_path": "Foco no caminho crítico",
      "tdd_workflow": "Foco no workflow TDD (Red-Green-Refactor)",
      "business_value": "Foco no valor de negócio"
    },
    "default_preset": "balanced",
    "total_presets": 4
  },
  "timestamp": "2025-01-15T14:30:00Z"
}
```

## Error Responses

All endpoints return standardized error responses:

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": "Additional details (optional)",
  "timestamp": "2025-01-15T14:30:00Z"
}
```

### Common Error Codes

- `AUTH_REQUIRED`: Authentication required
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded
- `INVALID_ENDPOINT`: Unknown API endpoint
- `MISSING_PARAMETER`: Required parameter missing
- `INVALID_PARAMETER`: Invalid parameter value
- `SERVICE_UNAVAILABLE`: Service not available
- `PLANNING_FAILED`: Execution planning failed
- `VALIDATION_FAILED`: Dependency validation failed
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

API endpoints have rate limits:
- **Standard API calls**: 100 requests per hour
- **Heavy operations** (execution planning): 20 requests per hour
- **Light operations** (presets): No limit

Rate limit headers are included in responses (when possible with Streamlit).

## Usage Examples

### Python Client

```python
import requests

# Plan execution for epic
response = requests.get("http://localhost:8501/?api=execution", 
                       params={"epic_id": 1, "preset": "balanced"})
data = response.json()

if data.get("success"):
    execution_plan = data["data"]
    print(f"Execution order: {execution_plan['execution_order']}")
else:
    print(f"Error: {data.get('error')}")
```

### cURL

```bash
# Get execution plan
curl "http://localhost:8501/?api=execution&epic_id=1&preset=tdd_workflow"

# Validate epic dependencies
curl "http://localhost:8501/?api=validate&epic_id=1"

# List scoring presets
curl "http://localhost:8501/?api=presets"
```

### JavaScript/Fetch

```javascript
// Get scoring analysis
const response = await fetch('/?api=scoring&epic_id=1&preset=business_value');
const data = await response.json();

if (data.success) {
    console.log('Scoring analysis:', data.data);
} else {
    console.error('Error:', data.error);
}
```

## Integration with External Systems

The API can be integrated with:
- **CI/CD pipelines**: Automate task planning
- **Project management tools**: Sync execution plans
- **Analytics dashboards**: Export planning data
- **Mobile apps**: Access planning functionality

## Security Considerations

- Always use HTTPS in production
- Implement proper API key management
- Monitor rate limits and usage patterns
- Validate all input parameters
- Log API access for security auditing

## Testing

Test endpoints using the provided examples or integration tests in `tests/test_api_endpoints.py`.

## Support

For API support, check:
1. Streamlit application logs
2. Service health endpoint: `/?health=1`
3. Debug information in Streamlit UI (if debug mode enabled)