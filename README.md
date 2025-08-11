# 🎯 TDD Project Template

> **Professional Test-Driven Development** template with epic management, automated progress tracking, and TDAH-optimized workflow

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![TDD Methodology](https://img.shields.io/badge/methodology-TDD-green.svg)](https://en.wikipedia.org/wiki/Test-driven_development)
[![Template Ready](https://img.shields.io/badge/template-ready-brightgreen.svg)](https://github.com/dbcantidio/tdd-project-template)

## 🌟 **What Makes This Template Special?**

This isn't just another project template. It's a **complete TDD ecosystem** that transforms how you manage and execute software projects:

- 🧪 **TDD Methodology Enforced** - Red-Green-Refactor cycle built into every workflow
- 📊 **Epic-Based Management** - JSON-driven project structure with GitHub integration
- ⏰ **TDAH Time Tracking** - Focus-optimized timer with productivity analytics
- 📈 **Automated Visualizations** - Real-time Gantt charts, mindmaps, and progress dashboards
- 🚀 **One-Command Setup** - Interactive wizard configures everything in minutes
- 🎨 **GitHub Pages Dashboard** - Beautiful, auto-updating project website
- 🔧 **Performance Optimized** - Advanced caching, parallel processing, and monitoring
- 🚨 **Production Ready** - Centralized error handling and graceful degradation

## 🚀 **Quick Start (GitHub Template)**

### **1. Use This Template**
Click the **"Use this template"** button above to create your new repository.

### **2. Clone and Initialize**
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_PROJECT_NAME.git
cd YOUR_PROJECT_NAME

# Run the interactive setup wizard
python3 setup/init_tdd_project.py

# Or non-interactive mode for CI/CD
python3 setup/init_tdd_project.py --non-interactive
```

2. **Set up development environment:**
   
   **For Python projects:**
   ```bash
   # Using Poetry (recommended)
   poetry install
   poetry shell
   
   # Or using pip
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```
   
   **For Node.js projects:**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Initialize the project:**
   ```bash
   # Run the setup wizard (if not already done)
   python setup/init_tdd_project.py
   
   # Validate environment
   python setup/validate_environment.py
   ```

## 🧪 TDD Workflow

This project follows the **Red-Green-Refactor** cycle:

### 1. 🔴 RED Phase - Write Failing Tests
```bash
# Start timer for focused work
python tdah_tools/task_timer.py start EPIC-1.1

# Write your failing test
# Example: tests/test_[module].py
```

### 2. 🟢 GREEN Phase - Make Tests Pass
```bash
# Implement minimal code to pass tests
# Example: src/[module].py

# Run tests to verify
pytest tests/
# or for Node.js
npm test
```

### 3. 🔄 REFACTOR Phase - Improve Design
```bash
# Improve code while keeping tests green
# Run tests frequently during refactoring
pytest tests/ --watch
```

### 4. ⏹️ Complete the Cycle
```bash
# Stop timer and log progress
python tdah_tools/task_timer.py stop

# Generate analytics
python tdah_tools/analytics_engine.py metrics
```

## 📋 Epic Management

### Current Epics
- [EPIC-1](epics/epic-1.json) - [EPIC_1_DESCRIPTION]
- [EPIC-2](epics/epic-2.json) - [EPIC_2_DESCRIPTION]
- [EPIC-3](epics/epic-3.json) - [EPIC_3_DESCRIPTION]

### Working with Epics
```bash
# Validate epic format
python scripts/validate_epic.py epics/epic-1.json

# Generate epic documentation
python scripts/convert_to_tdd.py epics/epic-1.json

# Create new epic from template
cp epics/epic_template.json epics/epic-new.json
# Edit and customize epic-new.json
```

## 📊 Analytics & Progress

### View Progress
```bash
# Generate productivity metrics
python tdah_tools/analytics_engine.py metrics --days 7

# Analyze time patterns
python tdah_tools/analytics_engine.py patterns --days 30

# Create focus dashboard
python tdah_tools/analytics_engine.py dashboard --output dashboard.html
```

### Project Dashboard
- **Live Dashboard:** https://[USERNAME].github.io/[REPOSITORY_NAME]/
- **Epic Progress:** [View current epic status](https://[USERNAME].github.io/[REPOSITORY_NAME]/epics/)
- **Analytics:** [Productivity insights](https://[USERNAME].github.io/[REPOSITORY_NAME]/analytics/)

## 🛠️ Development

### Available Scripts

**Python (Poetry):**
```bash
poetry run pytest                 # Run tests
poetry run black .                # Format code
poetry run flake8                 # Lint code
poetry run mypy src/              # Type checking
poetry run pytest --cov          # Test with coverage
```

**Node.js:**
```bash
npm test                          # Run tests
npm run test:watch                # Run tests in watch mode
npm run test:coverage             # Run tests with coverage
npm run lint                      # Lint code
npm run format                    # Format code
npm run build                     # Build project
```

### File Structure
```
[REPOSITORY_NAME]/
├── src/                          # Source code
├── tests/                        # Test files
├── epics/                        # Epic JSON files
├── scripts/                      # Automation scripts
├── tdah_tools/                   # Time tracking & analytics
├── docs/                         # Documentation
├── .github/                      # GitHub workflows & templates
└── config/                       # Configuration templates
```

## 📈 Current Status

### Epic Progress
| Epic | Status | Progress | Estimated Completion |
|------|--------|----------|---------------------|
| EPIC-1 | 🟡 In Progress | 60% | [DATE] |
| EPIC-2 | ⏳ Planned | 0% | [DATE] |
| EPIC-3 | ✅ Completed | 100% | [DATE] |

### Quality Metrics
- **Test Coverage:** [COVERAGE]%
- **Code Quality:** [QUALITY_GRADE]
- **Documentation:** [DOC_COVERAGE]%

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/epic-name`
3. **Follow TDD workflow:** Red → Green → Refactor
4. **Write/update tests** for all changes
5. **Ensure all tests pass:** `pytest` or `npm test`
6. **Submit a pull request**

### Contribution Guidelines
- Follow the Red-Green-Refactor TDD cycle
- Maintain test coverage above 90%
- Update epic documentation for new features
- Use the provided issue and PR templates

## 📚 Documentation

- 📖 **[Setup Guide](docs/SETUP_GUIDE.md)** - Detailed setup instructions
- 🎯 **[Epic Management](docs/EPIC_MANAGEMENT.md)** - Working with epics
- ⏰ **[TDAH Timer](docs/TDAH_TIMER.md)** - Time tracking features
- 📊 **[Analytics](docs/ANALYTICS.md)** - Progress and productivity insights
- 🔧 **[Customization](docs/CUSTOMIZATION_GUIDE.md)** - Template customization
- 🐛 **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🚨 Troubleshooting

### Common Issues

**Tests not running:**
```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Verify dependencies
poetry install  # or npm install
```

**Timer not working:**
```bash
# Initialize timer database
python tdah_tools/task_timer.py init

# Check database permissions
chmod 666 task_timer.db
```

**Epic validation errors:**
```bash
# Validate epic format
python scripts/validate_epic.py epics/your-epic.json

# Check JSON syntax
python -m json.tool epics/your-epic.json
```

For more troubleshooting, see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Test-Driven Development** methodology by Kent Beck
- **TDAH-optimized workflow** inspired by productivity research
- **Epic management** system for agile development
- **Community contributors** and feedback

## 📞 Contact

- **Author:** [AUTHOR_NAME]
- **Email:** [AUTHOR_EMAIL]
- **GitHub:** [@[USERNAME]](https://github.com/[USERNAME])
- **Project Link:** https://github.com/[USERNAME]/[REPOSITORY_NAME]

---

## 🔗 Quick Links

- [🎯 View Current Epics](epics/)
- [📊 Live Dashboard](https://[USERNAME].github.io/[REPOSITORY_NAME]/)
- [🐛 Report Issues](https://github.com/[USERNAME]/[REPOSITORY_NAME]/issues)
- [💬 Discussions](https://github.com/[USERNAME]/[REPOSITORY_NAME]/discussions)
- [📋 Project Board](https://github.com/[USERNAME]/[REPOSITORY_NAME]/projects)

---

**Built with the [TDD Project Template](https://github.com/tdd-project-template/template)** 🚀