#!/usr/bin/env python3
"""
🧙‍♂️ TDD Project Template - Interactive Setup Wizard

This script helps you initialize a new TDD project with all the necessary
components, configurations, and best practices pre-configured.

Features:
- Detects project type (Python, Node.js, etc.)
- Interactive configuration wizard
- GitHub repository setup
- Epic template generation
- Environment validation
- Development tools setup
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import standardized error handling
sys.path.append(str(Path(__file__).parent.parent))
from tdah_tools.error_handler import (
    get_error_handler, handle_error, log_info, log_warning, log_error,
    ValidationError, ConfigurationError, DependencyError, ProcessError,
    FileSystemError, GitError, ErrorSeverity
)

try:
    import click
    import rich
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("❌ Missing dependencies. Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "click", "rich"])
    import click
    import rich
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class TDDProjectWizard:
    """Interactive wizard for TDD project setup."""
    
    def __init__(self, non_interactive: bool = False):
        """Initialize the wizard."""
        self.config = {}
        self.project_root = Path.cwd()
        self.template_root = Path(__file__).parent.parent
        self.non_interactive = non_interactive
        
    def run(self) -> bool:
        """Run the complete setup wizard."""
        console.print(Panel.fit(
            "🎯 TDD Project Template Setup Wizard\n\n"
            "This wizard will help you create a new TDD project with:\n"
            "• Epic-based project management\n"
            "• Automated testing workflow\n"
            "• Time tracking for TDAH optimization\n"
            "• Interactive visualizations\n"
            "• GitHub integration",
            title="🧙‍♂️ Welcome",
            border_style="bright_blue"
        ))
        
        try:
            # Step 1: Collect project information
            if not self._collect_project_info():
                return False
            
            # Step 2: Detect and configure project type
            if not self._configure_project_type():
                return False
            
            # Step 3: Setup GitHub integration
            if not self._setup_github_integration():
                return False
            
            # Step 4: Create project structure
            if not self._create_project_structure():
                return False
            
            # Step 5: Generate initial epic
            if not self._generate_initial_epic():
                return False
            
            # Step 6: Setup development environment
            if not self._setup_development_environment():
                return False
            
            # Step 7: Initialize Git and GitHub
            if not self._initialize_git_repo():
                return False
            
            # Step 8: Final validation
            if not self._validate_setup():
                return False
            
            self._show_success_message()
            return True
            
        except KeyboardInterrupt:
            log_info("Setup cancelled by user")
            console.print("\n❌ Setup cancelled by user.")
            return False
        except Exception as e:
            error_report = handle_error(
                exception=e,
                user_action="Check setup requirements and try again",
                context={"step": "wizard_execution", "project_root": str(self.project_root)}
            )
            console.print(f"\n❌ Setup failed: {error_report.message}")
            return False
    
    def _collect_project_info(self) -> bool:
        """Collect basic project information."""
        if not self.non_interactive:
            console.print("\n📋 Project Information", style="bold blue")
        
        # Project name
        default_name = self.project_root.name
        if self.non_interactive:
            project_name = default_name
            console.print(f"Using project name: {project_name}")
        else:
            project_name = Prompt.ask(
                "Project name",
                default=default_name
            )
        
        # Author information
        default_author = self._get_git_config("user.name") or "Your Name"
        if self.non_interactive:
            author_name = default_author
            console.print(f"Using author name: {author_name}")
        else:
            author_name = Prompt.ask(
                "Author name",
                default=default_author
            )
        
        default_email = self._get_git_config("user.email") or "your.email@example.com"
        if self.non_interactive:
            author_email = default_email
            console.print(f"Using author email: {author_email}")
        else:
            author_email = Prompt.ask(
                "Author email",
                default=default_email
            )
        
        # Project description
        default_description = f"TDD project: {project_name}"
        if self.non_interactive:
            description = default_description
            console.print(f"Using description: {description}")
        else:
            description = Prompt.ask(
                "Project description",
                default=default_description
            )
        
        # GitHub username
        default_github = self._guess_github_username(author_email)
        if self.non_interactive:
            github_username = default_github
            console.print(f"Using GitHub username: {github_username}")
        else:
            github_username = Prompt.ask(
                "GitHub username",
                default=default_github
            )
        
        self.config.update({
            "project_name": project_name,
            "author_name": author_name,
            "author_email": author_email,
            "description": description,
            "github_username": github_username,
            "repository_name": project_name.lower().replace(" ", "-"),
            "created_date": datetime.now().strftime("%Y-%m-%d")
        })
        
        return True
    
    def _configure_project_type(self) -> bool:
        """Detect and configure project type."""
        if not self.non_interactive:
            console.print("\n🔍 Project Type Detection", style="bold blue")
        
        # Auto-detect project type
        detected_type = self._detect_project_type()
        
        # Show options
        project_types = {
            "python": "🐍 Python (with Poetry)",
            "python-pip": "🐍 Python (with pip)", 
            "node": "📦 Node.js (with npm)",
            "mixed": "🔀 Mixed (Python + Node.js)",
            "other": "❓ Other/Generic"
        }
        
        if self.non_interactive:
            # Use detected type or default to Python with Poetry
            selected_type = detected_type or "python"
            console.print(f"Using project type: {project_types.get(selected_type, 'Unknown')} ({selected_type})")
        else:
            console.print(f"Detected project type: [bold]{project_types.get(detected_type, 'Unknown')}[/bold]")
            
            # Ask for confirmation or selection
            if detected_type and Confirm.ask(f"Use detected type ({detected_type})?"):
                selected_type = detected_type
            else:
                console.print("\nAvailable project types:")
                for key, desc in project_types.items():
                    console.print(f"  {key}: {desc}")
                
                selected_type = Prompt.ask(
                    "Select project type",
                    choices=list(project_types.keys()),
                    default="python"
                )
        
        self.config["project_type"] = selected_type
        
        # Configure language-specific settings
        if selected_type.startswith("python"):
            self._configure_python_settings(selected_type)
        elif selected_type == "node":
            self._configure_node_settings()
        elif selected_type == "mixed":
            self._configure_python_settings("python")
            self._configure_node_settings()
        
        return True
    
    def _configure_python_settings(self, python_type: str) -> None:
        """Configure Python-specific settings."""
        if self.non_interactive:
            python_version = "3.11"
            test_framework = "pytest"
            console.print(f"Using Python {python_version} with {test_framework}")
        else:
            python_version = Prompt.ask("Python version", default="3.11")
            test_framework = Prompt.ask(
                "Test framework",
                choices=["pytest", "unittest"],
                default="pytest"
            )
        
        self.config["python"] = {
            "version": python_version,
            "use_poetry": python_type == "python",
            "test_framework": test_framework
        }
    
    def _configure_node_settings(self) -> None:
        """Configure Node.js-specific settings."""
        if self.non_interactive:
            node_version = "18"
            package_manager = "npm"
            test_framework = "jest"
            console.print(f"Using Node.js {node_version} with {package_manager} and {test_framework}")
        else:
            node_version = Prompt.ask("Node.js version", default="18")
            package_manager = Prompt.ask(
                "Package manager",
                choices=["npm", "yarn", "pnpm"],
                default="npm"
            )
            test_framework = Prompt.ask(
                "Test framework", 
                choices=["jest", "mocha", "vitest"],
                default="jest"
            )
        
        self.config["node"] = {
            "version": node_version,
            "package_manager": package_manager,
            "test_framework": test_framework
        }
    
    def _setup_github_integration(self) -> bool:
        """Setup GitHub integration."""
        if not self.non_interactive:
            console.print("\n🐙 GitHub Integration", style="bold blue")
        
        if self.non_interactive:
            enable_github = True
            console.print("Enabling GitHub integration (default)")
        else:
            enable_github = Confirm.ask("Enable GitHub integration?", default=True)
        
        if not enable_github:
            self.config["github_enabled"] = False
            return True
        
        self.config["github_enabled"] = True
        
        # GitHub Pages
        if self.non_interactive:
            enable_pages = True
            console.print("Enabling GitHub Pages dashboard (default)")
        else:
            enable_pages = Confirm.ask("Enable GitHub Pages dashboard?", default=True)
        self.config["github_pages"] = enable_pages
        
        # GitHub Actions
        if self.non_interactive:
            enable_actions = True
            console.print("Enabling GitHub Actions automation (default)")
        else:
            enable_actions = Confirm.ask("Enable GitHub Actions automation?", default=True)
        self.config["github_actions"] = enable_actions
        
        # Repository creation
        if self.non_interactive:
            create_repo = False  # Don't auto-create repos in non-interactive mode for safety
            console.print("Skipping automatic repository creation (non-interactive mode)")
        else:
            create_repo = Confirm.ask("Create GitHub repository automatically?", default=False)
        self.config["create_github_repo"] = create_repo
        
        if create_repo:
            # Check GitHub CLI
            if not self._check_github_cli():
                console.print("⚠️ GitHub CLI not found. Repository creation will be skipped.")
                self.config["create_github_repo"] = False
        
        return True
    
    def _create_project_structure(self) -> bool:
        """Create the project directory structure."""
        console.print("\n📁 Creating Project Structure", style="bold blue")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Setting up directories...", total=None)
            
            # Create core directories
            directories = [
                "src", "tests", "epics", "scripts", "docs", 
                "config", "data", "logs", "output"
            ]
            
            if self.config.get("python", {}).get("use_poetry"):
                directories.append("tdah_tools")
            
            for directory in directories:
                (self.project_root / directory).mkdir(exist_ok=True)
            
            progress.update(task, description="Copying template files...")
            
            # Copy template files based on project type
            self._copy_template_files()
            
            progress.update(task, description="Customizing configurations...")
            
            # Customize configuration files
            self._customize_config_files()
            
            progress.update(task, description="Project structure created!")
        
        return True
    
    def _copy_template_files(self) -> None:
        """Copy appropriate template files based on project type."""
        project_type = self.config["project_type"]
        
        # Copy core template files
        core_files = [
            ".gitignore",
            "README_TEMPLATE.md",
            "CHANGELOG.md"
        ]
        
        for file in core_files:
            src = self.template_root / file
            if src.exists():
                shutil.copy2(src, self.project_root / file.replace("_TEMPLATE", ""))
        
        # Copy project-type specific files
        if project_type.startswith("python"):
            self._copy_python_files()
        
        if project_type in ["node", "mixed"]:
            self._copy_node_files()
        
        # Copy shared files
        shared_dirs = ["scripts", "tdah_tools", ".github"]
        for dir_name in shared_dirs:
            src_dir = self.template_root / dir_name
            if src_dir.exists():
                dest_dir = self.project_root / dir_name
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                shutil.copytree(src_dir, dest_dir)
    
    def _copy_python_files(self) -> None:
        """Copy Python-specific template files."""
        python_config = self.config.get("python", {})
        
        if python_config.get("use_poetry"):
            # Copy Poetry configuration
            shutil.copy2(
                self.template_root / "config" / "python" / "pyproject_poetry.toml",
                self.project_root / "pyproject.toml"
            )
        else:
            # Copy pip configuration
            shutil.copy2(
                self.template_root / "config" / "python" / "requirements.txt",
                self.project_root / "requirements.txt"
            )
        
        # Copy pytest configuration
        shutil.copy2(
            self.template_root / "config" / "python" / "pytest.ini",
            self.project_root / "pytest.ini"
        )
    
    def _copy_node_files(self) -> None:
        """Copy Node.js-specific template files."""
        shutil.copy2(
            self.template_root / "config" / "node" / "package.json",
            self.project_root / "package.json"
        )
    
    def _customize_config_files(self) -> None:
        """Customize configuration files with project-specific values."""
        replacements = {
            "[PROJECT_NAME]": self.config["project_name"],
            "[AUTHOR_NAME]": self.config["author_name"],
            "[AUTHOR_EMAIL]": self.config["author_email"],
            "[USERNAME]": self.config["github_username"],
            "[REPOSITORY_NAME]": self.config["repository_name"],
            "[DESCRIPTION]": self.config["description"],
        }
        
        # Files to customize
        files_to_customize = [
            "pyproject.toml",
            "package.json",
            "README.md",
            ".github/workflows/tdd-automation.yml",
            "docs/_config.yml",
            "docs/index.md"
        ]
        
        for file_path in files_to_customize:
            full_path = self.project_root / file_path
            if full_path.exists():
                self._replace_placeholders_in_file(full_path, replacements)
    
    def _replace_placeholders_in_file(self, file_path: Path, replacements: Dict[str, str]) -> None:
        """Replace placeholders in a file with actual values."""
        try:
            content = file_path.read_text(encoding="utf-8")
            
            for placeholder, value in replacements.items():
                content = content.replace(placeholder, value)
            
            file_path.write_text(content, encoding="utf-8")
        except Exception as e:
            handle_error(
                exception=e,
                severity=ErrorSeverity.WARNING,
                user_action=f"Manually check and customize {file_path}",
                context={"file_path": str(file_path), "placeholders": list(replacements.keys())}
            )
            console.print(f"⚠️ Warning: Could not customize {file_path}: {e}")
    
    def _generate_initial_epic(self) -> bool:
        """Generate the first epic for the project."""
        if not self.non_interactive:
            console.print("\n🎯 Creating Initial Epic", style="bold blue")
        
        if self.non_interactive:
            create_epic = True
            console.print("Creating initial project setup epic (default)")
        else:
            create_epic = Confirm.ask("Create initial project setup epic?", default=True)
        
        if not create_epic:
            return True
        
        epic_data = {
            "epic": {
                "id": "EPIC-1",
                "name": "Project Foundation Setup",
                "summary": "Establish TDD project foundation with core infrastructure and initial implementation",
                "tdd_enabled": True,
                "methodology": "Test-Driven Development",
                "goals": [
                    "Setup development environment with TDD workflow",
                    "Implement core project structure and configuration",
                    "Create initial test suite and CI/CD pipeline"
                ],
                "definition_of_done": [
                    "All tests written before implementation",
                    "100% test coverage on new modules",
                    "Red-green-refactor cycle followed consistently",
                    "GitHub Actions workflow configured and passing",
                    "Documentation updated and complete"
                ],
                "duration": "3 days",
                "labels": ["tdd", "foundation", "setup"],
                "tasks": [
                    {
                        "id": "EPIC-1.1",
                        "title": "TEST: Validate project configuration",
                        "tdd_phase": "red",
                        "estimate_minutes": 15,
                        "story_points": 2,
                        "description": "Write tests to validate that project configuration is correct",
                        "test_specs": [
                            "should_load_project_config_successfully",
                            "should_validate_required_dependencies",
                            "should_verify_directory_structure"
                        ],
                        "acceptance_criteria": [
                            "Test fails initially (RED phase)",
                            "Configuration validation logic tested",
                            "Error handling for missing config tested"
                        ],
                        "deliverables": ["tests/test_project_config.py"],
                        "dependencies": [],
                        "branch": "feature/epic-1-foundation",
                        "files_touched": ["tests/test_project_config.py"],
                        "risk": "Configuration complexity",
                        "mitigation": "Keep configuration simple and well-documented"
                    },
                    {
                        "id": "EPIC-1.2", 
                        "title": "IMPL: Create project configuration module",
                        "tdd_phase": "green",
                        "estimate_minutes": 20,
                        "story_points": 3,
                        "description": "Implement minimal project configuration to pass tests",
                        "test_specs": [
                            "should_load_project_config_successfully"
                        ],
                        "acceptance_criteria": [
                            "All RED phase tests now pass",
                            "Configuration module loads successfully",
                            "No existing tests broken"
                        ],
                        "deliverables": [
                            "src/config.py",
                            "tests/test_project_config.py"
                        ],
                        "dependencies": ["EPIC-1.1"],
                        "branch": "feature/epic-1-foundation",
                        "files_touched": ["src/config.py"],
                        "risk": "Over-engineering initial implementation",
                        "mitigation": "Keep implementation minimal, focus on passing tests"
                    },
                    {
                        "id": "EPIC-1.3",
                        "title": "REFACTOR: Optimize configuration structure",
                        "tdd_phase": "refactor",
                        "estimate_minutes": 15,
                        "story_points": 2,
                        "description": "Improve configuration code structure while keeping tests green",
                        "test_specs": [
                            "all_existing_tests_still_pass"
                        ],
                        "acceptance_criteria": [
                            "All tests remain green",
                            "Code is cleaner and more maintainable",
                            "No functionality changes",
                            "Documentation updated"
                        ],
                        "deliverables": [
                            "src/config.py",
                            "docs/configuration.md"
                        ],
                        "dependencies": ["EPIC-1.2"],
                        "branch": "feature/epic-1-foundation", 
                        "files_touched": ["src/config.py"],
                        "risk": "Breaking existing functionality",
                        "mitigation": "Continuous test execution during refactoring"
                    }
                ],
                "checklist_epic_level": [
                    "All tasks follow red-green-refactor cycle",
                    "Test coverage >= 90%",
                    "All tests pass consistently",
                    "Code review completed",
                    "Documentation updated",
                    "CI/CD pipeline passing"
                ],
                "automation_hooks": {
                    "create_labels": ["tdd", "foundation", "setup"],
                    "project_board": {
                        "name": "TDD Development Board",
                        "columns": ["Red (Failing Tests)", "Green (Implementation)", "Refactor", "Done"]
                    },
                    "default_branch": "main",
                    "test_runner": self.config.get("python", {}).get("test_framework", "pytest"),
                    "coverage_threshold": 90,
                    "pre_commit_hooks": ["pytest", "coverage", "black", "flake8"],
                    "milestone": "EPIC 1 - Project Foundation"
                },
                "tdd_guidelines": {
                    "red_phase_rules": [
                        "Write the simplest test that fails",
                        "Test should express desired behavior clearly",
                        "Use descriptive test names",
                        "Keep tests focused and atomic"
                    ],
                    "green_phase_rules": [
                        "Write minimal code to pass the test",
                        "Don't worry about elegance yet", 
                        "Focus on making tests pass",
                        "Run all tests to ensure no regression"
                    ],
                    "refactor_phase_rules": [
                        "Improve design without changing behavior",
                        "Keep all tests green throughout",
                        "Eliminate code duplication",
                        "Improve readability and maintainability"
                    ]
                },
                "quality_gates": {
                    "test_coverage_minimum": 90,
                    "cyclomatic_complexity_max": 10,
                    "test_execution_time_max": "30s",
                    "code_duplication_max": "5%"
                }
            },
            "_metadata": {
                "template_version": "1.0",
                "created_date": self.config["created_date"],
                "description": f"Initial project setup epic for {self.config['project_name']}",
                "usage_instructions": [
                    "1. Follow the red-green-refactor cycle for each task",
                    "2. Start with EPIC-1.1 (RED phase)",
                    "3. Move to EPIC-1.2 (GREEN phase) only after tests fail",
                    "4. Complete with EPIC-1.3 (REFACTOR phase)"
                ]
            }
        }
        
        # Save epic file
        epic_file = self.project_root / "epics" / "epic-1.json"
        with open(epic_file, "w", encoding="utf-8") as f:
            json.dump(epic_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"✅ Created initial epic: {epic_file}")
        return True
    
    def _setup_development_environment(self) -> bool:
        """Setup development environment and dependencies.""" 
        console.print("\n🛠️ Setting Up Development Environment", style="bold blue")
        
        project_type = self.config["project_type"]
        
        # Python setup
        if project_type.startswith("python"):
            return self._setup_python_environment()
        
        # Node.js setup  
        if project_type in ["node", "mixed"]:
            return self._setup_node_environment()
        
        return True
    
    def _setup_python_environment(self) -> bool:
        """Setup Python development environment."""
        python_config = self.config.get("python", {})
        
        if python_config.get("use_poetry"):
            # Check if Poetry is installed
            if not self._check_command("poetry"):
                console.print("⚠️ Poetry not found. Please install Poetry first.")
                console.print("Visit: https://python-poetry.org/docs/#installation")
                return False
            
            # Initialize Poetry project
            if self.non_interactive or Confirm.ask("Initialize Poetry environment?", default=True):
                try:
                    subprocess.run(
                        ["poetry", "install"],
                        cwd=self.project_root,
                        check=True,
                        capture_output=True
                    )
                    console.print("✅ Poetry environment initialized")
                except subprocess.CalledProcessError as e:
                    handle_error(
                        ProcessError("Poetry installation failed", 
                                   user_action="Install Poetry manually: https://python-poetry.org/docs/#installation"),
                        context={"command": "poetry install", "cwd": str(self.project_root)}
                    )
                    console.print("⚠️ Poetry initialization failed")
        else:
            # pip setup
            if self.non_interactive or Confirm.ask("Install Python dependencies with pip?", default=True):
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                        cwd=self.project_root,
                        check=True
                    )
                    console.print("✅ Python dependencies installed")
                except subprocess.CalledProcessError as e:
                    handle_error(
                        ProcessError("Pip installation failed",
                                   user_action="Check requirements.txt and install dependencies manually"),
                        context={"command": "pip install -r requirements.txt", "cwd": str(self.project_root)}
                    )
                    console.print("⚠️ Pip installation failed")
        
        return True
    
    def _setup_node_environment(self) -> bool:
        """Setup Node.js development environment."""
        node_config = self.config.get("node", {})
        package_manager = node_config.get("package_manager", "npm")
        
        if not self._check_command(package_manager):
            console.print(f"⚠️ {package_manager} not found. Please install Node.js first.")
            return False
        
        if self.non_interactive or Confirm.ask(f"Install Node.js dependencies with {package_manager}?", default=True):
            try:
                subprocess.run(
                    [package_manager, "install"],
                    cwd=self.project_root,
                    check=True
                )
                console.print(f"✅ Node.js dependencies installed with {package_manager}")
            except subprocess.CalledProcessError as e:
                handle_error(
                    ProcessError(f"{package_manager} installation failed",
                               user_action=f"Check package.json and install with {package_manager} manually"),
                    context={"package_manager": package_manager, "cwd": str(self.project_root)}
                )
                console.print(f"⚠️ {package_manager} installation failed")
        
        return True
    
    def _initialize_git_repo(self) -> bool:
        """Initialize Git repository and optionally create GitHub repo."""
        console.print("\n📝 Git Repository Setup", style="bold blue")
        
        # Check if already a git repository
        if (self.project_root / ".git").exists():
            console.print("✅ Git repository already exists")
        else:
            if Confirm.ask("Initialize Git repository?", default=True):
                try:
                    subprocess.run(["git", "init"], cwd=self.project_root, check=True)
                    subprocess.run(["git", "add", "."], cwd=self.project_root, check=True)
                    subprocess.run([
                        "git", "commit", "-m", 
                        "🎉 Initial commit: TDD project template setup\n\n"
                        f"- Created {self.config['project_name']} project structure\n"
                        "- Configured TDD workflow with epic management\n"
                        "- Setup automated testing and CI/CD\n\n"
                        "🤖 Generated with TDD Project Template"
                    ], cwd=self.project_root, check=True)
                    
                    console.print("✅ Git repository initialized")
                except subprocess.CalledProcessError as e:
                    handle_error(
                        GitError("Git initialization failed",
                               user_action="Initialize Git repository manually: git init"),
                        context={"cwd": str(self.project_root), "commands": ["git init", "git add .", "git commit"]}
                    )
                    console.print("⚠️ Git initialization failed")
        
        # Create GitHub repository
        if self.config.get("create_github_repo") and self._check_github_cli():
            if Confirm.ask("Create GitHub repository now?", default=True):
                self._create_github_repository()
        
        return True
    
    def _create_github_repository(self) -> bool:
        """Create GitHub repository using GitHub CLI."""
        try:
            repo_name = self.config["repository_name"]
            description = self.config["description"]
            
            cmd = [
                "gh", "repo", "create", repo_name,
                "--description", description,
                "--public",  # Change to --private if needed
                "--source", ".",
                "--remote", "origin",
                "--push"
            ]
            
            subprocess.run(cmd, cwd=self.project_root, check=True)
            console.print(f"✅ GitHub repository created: https://github.com/{self.config['github_username']}/{repo_name}")
            
            return True
        except subprocess.CalledProcessError as e:
            handle_error(
                GitError("GitHub repository creation failed",
                       user_action="Create repository manually on GitHub"),
                context={"repo_name": repo_name, "command": " ".join(cmd)}
            )
            console.print(f"⚠️ Failed to create GitHub repository: {e}")
            return False
    
    def _validate_setup(self) -> bool:
        """Validate the project setup."""
        console.print("\n✅ Validating Setup", style="bold blue")
        
        validation_checks = [
            ("Project structure", self._validate_project_structure),
            ("Configuration files", self._validate_configuration),
            ("Dependencies", self._validate_dependencies),
            ("Git repository", self._validate_git_setup),
        ]
        
        all_valid = True
        
        for check_name, check_func in validation_checks:
            try:
                if check_func():
                    console.print(f"  ✅ {check_name}")
                else:
                    console.print(f"  ❌ {check_name}")
                    all_valid = False
            except Exception as e:
                handle_error(
                    exception=e,
                    severity=ErrorSeverity.WARNING,
                    user_action=f"Check {check_name.lower()} configuration manually",
                    context={"validation_check": check_name}
                )
                console.print(f"  ⚠️ {check_name}: {e}")
                all_valid = False
        
        return all_valid
    
    def _validate_project_structure(self) -> bool:
        """Validate project directory structure."""
        required_dirs = ["src", "tests", "epics", "docs"]
        return all((self.project_root / dir_name).exists() for dir_name in required_dirs)
    
    def _validate_configuration(self) -> bool:
        """Validate configuration files exist."""
        project_type = self.config["project_type"]
        
        if project_type.startswith("python"):
            if self.config.get("python", {}).get("use_poetry"):
                return (self.project_root / "pyproject.toml").exists()
            else:
                return (self.project_root / "requirements.txt").exists()
        
        if project_type in ["node", "mixed"]:
            return (self.project_root / "package.json").exists()
        
        return True
    
    def _validate_dependencies(self) -> bool:
        """Validate dependencies are properly installed."""
        project_type = self.config["project_type"]
        
        if project_type.startswith("python"):
            # Check virtual environment or poetry
            if self.config.get("python", {}).get("use_poetry"):
                return self._check_command("poetry")
            else:
                return True  # Can't easily check pip installs
        
        return True
    
    def _validate_git_setup(self) -> bool:
        """Validate Git setup."""
        return (self.project_root / ".git").exists()
    
    def _show_success_message(self) -> None:
        """Show final success message with next steps."""
        repo_url = f"https://github.com/{self.config['github_username']}/{self.config['repository_name']}"
        pages_url = f"https://{self.config['github_username']}.github.io/{self.config['repository_name']}"
        
        success_panel = Panel(
            f"🎉 [bold green]Setup Complete![/bold green]\n\n"
            f"Your TDD project '[bold]{self.config['project_name']}[/bold]' is ready!\n\n"
            f"📁 Project: {self.project_root}\n"
            f"🐙 GitHub: {repo_url}\n" +
            (f"📄 Dashboard: {pages_url}\n" if self.config.get("github_pages") else "") +
            f"\n🚀 [bold]Next Steps:[/bold]\n"
            f"1. Start your first TDD cycle with EPIC-1\n"
            f"2. Run tests: [code]pytest tests/[/code]\n" + 
            (f"3. Start timer: [code]poetry run tdd-timer start EPIC-1.1[/code]\n" if self.config.get("python", {}).get("use_poetry") else
             f"3. Start timer: [code]python -m tdah_tools.task_timer start EPIC-1.1[/code]\n") +
            f"4. Follow RED → GREEN → REFACTOR cycle\n\n"
            f"📚 Documentation: [code]docs/README.md[/code]\n"
            f"🎯 Epic Management: [code]epics/epic-1.json[/code]",
            title="🎯 Success!",
            border_style="bright_green"
        )
        
        console.print(success_panel)
    
    # Utility methods
    
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
    
    def _guess_github_username(self, email: str) -> str:
        """Guess GitHub username from email."""
        if "@" in email:
            return email.split("@")[0]
        return "your-username"
    
    def _detect_project_type(self) -> Optional[str]:
        """Auto-detect project type from existing files."""
        if (self.project_root / "pyproject.toml").exists():
            return "python"
        elif (self.project_root / "poetry.lock").exists():
            return "python"
        elif (self.project_root / "requirements.txt").exists():
            return "python-pip"
        elif (self.project_root / "package.json").exists():
            return "node"
        elif (self.project_root / "Pipfile").exists():
            return "python-pip"
        elif any(self.project_root.glob("*.py")):
            return "python"
        elif any(self.project_root.glob("*.js")) or any(self.project_root.glob("*.ts")):
            return "node"
        return None
    
    def _check_command(self, command: str) -> bool:
        """Check if a command is available."""
        try:
            subprocess.run(
                [command, "--version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_github_cli(self) -> bool:
        """Check if GitHub CLI is available and authenticated."""
        if not self._check_command("gh"):
            return False
        
        try:
            subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            console.print("⚠️ GitHub CLI not authenticated. Run: gh auth login")
            return False


@click.command()
@click.option("--project-dir", type=click.Path(exists=True), default=".", 
              help="Project directory (default: current directory)")
@click.option("--non-interactive", is_flag=True, 
              help="Use default values for all prompts")
def main(project_dir: str, non_interactive: bool) -> None:
    """🧙‍♂️ TDD Project Template - Interactive Setup Wizard."""
    
    # Change to project directory
    original_cwd = os.getcwd()
    os.chdir(project_dir)
    
    try:
        wizard = TDDProjectWizard(non_interactive=non_interactive)
        
        if non_interactive:
            console.print("🤖 Running in non-interactive mode with default values")
        
        success = wizard.run()
        sys.exit(0 if success else 1)
        
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    main()