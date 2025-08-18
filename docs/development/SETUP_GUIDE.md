# 🚀 TDD Project Template - Setup Guide

> **Step-by-step guide to get your TDD project running in minutes**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 📋 **Table of Contents**

- [🎯 Quick Start](#-quick-start)
- [💻 System Requirements](#-system-requirements)
- [🔧 Installation Methods](#-installation-methods)
- [🐍 Python Project Setup](#-python-project-setup)
- [📦 Node.js Project Setup](#-nodejs-project-setup)
- [🔀 Mixed Project Setup](#-mixed-project-setup)
- [🐙 GitHub Integration](#-github-integration)
- [🎨 GitHub Pages Dashboard](#-github-pages-dashboard)
- [✅ Environment Validation](#-environment-validation)
- [🔧 Troubleshooting](#-troubleshooting)

## 🎯 **Quick Start**

### **Method 1: GitHub Template (Recommended)**

1. **Click "Use this template"** on the GitHub repository page
2. **Create your new repository**
3. **Clone and setup:**
   ```bash
   git clone https://github.com/your-username/your-project-name.git
   cd your-project-name
   python setup/init_tdd_project.py
   ```

### **Method 2: Manual Clone**

```bash
# Clone template
git clone https://github.com/username/tdd-project-template.git my-tdd-project
cd my-tdd-project

# Run interactive setup
python setup/init_tdd_project.py

# Validate environment
python setup/validate_environment.py
```

## 💻 **System Requirements**

### **Minimum Requirements**
- **Python 3.8+** (required for core functionality)
- **Git** (version control)
- **4GB RAM** (recommended, 2GB minimum)
- **Internet connection** (for dependencies and GitHub integration)

### **Recommended Tools**
- **Poetry** (Python dependency management)
- **GitHub CLI** (`gh`) for repository automation
- **Docker** (optional, for containerized development)
- **VSCode** (IDE with pre-configured settings)

### **Quick System Check**

```bash
# Check Python version
python --version  # Should be 3.8+

# Check Git
git --version

# Check Poetry (optional but recommended)
poetry --version

# Check GitHub CLI (optional)
gh --version
```

## 🔧 **Installation Methods**

### **Option A: Interactive Setup Wizard (Recommended)**

The setup wizard will guide you through the entire process:

```bash
python setup/init_tdd_project.py
```

**What the wizard does:**
- ✅ Detects your project type (Python, Node.js, Mixed)
- ✅ Configures development environment
- ✅ Sets up GitHub integration
- ✅ Creates initial epic structure
- ✅ Installs dependencies
- ✅ Validates setup

### **Option B: Manual Step-by-Step Setup**

If you prefer manual control:

#### **Step 1: Choose Project Type**
```bash
# For Python projects
cp config/python/pyproject_poetry.toml pyproject.toml

# For Node.js projects  
cp config/node/package.json package.json

# For mixed projects
# Copy both configurations
```

#### **Step 2: Install Dependencies**
```bash
# Python with Poetry (recommended)
poetry install

# Python with pip
pip install -r requirements.txt

# Node.js
npm install
```

#### **Step 3: Configure Git**
```bash
git init
git add .
git commit -m "🎉 Initial commit: TDD project setup"
```

#### **Step 4: Create Initial Epic**
```bash
# Copy template epic
cp epics/epic_template.json epics/epic-1.json
# Edit epic-1.json with your project details
```

## 🐍 **Python Project Setup**

### **With Poetry (Recommended)**

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Configure Poetry**:
   ```bash
   poetry config virtualenvs.in-project true
   ```

3. **Install Dependencies**:
   ```bash
   poetry install
   ```

4. **Activate Virtual Environment**:
   ```bash
   poetry shell
   ```

5. **Run Tests**:
   ```bash
   poetry run pytest tests/ -v
   ```

6. **Start TDD Timer**:
   ```bash
   poetry run python tdah_tools/task_timer.py start EPIC-1.1
   ```

### **With pip**

1. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   
   # Activate (Linux/macOS)
   source venv/bin/activate
   
   # Activate (Windows)
   venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Tests**:
   ```bash
   pytest tests/ -v
   ```

### **Python Configuration Files**

The template includes pre-configured files:

- **`pyproject.toml`** - Poetry configuration with all necessary dependencies
- **`pytest.ini`** - Test configuration with coverage and markers
- **`.pre-commit-config.yaml`** - Code quality hooks
- **`mypy.ini`** - Type checking configuration

## 📦 **Node.js Project Setup**

### **With npm**

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Run Tests**:
   ```bash
   npm test
   ```

3. **Start Development Server**:
   ```bash
   npm run dev
   ```

### **With Yarn**

```bash
yarn install
yarn test
yarn dev
```

### **Node.js Configuration Files**

- **`package.json`** - npm/yarn configuration with test scripts
- **`jest.config.js`** - Jest testing framework configuration
- **`.eslintrc.js`** - ESLint code quality rules

## 🔀 **Mixed Project Setup**

For projects using both Python and Node.js:

1. **Setup Python Environment**:
   ```bash
   poetry install  # or pip install -r requirements.txt
   ```

2. **Setup Node.js Environment**:
   ```bash
   npm install  # or yarn install
   ```

3. **Run All Tests**:
   ```bash
   # Python tests
   poetry run pytest tests/

   # JavaScript/TypeScript tests
   npm test
   ```

## 🐙 **GitHub Integration**

### **Automatic Setup (via Wizard)**

The setup wizard can automatically:
- Create GitHub repository
- Configure GitHub Actions
- Setup GitHub Pages
- Configure issue templates

### **Manual GitHub Setup**

#### **1. Create Repository**
```bash
gh repo create your-project-name --public --source . --push
```

#### **2. Enable GitHub Actions**
The template includes workflows in `.github/workflows/`:
- **`tdd-automation.yml`** - Automated TDD workflow
- **`update-gantt.yml`** - Gantt chart generation
- **`pages-deploy.yml`** - GitHub Pages deployment

#### **3. Configure Repository Settings**
```bash
# Enable GitHub Pages (via GitHub CLI)
gh repo edit --enable-pages --pages-branch gh-pages

# Add repository topics
gh repo edit --add-topic tdd,python,automation,analytics
```

## 🎨 **GitHub Pages Dashboard**

### **Enable GitHub Pages**

1. **Via GitHub UI**:
   - Go to repository Settings
   - Scroll to "Pages" section
   - Select "Deploy from a branch"
   - Choose `gh-pages` branch

2. **Via GitHub CLI**:
   ```bash
   gh repo edit --enable-pages --pages-branch gh-pages
   ```

### **Configure Jekyll**

The template includes Jekyll configuration in `docs/`:
- **`_config.yml`** - Jekyll site configuration
- **`Gemfile`** - Ruby dependencies
- **`index.md`** - Dashboard homepage
- **`_layouts/`** - Custom layouts for epic documentation

### **Custom Domain (Optional)**

```bash
# Add custom domain
echo "your-domain.com" > docs/CNAME
git add docs/CNAME
git commit -m "Add custom domain"
git push
```

## ✅ **Environment Validation**

### **Run Validation Script**

```bash
python setup/validate_environment.py
```

### **Manual Validation Checklist**

- [ ] **Python 3.8+** installed and accessible
- [ ] **Virtual environment** activated (Poetry or venv)
- [ ] **Dependencies** installed successfully
- [ ] **Git** repository initialized
- [ ] **Tests** can run successfully
- [ ] **Directory structure** matches template
- [ ] **Configuration files** exist and are valid

### **Common Validation Issues**

#### **Python Version Error**
```bash
# Error: Python 3.7 or older
# Solution: Update Python
python --version  # Check current version
```

#### **Poetry Not Found**
```bash
# Error: poetry: command not found
# Solution: Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

#### **Import Errors**
```bash
# Error: ModuleNotFoundError
# Solution: Install dependencies and check PYTHONPATH
poetry install  # or pip install -r requirements.txt
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

## 🚀 **First TDD Cycle**

Once setup is complete, start your first TDD cycle:

### **1. Start Timer**
```bash
poetry run python tdah_tools/task_timer.py start EPIC-1.1
```

### **2. RED Phase - Write Failing Test**
```bash
# Write a failing test in tests/
pytest tests/ -x --tb=short  # Should fail
```

### **3. GREEN Phase - Implement Code**
```bash
# Implement minimal code to pass test
pytest tests/ --cov=src --cov-report=term-missing
```

### **4. REFACTOR Phase - Improve Code**
```bash
# Refactor while keeping tests green
pytest tests/ --cov=src --durations=10
```

### **5. Stop Timer and Analyze**
```bash
poetry run python tdah_tools/task_timer.py stop
poetry run python tdah_tools/analytics_engine.py report
```

## 🎯 **Next Steps**

After successful setup:

1. **📖 Read the methodology guide**: [TDD_METHODOLOGY.md](./TDD_METHODOLOGY.md)
2. **🎨 Customize your setup**: [CUSTOMIZATION.md](./CUSTOMIZATION.md)  
3. **📊 Explore analytics**: Check `tdah_tools/analytics_engine.py`
4. **🌐 Visit your dashboard**: `https://your-username.github.io/your-repo`
5. **🔄 Create your first epic**: Edit `epics/epic-1.json`

## 📞 **Getting Help**

- **🔧 Common Issues**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **💬 Discussions**: [GitHub Discussions](https://github.com/username/tdd-project-template/discussions)
- **🐛 Report Bugs**: [GitHub Issues](https://github.com/username/tdd-project-template/issues)
- **📚 Documentation**: Check `docs/` directory

---

**🎉 Congratulations! Your TDD project is ready for development.**

**Next:** Start your first epic with `EPIC-1.1` and follow the red-green-refactor cycle!