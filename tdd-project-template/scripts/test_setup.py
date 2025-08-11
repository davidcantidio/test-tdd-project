#!/usr/bin/env python3
"""
🧪 TDD Project Template - Setup Validation Test
===============================================

Script para validar que o template TDD está configurado corretamente.
Funciona mesmo sem dependências instaladas (graceful degradation).

Uso:
    python scripts/test_setup.py
"""

import sys
import os
from pathlib import Path
import subprocess


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists and report status."""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False


def check_directory_exists(dir_path: str, description: str) -> bool:
    """Check if a directory exists and report status."""
    if Path(dir_path).is_dir():
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path} - NOT FOUND")
        return False


def check_python_import(module_name: str, description: str) -> bool:
    """Check if a Python module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError:
        print(f"⚠️ {description}: {module_name} - NOT AVAILABLE (optional)")
        return False


def validate_toml_syntax() -> bool:
    """Validate pyproject.toml syntax."""
    try:
        import toml
        config = toml.load('pyproject.toml')
        project_name = config['tool']['poetry']['name']
        python_version = config['tool']['poetry']['dependencies']['python']
        print(f"✅ pyproject.toml syntax valid - Project: {project_name}, Python: {python_version}")
        return True
    except ImportError:
        print("⚠️ toml module not available - skipping syntax validation")
        return True
    except Exception as e:
        print(f"❌ pyproject.toml syntax error: {e}")
        return False


def check_git_repository() -> bool:
    """Check if we're in a git repository."""
    try:
        subprocess.run(['git', 'status'], 
                      capture_output=True, check=True, text=True)
        print("✅ Git repository detected")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ Not in a git repository (optional for template)")
        return True


def run_validation_tests() -> dict:
    """Run all validation tests and return results."""
    
    print("🧪 TDD Project Template - Setup Validation")
    print("=" * 50)
    
    results = {
        'core_files': [],
        'directories': [],
        'python_modules': [],
        'configurations': []
    }
    
    # Core files validation
    print("\n📁 Core Files:")
    core_files = [
        ('pyproject.toml', 'Poetry configuration'),
        ('requirements.txt', 'Pip fallback dependencies'),
        ('README.md', 'Project documentation'),
        ('scripts/commit_helper.py', 'TDD commit helper'),
        ('scripts/visualization/tdd_gantt_tracker.py', 'TDD Gantt tracker'),
        ('docs/index.md', 'Jekyll homepage'),
        ('docs/_config.yml', 'Jekyll configuration'),
        ('docs/Gemfile', 'Ruby dependencies'),
        ('.github/workflows/update-tdd-gantt.yml', 'GitHub Actions workflow'),
        ('docs/TDD_COMMIT_PATTERNS.md', 'TDD patterns documentation'),
    ]
    
    for file_path, description in core_files:
        result = check_file_exists(file_path, description)
        results['core_files'].append((file_path, result))
    
    # Directories validation
    print("\n📂 Directories:")
    directories = [
        ('scripts', 'Scripts directory'),
        ('scripts/visualization', 'Visualization scripts'),
        ('docs', 'Documentation directory'),
        ('.github/workflows', 'GitHub Actions workflows'),
        ('epics', 'Epic JSON files'),
    ]
    
    for dir_path, description in directories:
        result = check_directory_exists(dir_path, description)
        results['directories'].append((dir_path, result))
    
    # Python modules validation
    print("\n🐍 Python Dependencies:")
    python_modules = [
        ('sys', 'Python standard library'),
        ('pathlib', 'Path handling'),
        ('subprocess', 'Process execution'),
        ('re', 'Regular expressions'),
        ('datetime', 'Date/time handling'),
        ('json', 'JSON parsing'),
        ('argparse', 'CLI argument parsing'),
        ('plotly', 'Plotly visualization (optional)'),
        ('pandas', 'Data manipulation (optional)'),
        ('numpy', 'Numerical computing (optional)'),
        ('yaml', 'YAML parsing (optional)'),
        ('git', 'GitPython (optional)'),
        ('toml', 'TOML parsing (optional)'),
    ]
    
    for module_name, description in python_modules:
        result = check_python_import(module_name, description)
        results['python_modules'].append((module_name, result))
    
    # Configuration validation
    print("\n⚙️ Configuration:")
    config_tests = [
        ('pyproject.toml syntax', validate_toml_syntax),
        ('Git repository', check_git_repository),
    ]
    
    for test_name, test_func in config_tests:
        result = test_func()
        results['configurations'].append((test_name, result))
        
    return results


def generate_summary_report(results: dict) -> None:
    """Generate summary report of validation results."""
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for category, tests in results.items():
        category_passed = sum(1 for _, result in tests if result)
        category_total = len(tests)
        total_tests += category_total
        passed_tests += category_passed
        
        status = "✅" if category_passed == category_total else "⚠️"
        print(f"{status} {category.replace('_', ' ').title()}: {category_passed}/{category_total}")
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All validations passed! Template is ready to use.")
        print("\n💡 Quick Start:")
        print("   1. poetry install  # Install dependencies")
        print("   2. python scripts/commit_helper.py --guide  # Learn TDD patterns")
        print("   3. Start coding with TDD methodology!")
    else:
        missing_critical = any(
            not result for file_path, result in results['core_files'] 
            if 'pyproject.toml' in file_path or 'tdd_gantt_tracker.py' in file_path
        )
        
        if missing_critical:
            print("❌ Critical files missing! Template setup incomplete.")
            return
        else:
            print("⚠️ Some optional components missing, but core template is functional.")
            print("\n💡 To complete setup:")
            print("   1. poetry install  # Install missing Python dependencies")
            print("   2. Check missing files listed above")
            print("   3. Run test again: python scripts/test_setup.py")


def main():
    """Main validation function."""
    
    # Change to script directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    try:
        results = run_validation_tests()
        generate_summary_report(results)
        
        # Return appropriate exit code
        all_critical_passed = all(
            result for file_path, result in results['core_files']
            if any(critical in file_path for critical in ['pyproject.toml', 'commit_helper.py'])
        )
        
        return 0 if all_critical_passed else 1
        
    except KeyboardInterrupt:
        print("\n❌ Validation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error during validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())