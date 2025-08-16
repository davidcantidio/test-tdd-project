# 🎨 TDD Project Template - Customization Guide

> **Complete guide to customize and extend the TDD template for your specific needs**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 📋 **Table of Contents**

- [🎯 Overview](#-overview)
- [🐍 Python Customization](#-python-customization)
- [📦 Node.js Customization](#-nodejs-customization)
- [🎨 Theme & Styling](#-theme--styling)
- [📊 Epic Templates](#-epic-templates)
- [⏰ TDAH Analytics](#-tdah-analytics)
- [🔄 GitHub Automation](#-github-automation)
- [📈 Visualization Customization](#-visualization-customization)
- [🔧 Development Environment](#-development-environment)
- [🌐 GitHub Pages](#-github-pages)
- [📱 CI/CD Pipeline](#-cicd-pipeline)

## 🎯 **Overview**

The TDD Project Template is designed to be highly customizable. You can adapt it for different:

- **Programming languages** (Python, Node.js, mixed)
- **Project types** (web apps, APIs, data science, CLI tools)
- **Team sizes** (solo developer, small team, enterprise)
- **Methodologies** (TDD, BDD, DDD)
- **Deployment targets** (cloud, on-premise, hybrid)

## 🐍 **Python Customization**

### **Package Manager Options**

#### **Poetry (Recommended)**
```toml
# pyproject.toml
[tool.poetry]
name = "your-project"
version = "0.1.0"
description = "Your project description"

[tool.poetry.dependencies]
python = "^3.8"
# Add your specific dependencies
fastapi = "^0.104.0"     # For web APIs
pandas = "^2.0.0"        # For data science
click = "^8.0.0"         # For CLI applications
```

#### **pip + requirements.txt**
```txt
# requirements.txt
# Web development
fastapi==0.104.0
uvicorn[standard]==0.24.0

# Data science
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
```

### **Testing Framework Configuration**

#### **pytest.ini Customization**
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test* *Tests
python_functions = test_*

# Custom markers for your project
markers =
    unit: Unit tests
    integration: Integration tests  
    e2e: End-to-end tests
    slow: Slow running tests
    api: API-specific tests
    database: Database tests
    redis: Redis cache tests
    
    # TDD phases
    red: RED phase tests (should fail initially)
    green: GREEN phase tests (implementation)
    refactor: REFACTOR phase tests (optimization)
    
    # Your custom markers
    critical: Critical functionality tests
    performance: Performance benchmarks
    security: Security-related tests

# Coverage configuration
addopts = 
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=90
    -ra
    --tb=short

# Async test configuration
asyncio_mode = auto
```

#### **mypy.ini Type Checking**
```ini
# mypy.ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True

# Your project modules
[mypy-your_project.*]
ignore_missing_imports = False

# Third-party modules without stubs
[mypy-pandas.*]
ignore_missing_imports = True
```

### **Pre-commit Hooks Customization**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        args: [--line-length=88]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  # Add your custom hooks
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  # Security scanning
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, src/]

  # Custom epic validation
  - repo: local
    hooks:
      - id: validate-epics
        name: Validate Epic JSON files
        entry: python scripts/validate_epic.py
        language: python
        files: ^epics/.*\.json$
```

## 📦 **Node.js Customization**

### **Package.json Configuration**

```json
{
  "name": "your-tdd-project",
  "version": "1.0.0",
  "description": "TDD project with Node.js",
  "scripts": {
    "dev": "nodemon src/index.js",
    "start": "node src/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:tdd-red": "jest --bail --verbose",
    "test:tdd-green": "jest --coverage --verbose",
    "test:tdd-refactor": "jest --coverage --detectSlowTests",
    "lint": "eslint src/ tests/",
    "lint:fix": "eslint src/ tests/ --fix",
    "format": "prettier --write src/ tests/",
    "epic:validate": "node scripts/validate_epic.js"
  },
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "jest": "^29.7.0",
    "supertest": "^6.3.3",
    "eslint": "^8.54.0",
    "prettier": "^3.1.0",
    "nodemon": "^3.0.2"
  }
}
```

### **Jest Configuration**

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'node',
  collectCoverageFrom: [
    'src/**/*.{js,ts}',
    '!src/**/*.d.ts',
    '!src/**/*.test.{js,ts}',
    '!src/**/index.{js,ts}'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    }
  },
  testMatch: [
    '<rootDir>/tests/**/*.test.{js,ts}',
    '<rootDir>/src/**/*.test.{js,ts}'
  ],
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  
  // Custom test markers using tags
  runner: '@jest/runner',
  testTimeout: 10000,
  
  // TDD-specific configuration
  verbose: true,
  bail: false, // Set to true for RED phase
  detectSlowTests: true
};
```

## 🎨 **Theme & Styling**

### **GitHub Pages Theme**

#### **Jekyll Configuration**
```yaml
# docs/_config.yml
title: "Your TDD Project"
description: "Test-Driven Development project with epic management"
url: "https://your-username.github.io"
baseurl: "/your-repository"

# Theme configuration
theme: minima
plugins:
  - jekyll-feed
  - jekyll-sitemap
  - jekyll-mermaid

# Custom TDD theme settings
tdd:
  primary_color: "#2E7D32"      # Green for passing tests
  secondary_color: "#D32F2F"    # Red for failing tests  
  accent_color: "#FF9800"       # Orange for refactor phase
  
  # Epic visualization
  gantt_theme: "default"
  mindmap_theme: "colorful"
  
  # Analytics dashboard
  chart_colors: ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0"]

# Navigation
header_pages:
  - index.md
  - epics.md
  - analytics.md
  - about.md

# Collections for epic management
collections:
  epics:
    output: true
    permalink: /:collection/:name/
```

#### **Custom CSS**
```scss
// docs/_sass/tdd-dashboard.scss
:root {
  --tdd-green: #2E7D32;
  --tdd-red: #D32F2F;  
  --tdd-orange: #FF9800;
  --tdd-blue: #1976D2;
  --tdd-purple: #7B1FA2;
}

.tdd-phase {
  &.red {
    border-left: 4px solid var(--tdd-red);
    background-color: rgba(211, 47, 47, 0.1);
  }
  
  &.green {
    border-left: 4px solid var(--tdd-green);
    background-color: rgba(46, 125, 50, 0.1);
  }
  
  &.refactor {
    border-left: 4px solid var(--tdd-orange);
    background-color: rgba(255, 152, 0, 0.1);
  }
}

.epic-card {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: transform 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  }
}

.progress-bar {
  height: 20px;
  background: linear-gradient(90deg, 
    var(--tdd-red) 0%, 
    var(--tdd-orange) 50%, 
    var(--tdd-green) 100%);
  border-radius: 10px;
}

// Mermaid diagram customization
.mermaid {
  .node rect {
    fill: var(--tdd-blue);
    stroke: var(--tdd-purple);
  }
  
  .taskText {
    fill: white !important;
  }
}
```

### **VSCode Theme Integration**

```json
// .vscode/settings.json
{
  "workbench.colorTheme": "Material Theme Darker",
  "workbench.iconTheme": "material-icon-theme",
  
  // TDD-specific color customizations
  "workbench.colorCustomizations": {
    "statusBar.background": "#2E7D32",
    "statusBar.foreground": "#ffffff",
    "activityBar.activeBorder": "#2E7D32",
    "editorGutter.modifiedBackground": "#FF9800",
    "editorGutter.addedBackground": "#2E7D32",
    "editorGutter.deletedBackground": "#D32F2F",
    
    // Test result colors
    "testing.iconFailed": "#D32F2F",
    "testing.iconPassed": "#2E7D32",
    "testing.iconQueued": "#FF9800"
  },
  
  // TDD-specific settings
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.autoTestDiscoverOnSaveEnabled": true,
  
  // Epic management
  "json.schemas": [
    {
      "fileMatch": ["epics/*.json"],
      "url": "./schemas/epic-schema.json"
    }
  ]
}
```

## 📊 **Epic Templates**

### **Custom Epic Schema**

```json
{
  "$schema": "https://json-schema.org/draft/2019-09/schema",
  "type": "object",
  "title": "TDD Epic Schema",
  "properties": {
    "epic": {
      "type": "object",
      "properties": {
        "id": {"type": "string", "pattern": "^EPIC-[0-9]+$"},
        "name": {"type": "string", "minLength": 5},
        "summary": {"type": "string", "minLength": 20},
        "tdd_enabled": {"type": "boolean", "const": true},
        
        // Custom fields for your domain
        "domain": {
          "type": "string",
          "enum": ["backend", "frontend", "data", "infrastructure", "security"]
        },
        
        "business_value": {
          "type": "string",
          "enum": ["critical", "high", "medium", "low"]
        },
        
        "technical_complexity": {
          "type": "string", 
          "enum": ["simple", "moderate", "complex", "expert"]
        },
        
        // Custom task phases
        "tasks": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "tdd_phase": {
                "type": "string",
                "enum": ["red", "green", "refactor", "integration", "documentation"]
              },
              
              // Your custom fields
              "component": {"type": "string"},
              "api_endpoint": {"type": "string"},
              "database_changes": {"type": "boolean"},
              "security_review": {"type": "boolean"}
            }
          }
        }
      }
    }
  }
}
```

### **Domain-Specific Epic Templates**

#### **Web API Epic Template**
```json
{
  "epic": {
    "id": "EPIC-API-1",
    "name": "User Authentication API",
    "domain": "backend",
    "api_specification": "OpenAPI 3.0",
    "endpoints": [
      {
        "method": "POST",
        "path": "/api/auth/login",
        "tdd_tests": ["test_valid_login", "test_invalid_credentials", "test_rate_limiting"]
      }
    ],
    "database_schema": {
      "tables": ["users", "sessions"],
      "migrations": ["001_create_users", "002_add_sessions"]
    },
    "security": {
      "authentication": "JWT",
      "authorization": "RBAC",
      "rate_limiting": "100 req/min"
    }
  }
}
```

#### **Data Science Epic Template**
```json
{
  "epic": {
    "id": "EPIC-DS-1", 
    "name": "Customer Churn Prediction Model",
    "domain": "data",
    "data_sources": ["customer_db", "usage_logs", "support_tickets"],
    "ml_pipeline": {
      "preprocessing": ["feature_engineering", "data_cleaning"],
      "models": ["random_forest", "gradient_boosting"],
      "validation": ["cross_validation", "holdout_test"],
      "metrics": ["accuracy", "precision", "recall", "f1"]
    },
    "artifacts": {
      "notebook": "notebooks/churn_prediction.ipynb", 
      "model_file": "models/churn_model.pkl",
      "feature_store": "features/churn_features.parquet"
    }
  }
}
```

## ⏰ **TDAH Analytics Customization**

### **Custom Productivity Metrics**

```python
# tdah_tools/custom_analytics.py
from analytics_engine import TDDAHAnalytics

class CustomProductivityAnalytics(TDDAHAnalytics):
    """Extended analytics for your specific workflow."""
    
    def __init__(self):
        super().__init__()
        self.custom_metrics = {}
    
    def analyze_code_quality_correlation(self, days: int = 30):
        """Correlate time tracking with code quality metrics."""
        sessions = self.get_sessions(days)
        
        # Your custom analysis
        quality_metrics = {
            'cyclomatic_complexity': self._get_complexity_metrics(),
            'test_coverage': self._get_coverage_metrics(),
            'code_duplication': self._get_duplication_metrics()
        }
        
        return {
            'focus_quality_impact': self._correlate_focus_quality(sessions),
            'optimal_session_length': self._find_optimal_length(sessions),
            'break_frequency_vs_quality': self._analyze_breaks(sessions)
        }
    
    def generate_team_dashboard(self):
        """Generate team-wide productivity dashboard."""
        # Implementation for team analytics
        pass
        
    def predict_task_duration(self, epic_id: str, task_complexity: str):
        """ML-based task duration prediction."""
        # Use historical data to predict durations
        pass
```

### **Custom Timer Configurations**

```python
# tdah_tools/timer_config.py
TIMER_CONFIGS = {
    'development': {
        'work_duration': 25,  # minutes
        'short_break': 5,
        'long_break': 15,
        'sessions_until_long_break': 4,
        'auto_start_breaks': True
    },
    
    'research': {
        'work_duration': 45,  # Longer sessions for deep work
        'short_break': 10,
        'long_break': 30,
        'sessions_until_long_break': 3
    },
    
    'testing': {
        'work_duration': 15,  # Short bursts for test writing
        'short_break': 3,
        'long_break': 10,
        'sessions_until_long_break': 6
    },
    
    'refactoring': {
        'work_duration': 35,  # Medium sessions for code improvement
        'short_break': 7,
        'long_break': 20,
        'sessions_until_long_break': 4
    }
}
```

## 🔄 **GitHub Automation Customization**

### **Custom Workflow Triggers**

```yaml
# .github/workflows/custom-tdd-automation.yml
name: Custom TDD Automation

on:
  push:
    branches: [main, develop]
    paths: ['epics/*.json', 'src/**', 'tests/**']
  
  pull_request:
    types: [opened, synchronize, reopened]
    
  # Custom trigger for epic changes
  workflow_dispatch:
    inputs:
      epic_id:
        description: 'Epic ID to process'
        required: true
        type: string
      action:
        description: 'Action to perform'
        required: true
        type: choice
        options: ['validate', 'deploy', 'analyze']

jobs:
  tdd-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Custom TDD phase detection
      - name: Detect TDD Phase
        id: tdd-phase
        run: |
          # Your logic to determine current TDD phase
          echo "phase=green" >> $GITHUB_OUTPUT
      
      # Phase-specific testing
      - name: RED Phase Testing
        if: steps.tdd-phase.outputs.phase == 'red'
        run: |
          poetry run pytest -x --tb=short --no-cov
          
      - name: GREEN Phase Testing
        if: steps.tdd-phase.outputs.phase == 'green'
        run: |
          poetry run pytest --cov=src --cov-fail-under=90
          
      - name: REFACTOR Phase Testing
        if: steps.tdd-phase.outputs.phase == 'refactor'
        run: |
          poetry run pytest --cov=src --durations=10
          
  custom-epic-validation:
    runs-on: ubuntu-latest
    if: contains(github.event.head_commit.modified, 'epics/')
    steps:
      - uses: actions/checkout@v4
      
      # Your custom epic validation
      - name: Validate Epic Business Rules
        run: |
          python scripts/validate_business_rules.py
          
      - name: Update Project Board
        run: |
          python scripts/sync_github_projects.py
```

### **Custom Issue Templates**

```yaml
# .github/ISSUE_TEMPLATE/tdd-epic-task.yml
name: 🎯 TDD Epic Task
description: Create a new task following TDD methodology
title: "[EPIC-X.Y] "
labels: ["tdd", "epic-task"]
assignees: []

body:
  - type: dropdown
    id: tdd-phase
    attributes:
      label: TDD Phase
      options:
        - RED (Write failing test)
        - GREEN (Implement code)
        - REFACTOR (Improve design)
    validations:
      required: true
      
  - type: input
    id: epic-id
    attributes:
      label: Epic ID
      placeholder: "EPIC-1.2"
    validations:
      required: true
      
  - type: textarea
    id: test-specification
    attributes:
      label: Test Specification
      description: Describe the tests that need to be written
      placeholder: |
        - should_validate_user_input_successfully
        - should_handle_invalid_data_gracefully
        - should_return_appropriate_error_messages
    validations:
      required: true
      
  - type: textarea
    id: acceptance-criteria
    attributes:
      label: Acceptance Criteria
      description: Define when this task is complete
      placeholder: |
        - [ ] All tests pass
        - [ ] Code coverage >= 90%
        - [ ] No existing tests broken
        - [ ] Documentation updated
    validations:
      required: true
```

## 📈 **Visualization Customization**

### **Custom Mermaid Themes**

```javascript
// scripts/visualization/custom_themes.js
const customMermaidThemes = {
  tdd_dark: {
    theme: 'dark',
    themeVariables: {
      primaryColor: '#2E7D32',
      primaryTextColor: '#ffffff',
      primaryBorderColor: '#1B5E20',
      lineColor: '#FF9800',
      sectionBkgColor: '#424242',
      altSectionBkgColor: '#616161',
      gridColor: '#757575',
      c0: '#D32F2F',  // RED phase
      c1: '#2E7D32',  // GREEN phase  
      c2: '#FF9800',  // REFACTOR phase
      c3: '#1976D2',  // Done
    }
  },
  
  business_friendly: {
    theme: 'default',
    themeVariables: {
      primaryColor: '#1976D2',
      primaryTextColor: '#ffffff', 
      primaryBorderColor: '#0D47A1',
      lineColor: '#424242',
      gridColor: '#E0E0E0'
    }
  }
};
```

### **Custom Chart Types**

```python
# scripts/visualization/custom_charts.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class CustomTDDVisualization:
    """Custom visualization for TDD projects."""
    
    def create_velocity_chart(self, epic_data):
        """Create team velocity chart with TDD phases."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Velocity Trend', 'Phase Distribution', 
                          'Quality Metrics', 'Burndown Chart'),
            specs=[[{"secondary_y": True}, {"type": "pie"}],
                   [{"type": "scatter"}, {"type": "scatter"}]]
        )
        
        # Your custom chart implementation
        return fig
    
    def create_code_quality_heatmap(self, metrics_data):
        """Heatmap showing code quality over time."""
        # Implementation
        pass
        
    def create_tdd_compliance_dashboard(self, compliance_data):
        """Dashboard showing TDD methodology compliance."""
        # Implementation
        pass
```

## 🔧 **Development Environment**

### **Docker Customization**

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies for your specific needs
RUN apt-get update && apt-get install -y \
    git \
    curl \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY . .

# Custom healthcheck for your app
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run your application
CMD ["poetry", "run", "python", "src/main.py"]
```

### **Development Container**

```json
// .devcontainer/devcontainer.json
{
  "name": "TDD Development Container",
  "build": {
    "dockerfile": "Dockerfile",
    "context": ".."
  },
  
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-python.pytest",
        "github.copilot"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/app/.venv/bin/python",
        "python.testing.pytestEnabled": true
      }
    }
  },
  
  "forwardPorts": [8000, 5432, 6379],
  "postCreateCommand": "poetry install",
  "remoteUser": "root",
  
  // Development-specific environment
  "containerEnv": {
    "ENVIRONMENT": "development",
    "DEBUG": "true",
    "TDD_AUTO_TIMER": "true"
  }
}
```

## 📞 **Getting Help**

- **📚 More Examples**: Check `examples/` directory in the repository
- **💬 Community**: [GitHub Discussions](https://github.com/username/tdd-project-template/discussions)
- **🔧 Issues**: [Report customization problems](https://github.com/username/tdd-project-template/issues)

---

**🎨 Your TDD template is now customized for your specific needs!**

**Next Steps:**
1. Test your customizations with a sample project
2. Share your custom configurations with the community
3. Create your own epic templates for your domain