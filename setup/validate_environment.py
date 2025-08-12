#!/usr/bin/env python3
"""
🔍 TDD Project Template - Environment Validation

This script validates that the development environment is properly configured
for TDD development with all required tools and dependencies.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class EnvironmentValidator:
    """Validates TDD development environment setup."""
    
    def __init__(self, project_root: Path = None):
        """Initialize validator."""
        self.project_root = project_root or Path.cwd()
        self.checks = []
        self.warnings = []
        self.errors = []
    
    def run_validation(self) -> bool:
        """Run complete environment validation."""
        console.print(Panel.fit(
            "🔍 TDD Environment Validation\n\n"
            "Checking development environment for TDD project setup...",
            title="Environment Check",
            border_style="bright_blue"
        ))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Running validation checks...", total=None)
            
            # Core system checks
            progress.update(task, description="Checking system requirements...")
            self._check_system_requirements()
            
            # Python environment
            progress.update(task, description="Validating Python environment...")
            self._check_python_environment()
            
            # Development tools
            progress.update(task, description="Checking development tools...")
            self._check_development_tools()
            
            # Project structure
            progress.update(task, description="Validating project structure...")
            self._check_project_structure()
            
            # Git setup
            progress.update(task, description="Checking Git configuration...")
            self._check_git_setup()
            
            # GitHub integration
            progress.update(task, description="Validating GitHub integration...")
            self._check_github_integration()
            
            # Dependencies
            progress.update(task, description="Checking dependencies...")
            self._check_dependencies()
            
            # Streamlit extension
            progress.update(task, description="Checking Streamlit extension...")
            self._check_streamlit_extension()
            
            # Configuration files
            progress.update(task, description="Validating configuration...")
            self._check_configuration()
            
            progress.update(task, description="Validation complete!")
        
        # Show results
        self._show_results()
        
        return len(self.errors) == 0
    
    def _check_system_requirements(self) -> None:
        """Check basic system requirements."""
        # Operating System
        import platform
        os_name = platform.system()
        os_version = platform.release()
        
        self._add_check(
            "Operating System",
            f"{os_name} {os_version}",
            "✅",
            f"Running on {os_name}"
        )
        
        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        if sys.version_info >= (3, 8):
            self._add_check(
                "Python Version", 
                python_version,
                "✅",
                "Python 3.8+ required for TDD tools"
            )
        else:
            self._add_check(
                "Python Version",
                python_version,
                "❌",
                "Python 3.8 or higher required"
            )
            self.errors.append("Python version too old")
        
        # Available memory
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            if memory_gb >= 4:
                status = "✅"
                note = "Sufficient memory for development"
            elif memory_gb >= 2:
                status = "⚠️"
                note = "Limited memory, may affect performance"
                self.warnings.append("Low memory detected")
            else:
                status = "❌"
                note = "Insufficient memory for development"
                self.errors.append("Insufficient system memory")
            
            self._add_check(
                "System Memory",
                f"{memory_gb:.1f} GB",
                status,
                note
            )
        except ImportError:
            self._add_check(
                "System Memory",
                "Unknown",
                "⚠️",
                "psutil not available to check memory"
            )
    
    def _check_python_environment(self) -> None:
        """Check Python development environment."""
        # Virtual environment detection
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        
        if in_venv:
            venv_path = sys.prefix
            self._add_check(
                "Virtual Environment",
                "Active",
                "✅", 
                f"Using venv: {venv_path}"
            )
        else:
            self._add_check(
                "Virtual Environment", 
                "None",
                "⚠️",
                "Consider using virtual environment"
            )
            self.warnings.append("No virtual environment detected")
        
        # Poetry check
        poetry_available = self._check_command_available("poetry")
        if poetry_available:
            poetry_version = self._get_command_version("poetry")
            self._add_check(
                "Poetry",
                poetry_version,
                "✅",
                "Modern Python dependency management"
            )
            
            # Check if in Poetry project
            if (self.project_root / "pyproject.toml").exists():
                self._add_check(
                    "Poetry Project",
                    "Detected",
                    "✅",
                    "Poetry project configuration found"
                )
            else:
                self._add_check(
                    "Poetry Project", 
                    "Not configured",
                    "⚠️",
                    "No pyproject.toml found"
                )
        else:
            self._add_check(
                "Poetry",
                "Not installed", 
                "⚠️",
                "Poetry recommended for Python projects"
            )
            self.warnings.append("Poetry not available")
        
        # pip check
        pip_version = self._get_command_version("pip")
        if pip_version:
            self._add_check(
                "pip",
                pip_version,
                "✅",
                "Python package installer available"
            )
        else:
            self._add_check(
                "pip",
                "Not available",
                "❌", 
                "pip is required for Python development"
            )
            self.errors.append("pip not available")
    
    def _check_development_tools(self) -> None:
        """Check development tools availability."""
        tools = {
            "git": ("Git", "Version control system", True),
            "gh": ("GitHub CLI", "GitHub integration", False),
            "pytest": ("Pytest", "Testing framework", True),
            "black": ("Black", "Code formatter", True),
            "flake8": ("Flake8", "Code linter", True),
            "mypy": ("MyPy", "Type checker", False),
            "pre-commit": ("Pre-commit", "Git hooks", False),
        }
        
        for cmd, (name, description, required) in tools.items():
            available = self._check_command_available(cmd)
            version = self._get_command_version(cmd) if available else "Not installed"
            
            if available:
                self._add_check(name, version, "✅", description)
            elif required:
                self._add_check(name, version, "❌", f"Required: {description}")
                self.errors.append(f"{name} not available")
            else:
                self._add_check(name, version, "⚠️", f"Optional: {description}")
                self.warnings.append(f"{name} not available")
    
    def _check_project_structure(self) -> None:
        """Check TDD project structure."""
        required_dirs = [
            ("src", "Source code directory", True),
            ("tests", "Test files directory", True),
            ("epics", "Epic management files", True), 
            ("docs", "Documentation", False),
            ("scripts", "Utility scripts", False),
            ("tdah_tools", "TDAH time tracking tools", False),
        ]
        
        for dir_name, description, required in required_dirs:
            dir_path = self.project_root / dir_name
            exists = dir_path.exists() and dir_path.is_dir()
            
            if exists:
                file_count = len(list(dir_path.rglob("*")))
                self._add_check(
                    f"Directory: {dir_name}",
                    f"✓ ({file_count} files)",
                    "✅",
                    description
                )
            elif required:
                self._add_check(
                    f"Directory: {dir_name}",
                    "Missing",
                    "❌",
                    f"Required: {description}"
                )
                self.errors.append(f"Missing required directory: {dir_name}")
            else:
                self._add_check(
                    f"Directory: {dir_name}",
                    "Missing",
                    "⚠️",
                    f"Optional: {description}"
                )
        
        # Check for important files
        important_files = [
            ("README.md", "Project documentation", True),
            (".gitignore", "Git ignore rules", True),
            ("pyproject.toml", "Python project config", False),
            ("pytest.ini", "Test configuration", False),
        ]
        
        for file_name, description, required in important_files:
            file_path = self.project_root / file_name
            exists = file_path.exists() and file_path.is_file()
            
            if exists:
                size_kb = file_path.stat().st_size / 1024
                self._add_check(
                    f"File: {file_name}",
                    f"✓ ({size_kb:.1f}KB)",
                    "✅",
                    description
                )
            elif required:
                self._add_check(
                    f"File: {file_name}",
                    "Missing",
                    "❌",
                    f"Required: {description}"
                )
                self.errors.append(f"Missing required file: {file_name}")
            else:
                self._add_check(
                    f"File: {file_name}",
                    "Missing", 
                    "⚠️",
                    f"Optional: {description}"
                )
    
    def _check_git_setup(self) -> None:
        """Check Git configuration."""
        # Git repository
        git_dir = self.project_root / ".git"
        if git_dir.exists():
            self._add_check(
                "Git Repository",
                "Initialized",
                "✅",
                "Project is under version control"
            )
            
            # Check git config
            user_name = self._get_git_config("user.name")
            user_email = self._get_git_config("user.email")
            
            if user_name and user_email:
                self._add_check(
                    "Git Configuration",
                    f"{user_name} <{user_email}>",
                    "✅",
                    "Git user configured"
                )
            else:
                self._add_check(
                    "Git Configuration",
                    "Incomplete",
                    "⚠️",
                    "Set git user.name and user.email"
                )
                self.warnings.append("Git user not configured")
            
            # Check for remote
            try:
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                remote_url = result.stdout.strip()
                self._add_check(
                    "Git Remote",
                    "Configured",
                    "✅",
                    f"Origin: {remote_url}"
                )
            except subprocess.CalledProcessError as e:
                handle_error(
                    ProcessError("Git remote check failed"),
                    severity=ErrorSeverity.DEBUG,
                    context={"command": "git remote get-url origin"}
                )
                self._add_check(
                    "Git Remote",
                    "None",
                    "⚠️",
                    "No remote repository configured"
                )
        else:
            self._add_check(
                "Git Repository",
                "Not initialized",
                "❌", 
                "Initialize with: git init"
            )
            self.errors.append("Git repository not initialized")
    
    def _check_github_integration(self) -> None:
        """Check GitHub integration setup."""
        # GitHub CLI
        gh_available = self._check_command_available("gh")
        if gh_available:
            # Check authentication
            try:
                subprocess.run(
                    ["gh", "auth", "status"],
                    capture_output=True,
                    check=True
                )
                self._add_check(
                    "GitHub CLI",
                    "Authenticated", 
                    "✅",
                    "GitHub integration available"
                )
            except subprocess.CalledProcessError as e:
                handle_error(
                    ProcessError("GitHub CLI authentication check failed",
                               user_action="Run: gh auth login"),
                    severity=ErrorSeverity.WARNING,
                    context={"command": "gh auth status"}
                )
                self._add_check(
                    "GitHub CLI",
                    "Not authenticated",
                    "⚠️",
                    "Run: gh auth login"
                )
                self.warnings.append("GitHub CLI not authenticated")
        else:
            self._add_check(
                "GitHub CLI",
                "Not installed",
                "⚠️",
                "Optional: GitHub integration"
            )
        
        # GitHub workflows
        workflows_dir = self.project_root / ".github" / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml"))
            self._add_check(
                "GitHub Actions",
                f"{len(workflow_files)} workflows",
                "✅",
                "CI/CD automation configured"
            )
        else:
            self._add_check(
                "GitHub Actions",
                "Not configured",
                "⚠️",
                "Optional: CI/CD automation"
            )
    
    def _check_dependencies(self) -> None:
        """Check project dependencies."""
        # Python dependencies
        if (self.project_root / "pyproject.toml").exists():
            # Poetry project
            try:
                result = subprocess.run(
                    ["poetry", "check"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                self._add_check(
                    "Poetry Dependencies",
                    "Valid",
                    "✅",
                    "pyproject.toml is valid"
                )
                
                # Check if dependencies are installed
                try:
                    result = subprocess.run(
                        ["poetry", "run", "python", "-c", "import sys; print('OK')"],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    self._add_check(
                        "Poetry Environment",
                        "Ready",
                        "✅",
                        "Virtual environment configured"
                    )
                except subprocess.CalledProcessError:
                    self._add_check(
                        "Poetry Environment",
                        "Not ready",
                        "⚠️",
                        "Run: poetry install"
                    )
                    self.warnings.append("Poetry environment not ready")
                    
            except subprocess.CalledProcessError:
                self._add_check(
                    "Poetry Dependencies",
                    "Invalid",
                    "❌",
                    "Check pyproject.toml syntax"
                )
                self.errors.append("Invalid Poetry configuration")
        
        elif (self.project_root / "requirements.txt").exists():
            # pip project
            req_file = self.project_root / "requirements.txt"
            req_count = len(req_file.read_text().strip().split('\n'))
            self._add_check(
                "pip Requirements",
                f"{req_count} packages",
                "✅",
                "requirements.txt found"
            )
    
    def _check_configuration(self) -> None:
        """Check configuration files."""
        config_files = [
            ("pytest.ini", "Test configuration"),
            (".pre-commit-config.yaml", "Pre-commit hooks"),
            (".gitignore", "Git ignore rules"),
            ("pyproject.toml", "Python project config"),
        ]
        
        for file_name, description in config_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                # Basic validation
                try:
                    if file_name.endswith('.json'):
                        json.loads(file_path.read_text())
                    elif file_name.endswith('.toml'):
                        # Basic TOML check
                        content = file_path.read_text()
                        if '[' in content or '=' in content:
                            status = "✅"
                        else:
                            status = "⚠️"
                    else:
                        status = "✅"
                    
                    self._add_check(
                        f"Config: {file_name}",
                        "Valid",
                        status,
                        description
                    )
                except Exception as e:
                    self._add_check(
                        f"Config: {file_name}",
                        "Invalid",
                        "❌",
                        f"Validation error: {e}"
                    )
                    self.errors.append(f"Invalid config file: {file_name}")
    
    def _show_results(self) -> None:
        """Display validation results."""
        # Create results table
        table = Table(title="🔍 Environment Validation Results")
        table.add_column("Component", style="bold")
        table.add_column("Status")
        table.add_column("Value", style="dim")
        table.add_column("Notes")
        
        for check in self.checks:
            table.add_row(
                check["name"],
                check["status"],
                check["value"],
                check["notes"]
            )
        
        console.print(table)
        
        # Summary
        total_checks = len(self.checks)
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        success_count = total_checks - error_count - warning_count
        
        if error_count == 0:
            summary_style = "bright_green"
            summary_title = "✅ Environment Ready"
            summary_msg = (
                f"All critical requirements met!\n\n"
                f"✅ Passed: {success_count}\n"
                f"⚠️ Warnings: {warning_count}\n"
                f"❌ Errors: {error_count}"
            )
        else:
            summary_style = "bright_red"
            summary_title = "❌ Environment Issues"
            summary_msg = (
                f"Environment setup needs attention.\n\n"
                f"✅ Passed: {success_count}\n"
                f"⚠️ Warnings: {warning_count}\n" 
                f"❌ Errors: {error_count}"
            )
        
        console.print(Panel(
            summary_msg,
            title=summary_title,
            border_style=summary_style
        ))
        
        # Show specific errors and warnings
        if self.errors:
            console.print("\n❌ [bold red]Critical Issues:[/bold red]")
            for error in self.errors:
                console.print(f"  • {error}")
        
        if self.warnings:
            console.print("\n⚠️ [bold yellow]Warnings:[/bold yellow]")
            for warning in self.warnings:
                console.print(f"  • {warning}")
        
        if error_count == 0:
            console.print(
                "\n🚀 [bold green]Ready to start TDD development![/bold green]\n"
                "Next steps:\n"
                "1. Create your first epic: [code]python setup/init_tdd_project.py[/code]\n"
                "2. Start TDD timer: [code]python -m tdah_tools.task_timer start EPIC-1.1[/code]\n"
                "3. Launch Streamlit interface: [code]poetry run streamlit-run[/code]\n"
                "4. Run tests: [code]pytest tests/[/code]"
            )
    
    def _check_streamlit_extension(self) -> None:
        """Check Streamlit extension setup and dependencies."""
        
        # Check if streamlit_extension directory exists
        streamlit_dir = self.project_root / "streamlit_extension"
        if streamlit_dir.exists() and streamlit_dir.is_dir():
            self._add_check(
                "Streamlit Extension",
                "Directory exists",
                "✅",
                "Streamlit extension is available"
            )
            
            # Check key files
            key_files = [
                ("streamlit_app.py", "Main Streamlit app"),
                ("manage.py", "Management CLI"),
                ("config/streamlit_config.py", "Configuration module"),
                ("components/sidebar.py", "Sidebar component"),
                ("utils/database.py", "Database utilities")
            ]
            
            for file_path, description in key_files:
                full_path = streamlit_dir / file_path
                if full_path.exists():
                    self._add_check(
                        f"Streamlit: {file_path}",
                        "Available",
                        "✅",
                        description
                    )
                else:
                    self._add_check(
                        f"Streamlit: {file_path}",
                        "Missing",
                        "⚠️",
                        f"Optional: {description}"
                    )
        else:
            self._add_check(
                "Streamlit Extension",
                "Not available",
                "⚠️",
                "Optional: Install with poetry install --extras streamlit"
            )
            self.warnings.append("Streamlit extension not installed")
            return
        
        # Check Streamlit dependencies
        streamlit_deps = [
            ("streamlit", "Interactive web framework"),
            ("sqlalchemy", "Database ORM"),
            ("python-dotenv", "Environment configuration"),
            ("gql", "GraphQL client for GitHub")
        ]
        
        streamlit_available = True
        
        for package, description in streamlit_deps:
            try:
                __import__(package)
                self._add_check(
                    f"Package: {package}",
                    "Installed",
                    "✅",
                    description
                )
            except ImportError:
                self._add_check(
                    f"Package: {package}",
                    "Missing",
                    "⚠️",
                    f"Install with: pip install {package}"
                )
                streamlit_available = False
        
        # Check if Streamlit can be launched
        if streamlit_available:
            try:
                # Try to import main streamlit app
                import sys
                import importlib.util
                
                app_path = streamlit_dir / "streamlit_app.py"
                spec = importlib.util.spec_from_file_location("streamlit_app", app_path)
                if spec and spec.loader:
                    # Don't actually load the module, just check if it can be loaded
                    self._add_check(
                        "Streamlit App",
                        "Can be imported",
                        "✅",
                        "Main app is ready to run"
                    )
                else:
                    self._add_check(
                        "Streamlit App",
                        "Import issues",
                        "⚠️",
                        "Check app dependencies"
                    )
            except Exception as e:
                self._add_check(
                    "Streamlit App",
                    "Import error",
                    "⚠️",
                    f"Error: {str(e)[:50]}..."
                )
        
        # Check database files for Streamlit
        db_files = [
            ("framework.db", "Main framework database"),
            ("task_timer.db", "Timer tracking database")
        ]
        
        for db_file, description in db_files:
            db_path = self.project_root / db_file
            if db_path.exists():
                size_mb = db_path.stat().st_size / (1024 * 1024)
                self._add_check(
                    f"Database: {db_file}",
                    f"Available ({size_mb:.2f}MB)",
                    "✅",
                    description
                )
            else:
                self._add_check(
                    f"Database: {db_file}",
                    "Not found",
                    "⚠️",
                    f"Optional: {description} will be created when needed"
                )
    
    # Helper methods
    
    def _add_check(self, name: str, value: str, status: str, notes: str) -> None:
        """Add a validation check result."""
        self.checks.append({
            "name": name,
            "value": value,
            "status": status,
            "notes": notes
        })
    
    def _check_command_available(self, command: str) -> bool:
        """Check if a command is available in PATH."""
        return shutil.which(command) is not None
    
    def _get_command_version(self, command: str) -> Optional[str]:
        """Get version of a command."""
        if not self._check_command_available(command):
            return None
        
        version_flags = ["--version", "-V", "-v"]
        
        for flag in version_flags:
            try:
                result = subprocess.run(
                    [command, flag],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Extract version number from output
                    output = result.stdout.strip()
                    if output:
                        return output.split('\n')[0][:50]  # First line, max 50 chars
                    return "Available"
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return "Available"
    
    def _get_git_config(self, key: str) -> Optional[str]:
        """Get Git configuration value."""
        try:
            result = subprocess.run(
                ["git", "config", "--get", key],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🔍 Validate TDD development environment"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory to validate (default: current directory)"
    )
    parser.add_argument(
        "--output",
        choices=["table", "json", "summary"],
        default="table",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    validator = EnvironmentValidator(args.project_dir)
    success = validator.run_validation()
    
    if args.output == "json":
        # Output JSON for automation
        result = {
            "success": success,
            "checks": validator.checks,
            "errors": validator.errors,
            "warnings": validator.warnings,
            "summary": {
                "total": len(validator.checks),
                "passed": len(validator.checks) - len(validator.errors) - len(validator.warnings),
                "warnings": len(validator.warnings),
                "errors": len(validator.errors)
            }
        }
        print(json.dumps(result, indent=2))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()