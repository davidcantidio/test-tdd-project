# 🎨 TDD Template Customization Guide

## 📋 Overview

This guide provides comprehensive instructions for customizing the TDD Project Template to match your specific project needs, branding, and development workflow.

## 🚀 Quick Setup (Automated)

**Recommended:** Use the interactive setup wizard that automatically handles most customization:

```bash
python setup/init_tdd_project.py
```

The wizard will:
- ✅ Replace all placeholders automatically
- ✅ Configure project type (Python/Node.js/Mixed)
- ✅ Setup GitHub integration
- ✅ Initialize development environment
- ✅ Create initial epic templates

## 🔧 Manual Customization

### **Essential Placeholders to Replace**

The template uses the following placeholder patterns that **must** be customized:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `[PROJECT_NAME]` | Your project name | `my-awesome-app` |
| `[AUTHOR_NAME]` | Your full name | `John Doe` |
| `[AUTHOR_EMAIL]` | Your email address | `john.doe@example.com` |
| `[USERNAME]` | Your GitHub username | `johndoe` |
| `[REPOSITORY_NAME]` | Repository name | `my-awesome-app` |
| `[DESCRIPTION]` | Project description | `A TDD project for awesome features` |

### **Files Containing Placeholders**

#### **1. Python Configuration Files**

**File:** `config/python/pyproject_poetry.toml`
```toml
[tool.poetry]
name = "[PROJECT_NAME]"           # → "my-awesome-app"
authors = ["[AUTHOR_NAME] <[AUTHOR_EMAIL]>"]  # → ["John Doe <john.doe@example.com>"]
homepage = "https://github.com/[USERNAME]/[REPOSITORY_NAME]"
repository = "https://github.com/[USERNAME]/[REPOSITORY_NAME]"
documentation = "https://[USERNAME].github.io/[REPOSITORY_NAME]/"
```

**File:** `config/python/pyproject.toml`
```toml
[project]
name = "[PROJECT_NAME]"
authors = [{name = "[AUTHOR_NAME]", email = "[AUTHOR_EMAIL]"}]
```

#### **2. Node.js Configuration Files**

**File:** `config/node/package.json`
```json
{
  "name": "[PROJECT_NAME]",
  "author": "[AUTHOR_NAME] <[AUTHOR_EMAIL]>",
  "homepage": "https://github.com/[USERNAME]/[REPOSITORY_NAME]#readme",
  "repository": {
    "url": "https://github.com/[USERNAME]/[REPOSITORY_NAME].git"
  }
}
```

#### **3. Epic Template Files**

**File:** `epics/epic_template.json`
```json
{
  "epic": {
    "id": "[EPIC-ID]",                    # → "EPIC-1"
    "name": "[Epic Name]",                # → "User Authentication"
    "summary": "[Summary focused on...]", # → "Implement secure user login system"
    "tasks": [
      {
        "id": "[EPIC-ID].1",             # → "EPIC-1.1"
        "title": "TEST: [specific behavior]",  # → "TEST: User login validation"
        "branch": "feature/[epic-name]",      # → "feature/user-authentication"
        "files_touched": ["tests/test_[module].py"]  # → ["tests/test_auth.py"]
      }
    ]
  }
}
```

#### **4. Documentation Files**

**File:** `README.md`
```markdown
# [PROJECT_NAME]
> [DESCRIPTION]

**Author:** [AUTHOR_NAME]
**Repository:** https://github.com/[USERNAME]/[REPOSITORY_NAME]
```

**File:** `docs/_config.yml`
```yaml
title: [PROJECT_NAME]
description: [DESCRIPTION]
baseurl: "/[REPOSITORY_NAME]"
url: "https://[USERNAME].github.io"
```

#### **5. GitHub Configuration**

**File:** `.github/workflows/*.yml`
```yaml
name: [PROJECT_NAME] CI/CD
env:
  PROJECT_NAME: [PROJECT_NAME]
  REPOSITORY_URL: https://github.com/[USERNAME]/[REPOSITORY_NAME]
```

## 🎯 Epic Customization

### **Epic Template Structure**

When creating new epics, customize these key areas:

