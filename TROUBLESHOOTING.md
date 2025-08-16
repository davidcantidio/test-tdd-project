# 🔧 TDD Project Template - Troubleshooting Guide

> **Solutions to common issues and problems when using the TDD template**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 📋 **Table of Contents**

- [🚨 Common Setup Issues](#-common-setup-issues)
- [🐍 Python Environment Problems](#-python-environment-problems)
- [📦 Node.js Environment Issues](#-nodejs-environment-issues)
- [🧪 Testing Framework Issues](#-testing-framework-issues)
- [🐙 GitHub Integration Problems](#-github-integration-problems)
- [⏰ TDAH Timer Issues](#-tdah-timer-issues)
- [📊 Visualization Problems](#-visualization-problems)
- [🔄 CI/CD Pipeline Issues](#-cicd-pipeline-issues)
- [📱 VSCode Integration](#-vscode-integration)
- [🌐 GitHub Pages Issues](#-github-pages-issues)
- [🎯 Type Hints and Constants Issues](#-type-hints-and-constants-issues)
- [🏗️ DRY Components Issues](#-dry-components-issues)
- [🔒 Security and Validation Issues](#-security-and-validation-issues)
- [🏗️ Service Layer Issues](#-service-layer-issues)
- [🔐 Authentication System Issues](#-authentication-system-issues)
- [🛡️ Security Stack Issues](#-security-stack-issues)
- [🌍 Environment Configuration Issues](#-environment-configuration-issues)
- [🏥 Health Monitoring Issues](#-health-monitoring-issues)
- [📞 Getting Additional Help](#-getting-additional-help)

## 🚨 **Common Setup Issues**

### **❌ Setup Wizard Fails to Start**

**Error:**
```
ModuleNotFoundError: No module named 'rich'
```

**Solution:**
```bash
# Install required dependencies first
pip install rich click

# Then run the wizard
python setup/init_tdd_project.py
```

**Error:**
```
Permission denied: cannot create directory 'src'
```

**Solution:**
```bash
# Check directory permissions
ls -la

# Fix permissions if needed  
sudo chown -R $USER:$USER .

# Or run with proper permissions
sudo python setup/init_tdd_project.py
```

### **❌ Template Files Not Found**

**Error:**
```
FileNotFoundError: config/python/pyproject_poetry.toml not found
```

**Solution:**
```bash
# Ensure you're in the correct directory
pwd  # Should show .../tdd-project-template

# Check if template files exist
ls config/python/

# If missing, re-clone the repository
git clone https://github.com/username/tdd-project-template.git
```

### **❌ Git Repository Issues**

**Error:**
```
fatal: not a git repository
```

**Solution:**
```bash
# Initialize git repository
git init

# Add initial commit
git add .
git commit -m "Initial commit"

# Add remote if needed
git remote add origin https://github.com/your-username/your-repo.git
```

## 🐍 **Python Environment Problems**

### **❌ Poetry Not Found**

**Error:**
```
poetry: command not found
```

**Solution:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (Linux/macOS)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
poetry --version
```

### **❌ Python Version Issues**

**Error:**
```
The current project's Python requirement (^3.8) is not compatible with some of the required packages.
```

**Solution:**
```bash
# Check Python version
python --version

# Update Python if needed (Ubuntu)
sudo apt update
sudo apt install python3.11 python3.11-venv

# Tell Poetry to use correct Python
poetry env use python3.11
```

### **❌ Virtual Environment Issues**

**Error:**
```
No module named 'src'
```

**Solution:**
```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or add to .bashrc/.zshrc
echo 'export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"' >> ~/.bashrc

# For Poetry projects
poetry install
poetry shell
```

### **❌ Package Installation Fails**

**Error:**
```
ERROR: Could not find a version that satisfies the requirement
```

**Solution:**
```bash
# Update pip first
pip install --upgrade pip

# Clear cache
pip cache purge

# Try installing with specific index
pip install -r requirements.txt -i https://pypi.org/simple/

# For Poetry
poetry cache clear pypi --all
poetry install
```

## 📦 **Node.js Environment Issues**

### **❌ Node.js Version Incompatibility**

**Error:**
```
Node.js version v14.0.0 is not supported
```

**Solution:**
```bash
# Install Node Version Manager
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install and use correct Node.js version
nvm install 18
nvm use 18

# Verify version
node --version
```

### **❌ NPM Installation Issues**

**Error:**
```
EACCES: permission denied, mkdir '/usr/local/lib/node_modules'
```

**Solution:**
```bash
# Option 1: Use npm with prefix (recommended)
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Option 2: Fix npm permissions
sudo chown -R $USER /usr/local/lib/node_modules

# Option 3: Use yarn instead
npm install -g yarn
yarn install
```

### **❌ Package Lock Issues**

**Error:**
```
npm ERR! peer dep missing
```

**Solution:**
```bash
# Delete lock files and node_modules
rm -rf node_modules package-lock.json yarn.lock

# Clean npm cache
npm cache clean --force

# Reinstall
npm install

# Or with exact versions
npm install --package-lock-only
npm ci
```

## 🧪 **Testing Framework Issues**

### **❌ Pytest Not Finding Tests**

**Error:**
```
collected 0 items
```

**Solution:**
```bash
# Check pytest configuration
cat pytest.ini

# Verify test file patterns
ls tests/test_*.py

# Run with discovery verbose
pytest --collect-only -v

# Fix PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src:$(pwd)"
```

### **❌ Import Errors in Tests**

**Error:**
```
ModuleNotFoundError: No module named 'src.my_module'
```

**Solution:**
```bash
# Option 1: Fix PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Option 2: Create __init__.py files
touch src/__init__.py
touch tests/__init__.py

# Option 3: Use relative imports
# In test file:
# from ..src.my_module import MyClass

# Option 4: Install package in development mode
pip install -e .
```

### **❌ Coverage Issues**

**Error:**
```
No source for code: '/path/to/project/src/my_module.py'
```

**Solution:**
```bash
# Check coverage configuration
cat .coveragerc

# Create .coveragerc if missing
cat > .coveragerc << EOF
[run]
source = src
omit = 
    tests/*
    */venv/*
    */virtualenvs/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
EOF
```

### **❌ Test Markers Not Working**

**Error:**
```
PytestUnknownMarkWarning: Unknown pytest.mark.red
```

**Solution:**
```bash
# Add markers to pytest.ini
cat >> pytest.ini << EOF

markers =
    red: RED phase tests (should fail initially)
    green: GREEN phase tests (implementation)
    refactor: REFACTOR phase tests (optimization)
    slow: Slow running tests
    integration: Integration tests
EOF
```

## 🐙 **GitHub Integration Problems**

### **❌ GitHub CLI Not Authenticated**

**Error:**
```
gh: To get started with GitHub CLI, please run: gh auth login
```

**Solution:**
```bash
# Authenticate with GitHub CLI
gh auth login

# Select authentication method
# Follow the prompts

# Verify authentication
gh auth status
```

### **❌ Repository Creation Fails**

**Error:**
```
gh: repository not found
```

**Solution:**
```bash
# Check if you're authenticated
gh auth status

# Create repository manually
gh repo create your-project-name --public --source . --push

# Or use the web interface and add remote
git remote add origin https://github.com/username/repo.git
git push -u origin main
```

### **❌ GitHub Actions Failing**

**Error:**
```
Error: Process completed with exit code 1
```

**Solution:**
```bash
# Check workflow file syntax
cd .github/workflows
yamllint *.yml

# Validate GitHub Actions locally (optional)
# Install act: https://github.com/nektos/act
act --list

# Check secrets are set properly
gh secret list

# View workflow logs
gh run list
gh run view [run-id]
```

### **❌ GitHub Pages Not Deploying**

**Error:**
```
Your site is having problems building
```

**Solution:**
```bash
# Check Pages settings
gh repo view --json url,isPages,pagesSource

# Validate Jekyll files
cd docs
bundle exec jekyll build --verbose

# Check for common issues
# 1. Missing _config.yml
# 2. Invalid YAML front matter
# 3. Missing Gemfile
# 4. Incorrect file permissions

# Create minimal _config.yml if missing
cat > docs/_config.yml << EOF
title: Your Project
description: TDD project documentation
theme: minima
EOF
```

## ⏰ **TDAH Timer Issues**

### **❌ Timer Database Issues**

**Error:**
```
sqlite3.OperationalError: no such table: time_sessions
```

**Solution:**
```bash
# Initialize database
python tdah_tools/task_timer.py init

# Or manually create database
python -c "
import sqlite3
from pathlib import Path

db_path = Path('data/time_tracking.db')
db_path.parent.mkdir(exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute('''
    CREATE TABLE IF NOT EXISTS time_sessions (
        id INTEGER PRIMARY KEY,
        task_id TEXT,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        duration_minutes INTEGER,
        status TEXT
    )
''')
conn.commit()
conn.close()
"
```

### **❌ Timer Import Errors**

**Error:**
```
ModuleNotFoundError: No module named 'tdah_tools'
```

**Solution:**
```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use module syntax
python -m tdah_tools.task_timer start EPIC-1.1

# Or install in development mode
pip install -e .
```

### **❌ Analytics Generation Fails**

**Error:**
```
No data available for analytics
```

**Solution:**
```bash
# Check if timer data exists
ls data/time_tracking.db

# Check database contents
sqlite3 data/time_tracking.db ".tables"
sqlite3 data/time_tracking.db "SELECT COUNT(*) FROM time_sessions;"

# Generate sample data for testing
python scripts/generate_sample_timer_data.py
```

## 📊 **Visualization Problems**

### **❌ Mermaid Diagrams Not Rendering**

**Error:**
```
Mermaid diagram failed to render
```

**Solution:**
```bash
# Check Mermaid syntax
# Install mermaid-cli for validation
npm install -g @mermaid-js/mermaid-cli

# Validate diagram
mmdc -i docs/gantt.mmd -o test.png

# Common syntax issues:
# 1. Missing quotes in task names
# 2. Invalid date formats  
# 3. Circular dependencies

# Fix GitHub Pages integration
# Add to docs/_config.yml:
echo "plugins: [jekyll-mermaid]" >> docs/_config.yml
```

### **❌ Plotly Charts Not Displaying**

**Error:**
```
Plotly chart container not found
```

**Solution:**
```bash
# Install required dependencies
pip install plotly kaleido

# Check HTML template
# Ensure container div exists:
# <div id="plotly-chart"></div>

# Generate charts with proper configuration
python scripts/visualization/generate_charts.py --debug
```

## 🔄 **CI/CD Pipeline Issues**

### **❌ Workflow Permissions**

**Error:**
```
Error: Resource not accessible by integration
```

**Solution:**
```bash
# Add permissions to workflow file
# .github/workflows/tdd-automation.yml:

permissions:
  contents: read
  pages: write
  id-token: write
  issues: write
  pull-requests: write

# Or enable workflow permissions in repo settings
gh repo edit --enable-issues --enable-projects --enable-wiki
```

### **❌ Environment Secrets**

**Error:**
```
Error: Secret CUSTOM_TOKEN is not set
```

**Solution:**
```bash
# Add repository secrets
gh secret set CUSTOM_TOKEN --body "your-token-value"

# List secrets
gh secret list

# For organization secrets
gh secret set CUSTOM_TOKEN --org your-org --body "value"
```

### **❌ Build Cache Issues**

**Error:**
```
Cache restore failed
```

**Solution:**
```yaml
# Update cache action in workflow
- uses: actions/cache@v3
  with:
    path: |
      ~/.cache/pip
      ~/.cache/pypoetry
    key: ${{ runner.os }}-python-${{ hashFiles('**/poetry.lock') }}
    restore-keys: |
      ${{ runner.os }}-python-
```

## 📱 **VSCode Integration**

### **❌ Python Extension Issues**

**Error:**
```
Python interpreter not found
```

**Solution:**
```bash
# Set Python interpreter in VSCode
# Ctrl+Shift+P -> "Python: Select Interpreter"
# Choose from list or enter path

# For Poetry projects
poetry env info --path
# Copy the path and set as interpreter

# Add to .vscode/settings.json
echo '{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.terminal.activateEnvironment": true
}' > .vscode/settings.json
```

### **❌ Test Discovery Issues**

**Error:**
```
No tests discovered
```

**Solution:**
```json
// .vscode/settings.json
{
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "python.testing.autoTestDiscoverOnSaveEnabled": true
}
```

### **❌ Debugging Not Working**

**Error:**
```
Debugger failed to attach
```

**Solution:**
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch", 
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": false,
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      }
    }
  ]
}
```

## 🌐 **GitHub Pages Issues**

### **❌ 404 Page Not Found**

**Error:**
```
404 - File not found
```

**Solution:**
```bash
# Check repository settings
gh repo view --json pagesUrl,pagesEnabled

# Ensure correct branch is set
gh repo edit --enable-pages --pages-branch gh-pages

# Check file exists
ls docs/index.md

# Verify workflow is running
gh workflow list
gh run list --workflow=pages-deploy
```

### **❌ Jekyll Build Fails**

**Error:**
```
Liquid Exception: Liquid syntax error
```

**Solution:**
```bash
# Test Jekyll build locally
cd docs
bundle exec jekyll serve --trace

# Common issues:
# 1. YAML front matter syntax
# 2. Liquid template syntax
# 3. Missing dependencies

# Fix common YAML issues
# Use proper indentation
# Quote special characters
# Validate with: http://www.yamllint.com/
```

### **❌ Custom Domain Issues**

**Error:**
```
Domain verification failed
```

**Solution:**
```bash
# Add CNAME file
echo "your-domain.com" > docs/CNAME

# Configure DNS records
# A record: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
# CNAME record: your-username.github.io

# Verify domain
gh repo edit --add-topic custom-domain
```

## 🎯 **Type Hints and Constants Issues**

### **❌ Type Hint Coverage Analysis Fails**

**Error:**
```
TypeError: 'NoneType' object has no attribute 'get_all_values'
```

**Solution:**
```bash
# Check if constants module is imported correctly
python -c "from streamlit_extension.config.constants import TaskStatus; print(TaskStatus.get_all_values())"

# Run the analysis tool
python analysis_type_hints.py

# If analysis shows low coverage, add type hints gradually
# Focus on high-priority CRUD methods first
```

### **❌ Constants Import Errors**

**Error:**
```
ImportError: No module named 'streamlit_extension.config.constants'
```

**Solution:**
```bash
# Verify constants module exists
ls -la streamlit_extension/config/constants.py

# Test constants functionality
python test_constants.py

# Check if __init__.py includes constants
grep -n "constants" streamlit_extension/config/__init__.py

# If missing, add to __init__.py:
# from .constants import TaskStatus, EpicStatus, ...
```

### **❌ Enum Values Not Working**

**Error:**
```
AttributeError: 'NoneType' object has no attribute 'value'
```

**Solution:**
```bash
# Test enum functionality
python -c "
from streamlit_extension.config.constants import TaskStatus
print('All values:', TaskStatus.get_all_values())
print('Active statuses:', TaskStatus.get_active_statuses())
print('TODO value:', TaskStatus.TODO.value)
"

# Use graceful fallbacks in code:
status_options = TaskStatus.get_all_values() if TaskStatus else ["todo", "in_progress", "completed"]
```

## 🏗️ **DRY Components Issues**

### **❌ Form Components Import Error**

**Error:**
```
ImportError: No module named 'streamlit_extension.components.form_components'
```

**Solution:**
```bash
# Check if form components exist
ls -la streamlit_extension/components/form_components.py

# Test form components
python test_form_components.py

# Verify dependencies are available
python -c "import streamlit; print('Streamlit available')"
```

### **❌ DRY Form Validation Fails**

**Error:**
```
TypeError: validate_and_submit() missing required arguments
```

**Solution:**
```bash
# Check form component usage pattern:
# 1. Create form configuration
config = FormConfig("form_id", "Form Title")

# 2. Create form instance
form = StandardForm(config)

# 3. Use validation
result = form.validate_and_submit(
    form_data,
    required_fields,
    validation_func=custom_validation,
    submit_func=submit_function
)

# Test form components thoroughly
python test_form_components.py -v
```

### **❌ Modal Forms Not Displaying**

**Error:**
```
Modal forms appear empty or don't respond to interactions
```

**Solution:**
```bash
# Check Streamlit version compatibility
pip show streamlit

# Ensure proper modal usage with context manager:
with form.modal_form(width="large"):
    # Form content here
    pass

# Check for session state conflicts
# Use unique form IDs to avoid conflicts
```

## 🔒 **Security and Validation Issues**

### **❌ CSRF Token Validation Fails**

**Error:**
```
Security Error: Invalid CSRF token
```

**Solution:**
```bash
# Check if security manager is available
python -c "
try:
    from streamlit_extension.utils.security import security_manager
    print('Security manager available:', security_manager is not None)
except ImportError as e:
    print('Security import error:', e)
"

# Ensure CSRF tokens are generated and validated properly
# In forms, check for:
csrf_field = security_manager.get_csrf_form_field(form_id)
csrf_valid, csrf_error = security_manager.require_csrf_protection(form_id, token)
```

### **❌ Rate Limiting Blocking Operations**

**Error:**
```
Rate limited: Too many requests
```

**Solution:**
```bash
# Check rate limiting configuration
python -c "
from streamlit_extension.utils.security import check_rate_limit
result, error = check_rate_limit('test_operation')
print(f'Rate limit result: {result}, error: {error}')
"

# Adjust rate limits in security configuration if needed
# Wait between operations or implement exponential backoff
```

### **❌ Validation Rules Not Applied**

**Error:**
```
Invalid data passed validation checks
```

**Solution:**
```bash
# Test validation rules
python -c "
from streamlit_extension.config.constants import ValidationRules
print('Max name length:', ValidationRules.MAX_NAME_LENGTH)
print('Email pattern:', ValidationRules.EMAIL_PATTERN)
"

# Check validation implementation:
# 1. Import validation functions correctly
# 2. Apply business rules consistently  
# 3. Use ValidationRules constants for limits
```

## 🏗️ **Service Layer Issues**

### **❌ Service Import Errors**

**Error:**
```
ImportError: No module named 'streamlit_extension.services'
```

**Solution:**
```bash
# Check if services module exists
ls -la streamlit_extension/services/

# Verify service container setup
python -c "
from streamlit_extension.services import ServiceContainer
container = ServiceContainer()
print('Container initialized:', container is not None)
"

# Test individual service imports
python -c "
from streamlit_extension.services import ClientService, ProjectService
print('Services imported successfully')
"
```

### **❌ Service Container Registration Fails**

**Error:**
```
ServiceError: Service 'client_service' not registered
```

**Solution:**
```bash
# Check service container initialization
python -c "
from streamlit_extension.services.service_container import ServiceContainer
container = ServiceContainer()
health = container.health_check()
print('Container health:', health)
"

# Verify all services are registered
python -c "
from streamlit_extension.services import ServiceContainer
container = ServiceContainer()
services = ['client_service', 'project_service', 'epic_service', 'task_service', 'analytics_service', 'timer_service']
for service in services:
    try:
        svc = getattr(container, f'get_{service}')()
        print(f'{service}: OK')
    except Exception as e:
        print(f'{service}: ERROR - {e}')
"
```

### **❌ ServiceResult Pattern Errors**

**Error:**
```
AttributeError: 'ServiceResult' object has no attribute 'is_success'
```

**Solution:**
```bash
# Check ServiceResult usage pattern
python -c "
from streamlit_extension.services.base import ServiceResult
result = ServiceResult.success('test')
print('Success result:', result.success, result.data)

error_result = ServiceResult.error('Test error')
print('Error result:', error_result.success, error_result.errors)
"

# Use proper ServiceResult checking:
# if result.success:
#     data = result.data
# else:
#     errors = result.errors
```

### **❌ Repository Transaction Errors**

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Check database connection pool
python -c "
from streamlit_extension.services.base import BaseRepository
from streamlit_extension.utils.database import DatabaseManager

db_manager = DatabaseManager()
repo = BaseRepository(db_manager)
print('Repository initialized:', repo is not None)
"

# Test transaction handling
python -c "
from streamlit_extension.services import ServiceContainer
container = ServiceContainer()
client_service = container.get_client_service()

# Test with proper transaction context
try:
    result = client_service.get_all_clients()
    print('Transaction test:', result.success)
except Exception as e:
    print('Transaction error:', e)
"
```

### **❌ Business Rule Validation Fails**

**Error:**
```
ValidationError: Email already exists
```

**Solution:**
```bash
# Check business rule validation
python -c "
from streamlit_extension.services import ServiceContainer
container = ServiceContainer()
client_service = container.get_client_service()

# Test validation rules
client_data = {
    'name': 'Test Client',
    'email': 'test@example.com',
    'phone': '+1234567890'
}

result = client_service.validate_client_data(client_data)
print('Validation result:', result.success)
if not result.success:
    print('Validation errors:', result.errors)
"

# Business rules to check:
# 1. Email uniqueness (clients)
# 2. Project name uniqueness per client
# 3. Task dependencies (no cycles)
# 4. Date consistency (start <= end)
# 5. Budget validation (positive values)
```

### **❌ TDD Workflow Integration Issues**

**Error:**
```
TypeError: advance_tdd_phase() missing required argument 'task_id'
```

**Solution:**
```bash
# Test TDD workflow integration
python -c "
from streamlit_extension.services import ServiceContainer
container = ServiceContainer()
task_service = container.get_task_service()

# Check TDD phase management
task_id = 1  # Replace with actual task ID
result = task_service.advance_tdd_phase(task_id)
print('TDD phase advancement:', result.success)

if result.success:
    print('New phase:', result.data)
else:
    print('TDD errors:', result.errors)
"

# TDD Phase progression:
# RED -> GREEN -> REFACTOR -> RED (cycle)
# Ensure task exists and phase is valid
```

### **❌ Analytics Service Calculation Errors**

**Error:**
```
ZeroDivisionError: division by zero in productivity calculation
```

**Solution:**
```bash
# Test analytics calculations with safe defaults
python -c "
from streamlit_extension.services import ServiceContainer
container = ServiceContainer()
analytics_service = container.get_analytics_service()

# Test dashboard metrics
try:
    metrics = analytics_service.get_dashboard_metrics()
    print('Dashboard metrics:', metrics.success)
    if metrics.success:
        print('Metrics data keys:', list(metrics.data.keys()))
except Exception as e:
    print('Analytics error:', e)
"

# Analytics calculations use safe defaults:
# - Zero division protection
# - Minimum data requirements
# - Graceful degradation for empty datasets
```

### **❌ Timer Service Session Errors**

**Error:**
```
TimerError: Invalid session type 'custom_focus'
```

**Solution:**
```bash
# Check valid session types
python -c "
from streamlit_extension.services import ServiceContainer
from streamlit_extension.config.constants import SessionType

container = ServiceContainer()
timer_service = container.get_timer_service()

# Check available session types
print('Session types:', [t.value for t in SessionType])

# Valid types: focus, break, deep_work, planning, review
session_data = {
    'session_type': SessionType.FOCUS.value,
    'duration_minutes': 25,
    'task_id': 1
}

result = timer_service.start_session(session_data)
print('Session start:', result.success)
"
```

### **❌ Service Health Check Failures**

**Error:**
```
HealthCheckError: Service dependencies not available
```

**Solution:**
```bash
# Run comprehensive service health check
python -c "
from streamlit_extension.services import ServiceContainer

container = ServiceContainer()
health = container.health_check()

print('=== Service Health Check ===')
for service, status in health.items():
    status_icon = '✅' if status['healthy'] else '❌'
    print(f'{status_icon} {service}: {status.get('message', 'OK')}')

# Check database connectivity
print('\n=== Database Health ===')
db_health = container.get_client_service().repository.health_check()
print(f'Database: {'✅ Connected' if db_health else '❌ Connection failed'}')
"

# Health check verifies:
# 1. Database connectivity
# 2. Service initialization
# 3. Configuration validation
# 4. Dependency availability
```

## 🔐 **Authentication System Issues**

### **❌ Authentication Import Errors**

**Error:**
```
ImportError: No module named 'streamlit_extension.auth'
```

**Solution:**
```bash
# Check if auth module exists
ls -la streamlit_extension/auth/

# Verify all auth files are present
ls streamlit_extension/auth/
# Should show: __init__.py, auth_manager.py, login_page.py, middleware.py, session_handler.py, user_model.py

# Test auth module import
python -c "
from streamlit_extension.auth import AuthManager
print('AuthManager imported successfully')
"
```

### **❌ Database Tables Not Created**

**Error:**
```
sqlite3.OperationalError: no such table: auth_users
```

**Solution:**
```bash
# Initialize authentication database tables
python -c "
from streamlit_extension.auth.auth_manager import AuthManager
auth_manager = AuthManager()
print('Authentication tables created successfully')
"

# Verify tables exist
sqlite3 framework.db ".tables" | grep auth

# Check table structure
sqlite3 framework.db ".schema auth_users"
```

### **❌ User Registration Fails**

**Error:**
```
Registration failed: Username or email already exists
```

**Solution:**
```bash
# Check existing users
sqlite3 framework.db "SELECT username, email FROM auth_users;"

# Clear test users if needed (development only)
sqlite3 framework.db "DELETE FROM auth_users WHERE username LIKE 'test%';"

# Test registration with unique credentials
python -c "
from streamlit_extension.auth.auth_manager import AuthManager
auth = AuthManager()
result = auth.register_user('test_user_$(date +%s)', 'test$(date +%s)@example.com', 'testpassword123')
print('Registration result:', result.success, result.message)
"
```

### **❌ Login Session Issues**

**Error:**
```
Session expired or invalid
```

**Solution:**
```bash
# Check session handler configuration
python -c "
from streamlit_extension.auth.session_handler import SessionHandler
handler = SessionHandler()
print('Session handler initialized')

# Check active sessions
sessions = handler.get_active_sessions()
print('Active sessions:', len(sessions))
"

# Clear expired sessions manually
python -c "
from streamlit_extension.auth.session_handler import SessionHandler
handler = SessionHandler()
cleaned = handler.cleanup_expired_sessions()
print('Cleaned expired sessions:', cleaned)
"
```

### **❌ Account Lockout Issues**

**Error:**
```
Account temporarily locked
```

**Solution:**
```bash
# Check lockout status
sqlite3 framework.db "
SELECT username, failed_login_attempts, locked_until 
FROM auth_users 
WHERE locked_until IS NOT NULL;
"

# Reset account lockout (development only)
sqlite3 framework.db "
UPDATE auth_users 
SET failed_login_attempts = 0, locked_until = NULL 
WHERE username = 'your_username';
"

# Test account unlock
python -c "
from streamlit_extension.auth.auth_manager import AuthManager
auth = AuthManager()
result = auth.authenticate('your_username', 'your_password')
print('Login result:', result.success, result.message)
"
```

### **❌ Authentication Middleware Not Working**

**Error:**
```
@require_auth() decorator not blocking access
```

**Solution:**
```bash
# Check if @require_auth() is applied correctly
grep -r "@require_auth" streamlit_extension/pages/

# Verify middleware import
python -c "
from streamlit_extension.auth.middleware import require_auth
print('Middleware imported successfully')
"

# Test authentication check
python -c "
from streamlit_extension.auth import is_authenticated
print('Auth check function available:', callable(is_authenticated))
"

# Check Streamlit session state integration
# In Streamlit app, verify:
# st.session_state should contain auth-related keys when logged in
```

## 🛡️ **Security Stack Issues**

### **❌ Security Manager Import Errors**

**Error:**
```
ImportError: No module named 'streamlit_extension.utils.security'
```

**Solution:**
```bash
# Check if security module exists
ls -la streamlit_extension/utils/security.py

# Test security manager import
python -c "
from streamlit_extension.utils.security import security_manager
print('Security manager imported:', security_manager is not None)
"

# Check security features availability
python -c "
from streamlit_extension.utils.security import (
    sanitize_input, validate_form, check_rate_limit, 
    create_safe_client, create_safe_project
)
print('Security functions imported successfully')
"
```

### **❌ CSRF Token Generation Fails**

**Error:**
```
AttributeError: 'NoneType' object has no attribute 'generate_csrf_token'
```

**Solution:**
```bash
# Test CSRF token generation
python -c "
from streamlit_extension.utils.security import security_manager
token = security_manager.generate_csrf_token('test_form')
print('CSRF token generated:', len(token) > 0)
print('Token preview:', token[:16] + '...')
"

# Test CSRF validation
python -c "
from streamlit_extension.utils.security import security_manager
token = security_manager.generate_csrf_token('test_form')
valid = security_manager.validate_csrf_token('test_form', token)
print('CSRF validation result:', valid)
"

# Check Streamlit session state for CSRF tokens
# In Streamlit: st.session_state should contain csrf_token_[form_id] keys
```

### **❌ XSS Sanitization Not Working**

**Error:**
```
Dangerous content not being sanitized
```

**Solution:**
```bash
# Test XSS sanitization
python -c "
from streamlit_extension.utils.security import sanitize_input
test_input = '<script>alert(\"XSS\")</script>Hello World'
sanitized = sanitize_input(test_input)
print('Original:', test_input)
print('Sanitized:', sanitized)
print('Script removed:', '<script>' not in sanitized)
"

# Test HTML entity encoding
python -c "
from streamlit_extension.utils.security import sanitize_display
dangerous_text = '<img src=x onerror=alert(1)>Test'
safe_text = sanitize_display(dangerous_text)
print('Dangerous text sanitized:', '<' not in safe_text or '&lt;' in safe_text)
"
```

### **❌ Rate Limiting Not Functioning**

**Error:**
```
Rate limiting allows unlimited requests
```

**Solution:**
```bash
# Test rate limiting functionality
python -c "
from streamlit_extension.utils.security import check_rate_limit
import time

print('Testing rate limiting...')
for i in range(10):
    allowed, error = check_rate_limit('test_operation')
    print(f'Request {i+1}: Allowed={allowed}, Error={error}')
    if not allowed:
        break
    time.sleep(0.1)
"

# Check rate limit configuration
python -c "
from streamlit_extension.utils.security import get_rate_limit_stats
stats = get_rate_limit_stats()
print('Rate limit stats:', stats)
"

# Reset rate limits for testing
python -c "
from streamlit_extension.utils.security import reset_rate_limits
reset_rate_limits('test_operation')
print('Rate limits reset for test_operation')
"
```

### **❌ DoS Protection Triggering False Positives**

**Error:**
```
DoS protection blocking legitimate requests
```

**Solution:**
```bash
# Check DoS protection configuration
python -c "
from streamlit_extension.utils.security import check_dos_protection
allowed, error, details = check_dos_protection('normal_operation')
print('DoS check result:', allowed, error)
print('Protection details:', details)
"

# Get DoS protection statistics
python -c "
from streamlit_extension.utils.security import get_dos_protection_stats
stats = get_dos_protection_stats()
print('DoS protection stats:', stats)
"

# Reset DoS protection if needed
python -c "
from streamlit_extension.utils.security import reset_dos_protection
reset_dos_protection('normal_operation', user_id='test_user')
print('DoS protection reset')
"
```

### **❌ Input Validation Too Strict**

**Error:**
```
Valid input being rejected by validation
```

**Solution:**
```bash
# Test input validation patterns
python -c "
from streamlit_extension.utils.security import validate_form
test_data = {
    'name': 'Valid Name',
    'email': 'valid@example.com',
    'description': 'A normal description without dangerous content'
}
is_valid, errors = validate_form(test_data)
print('Validation result:', is_valid)
if not is_valid:
    print('Validation errors:', errors)
"

# Check if security module is too restrictive
# Adjust validation patterns in security.py if needed
# Or use specific safe functions for known-good data
```

## 🌍 **Environment Configuration Issues**

### **❌ Environment Configuration Import Errors**

**Error:**
```
ImportError: No module named 'config.environment'
```

**Solution:**
```bash
# Check if config module exists
ls -la config/environment.py

# Test environment configuration import
python -c "
from config.environment import get_config
config = get_config()
print('Environment configuration loaded:', config.environment)
"

# Check environment files
ls -la config/environments/
# Should show: development.yaml, staging.yaml, production.yaml
```

### **❌ Environment Variable Not Found**

**Error:**
```
Missing required environment variables for production: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
```

**Solution:**
```bash
# Set required environment variables
export TDD_ENVIRONMENT=development  # Use development mode to skip required vars

# For production, set all required variables:
export TDD_ENVIRONMENT=production
export GOOGLE_CLIENT_ID="your_google_client_id"
export GOOGLE_CLIENT_SECRET="your_google_client_secret"
export LOG_LEVEL="INFO"

# Test configuration loading
python config/environment.py

# Create .env file for persistent configuration (development only)
cat > .env << EOF
TDD_ENVIRONMENT=development
GOOGLE_CLIENT_ID=dev_client_id
GOOGLE_CLIENT_SECRET=dev_client_secret
LOG_LEVEL=DEBUG
EOF
```

### **❌ YAML Configuration Parse Error**

**Error:**
```
yaml.scanner.ScannerError: while scanning for the next token
```

**Solution:**
```bash
# Validate YAML syntax
python -c "
import yaml
with open('config/environments/development.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print('YAML is valid:', config is not None)
"

# Check for common YAML issues:
# 1. Incorrect indentation (use spaces, not tabs)
# 2. Missing quotes around special characters
# 3. Unescaped colons or other special characters

# Test with a minimal YAML config
cat > config/environments/test.yaml << EOF
app:
  name: "Test App"
  debug: true

database:
  framework_db_path: "framework.db"
  
security:
  require_auth: false
EOF

python -c "
from config.environment import EnvironmentConfigLoader
loader = EnvironmentConfigLoader()
loader.environment = 'test'
config = loader.load_config()
print('Test config loaded:', config.app_name)
"
```

### **❌ Configuration Validation Fails**

**Error:**
```
ValueError: Missing required environment variables
```

**Solution:**
```bash
# Check which environment you're running
echo "Current environment: $TDD_ENVIRONMENT"

# Use development environment to bypass strict validation
export TDD_ENVIRONMENT=development

# Check configuration validation
python -c "
from config.environment import get_config
try:
    config = get_config()
    print('Config validation passed')
    print('Environment:', config.environment)
    print('Debug mode:', config.debug)
    print('Auth required:', config.security.require_auth)
except Exception as e:
    print('Validation error:', e)
"
```

### **❌ OAuth Configuration Issues**

**Error:**
```
Google OAuth credentials not found in environment variables
```

**Solution:**
```bash
# For development (OAuth optional)
export TDD_ENVIRONMENT=development

# For production with OAuth
export GOOGLE_CLIENT_ID="your_real_client_id"
export GOOGLE_CLIENT_SECRET="your_real_client_secret"

# Test OAuth configuration
python -c "
from config.environment import get_google_oauth_config
oauth_config = get_google_oauth_config()
print('OAuth Client ID set:', bool(oauth_config.client_id))
print('OAuth Client Secret set:', bool(oauth_config.client_secret))
print('Redirect URI:', oauth_config.redirect_uri)
"

# Get OAuth credentials from Google Cloud Console:
# 1. Go to https://console.cloud.google.com/
# 2. Create a new project or select existing
# 3. Enable Google+ API
# 4. Create OAuth 2.0 credentials
# 5. Add http://localhost:8501 to authorized redirect URIs
```

## 🏥 **Health Monitoring Issues**

### **❌ Health Endpoint Import Errors**

**Error:**
```
ImportError: No module named 'streamlit_extension.endpoints.health'
```

**Solution:**
```bash
# Check if health module exists
ls -la streamlit_extension/endpoints/health.py

# Test health endpoint import
python -c "
from streamlit_extension.endpoints.health import HealthCheckEndpoint
endpoint = HealthCheckEndpoint()
print('Health endpoint imported successfully')
"
```

### **❌ Health Checks Failing**

**Error:**
```
Database health check failed
```

**Solution:**
```bash
# Test health checks manually
python -c "
from streamlit_extension.endpoints.health import HealthCheckEndpoint
endpoint = HealthCheckEndpoint()

# Basic health check
basic = endpoint.basic_health()
print('Basic health:', basic)

# Detailed health check
detailed = endpoint.detailed_health()
print('Detailed health:', detailed)

# Component health
checker = endpoint.checker
db_health = checker.check_database()
print('Database health:', db_health)
"

# Check database connectivity
python -c "
from streamlit_extension.utils.database import DatabaseManager
try:
    db = DatabaseManager()
    clients = db.get_all_clients()
    print('Database connection: OK')
except Exception as e:
    print('Database connection error:', e)
"
```

### **❌ Kubernetes Probes Not Working**

**Error:**
```
Readiness probe failed: dependencies unavailable
```

**Solution:**
```bash
# Test readiness probe
python -c "
from streamlit_extension.endpoints.health import HealthCheckEndpoint
endpoint = HealthCheckEndpoint()

status_code, payload = endpoint.readiness_check()
print('Readiness status code:', status_code)
print('Readiness payload:', payload)

if status_code != 200:
    print('Readiness check failed - check dependencies')
"

# Test liveness probe
python -c "
from streamlit_extension.endpoints.health import HealthCheckEndpoint
endpoint = HealthCheckEndpoint()

status_code, payload = endpoint.liveness_check()
print('Liveness status code:', status_code)
print('Liveness payload:', payload)
"

# Health check dependencies:
# 1. Database connectivity
# 2. Cache system (if enabled)
# 3. Memory usage within limits
# 4. Disk space available
```

### **❌ Performance Monitoring Issues**

**Error:**
```
Component health status shows degraded
```

**Solution:**
```bash
# Check system resources
python -c "
import psutil
print('CPU usage:', psutil.cpu_percent(interval=1))
print('Memory usage:', psutil.virtual_memory().percent)
print('Disk usage:', psutil.disk_usage('.').percent)
"

# Monitor health status over time
python -c "
from streamlit_extension.endpoints.health import HealthCheckEndpoint
import time

endpoint = HealthCheckEndpoint()
for i in range(5):
    health = endpoint.detailed_health()
    print(f'Health check {i+1}:', health['status'])
    time.sleep(1)
"

# Check performance thresholds in health checker
# Adjust ComponentChecker methods if thresholds are too strict
```

### **❌ Health Check Timeout Issues**

**Error:**
```
Health check timed out
```

**Solution:**
```bash
# Test individual health components
python -c "
from streamlit_extension.endpoints.health import ComponentChecker
checker = ComponentChecker()

print('Testing database...')
db_result = checker.check_database()
print('Database result:', db_result)

print('Testing cache...')
cache_result = checker.check_cache()
print('Cache result:', cache_result)

print('Testing memory...')
memory_result = checker.check_memory_usage()
print('Memory result:', memory_result)
"

# For slow database operations, check:
# 1. Database file permissions
# 2. Disk space availability
# 3. SQLite WAL mode configuration
# 4. Connection pool settings
```

## 📞 **Getting Additional Help**

### **🔍 Diagnostic Commands**

Run these commands to gather information for bug reports:

```bash
# System information
python --version
poetry --version
git --version
gh --version

# Environment validation
python setup/validate_environment.py --output json > diagnostic.json

# Project structure
find . -type f -name "*.py" | head -20
find . -type f -name "*.json" | grep epic

# Recent git activity  
git log --oneline -10
git status --porcelain

# Python environment
pip list --format=freeze | head -20
poetry show | head -20

# Test execution
pytest --collect-only --quiet
```

### **📝 Creating Bug Reports**

When creating bug reports, include:

1. **Environment Information:**
   ```bash
   python setup/validate_environment.py --output json
   ```

2. **Reproduction Steps:**
   - Exact commands run
   - Expected vs actual behavior
   - Error messages (full stack trace)

3. **Configuration Files:**
   - `pyproject.toml` or `package.json`
   - `pytest.ini` 
   - `.vscode/settings.json`
   - Epic JSON files (if relevant)

### **🆘 Emergency Reset**

If everything breaks and you need to start fresh:

```bash
# Backup your work
git stash
git branch backup-$(date +%Y%m%d)

# Clean reset
git clean -fdx
git reset --hard HEAD

# Restore template files
git pull origin main

# Reinstall dependencies
poetry install  # or npm install
python setup/validate_environment.py
```

### **💬 Community Support**

- **GitHub Discussions**: [Ask questions](https://github.com/username/tdd-project-template/discussions)
- **GitHub Issues**: [Report bugs](https://github.com/username/tdd-project-template/issues)
- **Stack Overflow**: Tag questions with `tdd-project-template`

### **📚 Additional Resources**

- **TDD Methodology**: [Martin Fowler's TDD Guide](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- **Poetry Documentation**: [python-poetry.org](https://python-poetry.org/docs/)
- **pytest Documentation**: [docs.pytest.org](https://docs.pytest.org/)
- **GitHub Actions**: [docs.github.com/actions](https://docs.github.com/en/actions)

---

**🔧 Still having issues?**

If this guide doesn't solve your problem:
1. Search [existing issues](https://github.com/username/tdd-project-template/issues)
2. Create a [new issue](https://github.com/username/tdd-project-template/issues/new) with diagnostic information
3. Join our [community discussions](https://github.com/username/tdd-project-template/discussions)

**We're here to help! 🤝**