#### **Epic Metadata**
```json
{
  "epic": {
    "id": "EPIC-[NUMBER]",                    // Sequential numbering
    "name": "Your Epic Name",                 // Descriptive, action-oriented
    "summary": "Clear, testable objective",   // What will be achieved
    "duration": "3 days",                     // Realistic time estimate
    "labels": ["tdd", "feature", "auth"],     // Relevant tags
  }
}
```

#### **Task Customization**
```json
{
  "tasks": [
    {
      "id": "EPIC-1.1",
      "title": "TEST: [what behavior you're testing]",  
      "tdd_phase": "red",    // Always start with "red"
      "estimate_minutes": 15, // Realistic time estimate
      "story_points": 2,     // Complexity (1=simple, 5=complex)
      "test_specs": [
        "should_authenticate_user_when_credentials_valid",
        "should_reject_user_when_credentials_invalid"
      ],
      "deliverables": ["tests/test_auth.py::test_login_validation"],
      "files_touched": ["tests/test_auth.py"],
      "branch": "feature/user-authentication",
      "risk": "Complex password validation logic",
      "mitigation": "Start with simple validation, iterate"
    }
  ]
}
```

### **TDD Phase Guidelines**

#### **RED Phase Tasks**
- **Title Pattern:** `"TEST: [specific behavior]"`
- **Focus:** Write failing tests first
- **Deliverables:** Test files only
- **Acceptance:** Test fails with clear assertion

#### **GREEN Phase Tasks**  
- **Title Pattern:** `"IMPL: [minimal functionality]"`
- **Focus:** Make tests pass with minimal code
- **Deliverables:** Implementation + updated tests
- **Acceptance:** All tests pass, no regression

#### **REFACTOR Phase Tasks**
- **Title Pattern:** `"REFACTOR: [design improvement]"`
- **Focus:** Improve code quality while keeping tests green
- **Deliverables:** Refactored code with passing tests
- **Acceptance:** Better design, all tests still pass

## 🛠️ Environment Customization

### **Python Projects**

#### **Dependencies**
Edit `pyproject_poetry.toml`:
```toml
[tool.poetry.dependencies]
python = "^3.8"

# Add your project-specific dependencies
fastapi = "^0.68.0"          # If building API
django = "^4.0.0"            # If using Django
flask = "^2.0.0"             # If using Flask
sqlalchemy = "^1.4.0"        # If using database
```

#### **Development Tools**
```toml
[tool.poetry.group.dev.dependencies]
# Customize based on your needs
black = "^22.0.0"            # Code formatting
flake8 = "^4.0.0"            # Linting
mypy = "^0.991"              # Type checking
pytest-cov = "^4.0.0"       # Coverage
```

### **Node.js Projects**

#### **Dependencies**
Edit `package.json`:
```json
{
  "dependencies": {
    "express": "^4.18.0",      // If building web server
    "react": "^18.2.0",        // If using React
    "lodash": "^4.17.0",       // Utility functions
    "axios": "^1.4.0"          // HTTP client
  },
  "devDependencies": {
    "typescript": "^5.1.0",    // If using TypeScript
    "jest": "^29.6.0",         // Testing framework
    "eslint": "^8.44.0",       // Linting
    "prettier": "^3.0.0"       // Code formatting
  }
}
```

## 📊 Analytics & Visualization

### **TDAH Timer Configuration**

Customize timer settings in `tdah_tools/task_timer.py`:
```python
# Default work session duration (minutes)
DEFAULT_SESSION_DURATION = 25  # Customize for your focus pattern

# Break reminder intervals
SHORT_BREAK_DURATION = 5       # After each session
LONG_BREAK_DURATION = 15       # After 4 sessions

# Database configuration
DATABASE_PATH = "custom_timer.db"  # Customize storage location
```

### **Analytics Dashboard**

Customize `tdah_tools/analytics_engine.py`:
```python
class TDDAHAnalytics:
    def __init__(self, db_path: str = "custom_analytics.db"):
        # Customize database path
        self.db_path = Path(db_path)
        
    def generate_productivity_metrics(self, days: int = 30):
        # Customize analysis period
        # Adjust focus quality thresholds
        high_focus_threshold = 0.8  # Customize based on your standards
```

## 🎨 Branding & Styling

### **GitHub Pages Customization**

#### **Site Configuration**
Edit `docs/_config.yml`:
```yaml
title: Your Project Name
description: Your project description
author: Your Name

# Customize theme and styling
theme: minima
plugins:
  - jekyll-feed
  - jekyll-sitemap

# Custom navigation
header_pages:
  - about.md
  - epics.md
  - analytics.md

# Social links
github_username: your-username
twitter_username: your-twitter
```

#### **Custom Styling**
Create `docs/_sass/custom.scss`:
```scss
// Customize colors
$primary-color: #3498db;      // Your brand primary color
$secondary-color: #2ecc71;    // Your brand secondary color
$accent-color: #e74c3c;       // Accent color for highlights

// Customize fonts
$heading-font: 'Your Font', sans-serif;
$body-font: 'Your Body Font', sans-serif;

// Custom styles
.epic-status {
  &.completed { background-color: $secondary-color; }
  &.in-progress { background-color: $primary-color; }
  &.pending { background-color: $accent-color; }
}
```

### **Visualization Themes**

#### **Mermaid Diagram Styling**
Edit `scripts/visualization/tdd_diagram_generator.py`:
```python
MERMAID_THEME_CONFIG = {
    "theme": "base",
    "themeVariables": {
        "primaryColor": "#3498db",      # Your brand colors
        "primaryTextColor": "#2c3e50",
        "primaryBorderColor": "#34495e",
        "lineColor": "#95a5a6",
        "secondaryColor": "#ecf0f1",
        "tertiaryColor": "#ffffff"
    }
}
```

#### **Plotly Dashboard Styling**
Edit `tdah_tools/analytics_engine.py`:
```python
DASHBOARD_THEME = {
    "layout": {
        "colorway": ['#3498db', '#2ecc71', '#e74c3c', '#f39c12'],  # Your colors
        "font": {"family": "Your Font, sans-serif"},
        "paper_bgcolor": "#ffffff",
        "plot_bgcolor": "#f8f9fa"
    }
}
```

## 🔧 Development Workflow Customization

### **Pre-commit Hooks**

Edit `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
        # Customize code formatting options
        args: [--line-length=88, --target-version=py38]
        
  - repo: https://github.com/pycqa/flake8
    rev: 5.0.4
    hooks:
      - id: flake8
        # Customize linting rules
        args: [--max-line-length=88, --ignore=E203,W503]
```

### **GitHub Actions Customization**

Edit `.github/workflows/tdd-automation.yml`:
```yaml
name: Your Project CI/CD

on:
  push:
    branches: [ main, develop ]  # Customize trigger branches
  pull_request:
    branches: [ main ]

jobs:
  test:
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]  # Customize versions
        os: [ubuntu-latest, windows-latest]        # Customize OS matrix
```

### **VSCode Configuration**

#### **Extensions**
Edit `.vscode/extensions.json`:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    // Add your preferred extensions
    "ms-vscode.vscode-typescript-next",
    "bradlc.vscode-tailwindcss",
    "your-favorite-extension"
  ]
}
```

#### **Settings**
Edit `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "black",
  
  // Customize for your preferences
  "editor.fontSize": 14,
  "editor.tabSize": 4,
  "files.autoSave": "onFocusChange"
}
```

## 🌐 GitHub Integration Customization

### **Issue Templates**

Edit `.github/ISSUE_TEMPLATE/epic-task.yml`:
```yaml
name: Epic Task
description: Create a new TDD epic task
title: "[EPIC-ID.X] [TDD_PHASE]: [Task Title]"
labels: ["tdd", "epic", "your-label"]  # Customize labels

body:
  - type: input
    id: epic-id
    attributes:
      label: Epic ID
      description: "Format: EPIC-X.Y"
      placeholder: "EPIC-1.1"
    validations:
      required: true
      
  # Customize form fields based on your needs
```

### **PR Templates**

Edit `.github/pull_request_template.md`:
```markdown
## 🎯 Epic Reference
- **Epic ID:** [EPIC-X.Y]
- **TDD Phase:** [Red/Green/Refactor]
- **Branch:** feature/[epic-name]

## ✅ TDD Checklist
- [ ] RED: Tests written and failing
- [ ] GREEN: Minimal implementation passes tests  
- [ ] REFACTOR: Code improved while tests stay green
- [ ] All existing tests pass
- [ ] Code coverage maintained/improved

## 📋 Changes Made
<!-- Describe what was implemented -->

## 🧪 Testing
<!-- How to test these changes -->

<!-- Customize sections based on your workflow -->
```

## 📚 Documentation Customization

### **Project-Specific Documentation**

Create custom documentation files:
- `docs/API.md` - API documentation
- `docs/DEPLOYMENT.md` - Deployment instructions  
- `docs/ARCHITECTURE.md` - System architecture
- `docs/CONTRIBUTING.md` - Contribution guidelines

### **Epic Documentation Generation**

Customize `scripts/convert_to_tdd.py`:
```python
def generate_epic_documentation(epic_data):
    """Customize how epic documentation is generated."""
    
    # Customize documentation format
    doc_template = """
    # Epic {epic_id}: {epic_name}
    
    **Summary:** {summary}
    **Duration:** {duration}
    **Status:** {status}
    
    ## Your Custom Sections
    <!-- Add project-specific sections -->
    """
    
    return doc_template.format(**epic_data)
```

## 🔍 Advanced Customization

### **Custom Epic Validations**

Edit `scripts/validate_epic.py`:
```python
def validate_custom_requirements(epic_data):
    """Add your project-specific validations."""
    
    errors = []
    
    # Example: Ensure certain fields exist
    required_custom_fields = ['business_value', 'technical_debt']
    for field in required_custom_fields:
        if field not in epic_data['epic']:
            errors.append(f"Missing required field: {field}")
    
    # Example: Validate naming conventions
    if not epic_data['epic']['name'].startswith('User'):
        errors.append("Epic names must start with 'User' for user stories")
    
    return errors
```

### **Custom Metrics and Analytics**

Create `tdah_tools/custom_analytics.py`:
```python
class CustomAnalytics(TDDAHAnalytics):
    """Extend analytics with project-specific metrics."""
    
    def analyze_business_value(self):
        """Calculate custom business value metrics."""
        # Your custom analytics logic
        pass
    
    def generate_custom_report(self):
        """Generate project-specific reports."""
        # Your custom reporting logic
        pass
```

## ✅ Customization Checklist

### **Essential (Must Do)**
- [ ] Replace all `[PLACEHOLDER]` values
- [ ] Update project metadata in configuration files
- [ ] Customize epic templates for your domain
- [ ] Configure development environment
- [ ] Set up GitHub integration

### **Recommended**
- [ ] Customize branding and styling
- [ ] Configure pre-commit hooks
- [ ] Set up custom GitHub Actions workflows
- [ ] Add project-specific documentation
- [ ] Configure VSCode settings

### **Advanced (Optional)**
- [ ] Create custom analytics and metrics
- [ ] Add custom epic validations
- [ ] Implement project-specific automation
- [ ] Customize visualization themes
- [ ] Add advanced GitHub integrations

## 🚨 Common Gotchas

### **1. Placeholder Replacement**
- ⚠️ **Issue:** Missing placeholder replacement breaks builds
- ✅ **Solution:** Use the setup wizard or systematically search/replace all placeholders

### **2. GitHub Pages Configuration**
- ⚠️ **Issue:** Site doesn't deploy correctly
- ✅ **Solution:** Ensure `baseurl` and `url` in `_config.yml` match your repository

### **3. Epic Template Validation**
- ⚠️ **Issue:** Invalid epic JSON breaks automation
- ✅ **Solution:** Always validate epics with `python scripts/validate_epic.py`

### **4. Path Configuration**
- ⚠️ **Issue:** Scripts can't find files after customization
- ✅ **Solution:** Update file paths in scripts when moving/renaming files

### **5. Environment Variables**
- ⚠️ **Issue:** GitHub Actions fail due to missing secrets
- ✅ **Solution:** Configure required secrets in repository settings

## 📞 Getting Help

### **Built-in Validation**
```bash
# Validate your customization
python setup/validate_environment.py

# Check epic format
python scripts/validate_epic.py epics/your-epic.json

# Test configuration
python -c "import config; print('Configuration valid')"
```

### **Community Resources**
- 📖 **Documentation:** `/docs/` directory
- 🐛 **Issues:** GitHub Issues for bugs
- 💬 **Discussions:** GitHub Discussions for questions  
- 🔧 **Examples:** `/examples/` directory for reference

---

**Last Updated:** 2025-01-09  
**Template Version:** 1.0  
**Status:** Ready for production use