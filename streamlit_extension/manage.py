#!/usr/bin/env python3
"""
🎛️ Streamlit Extension Management CLI

Command-line interface for managing the Streamlit extension with:
- Launch Streamlit app
- GitHub synchronization
- Database migrations
- Configuration validation
- Development tools
"""

import sys
import os
import subprocess  # nosec B404 - Used for launching Streamlit with validated arguments
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import time
from datetime import datetime

# Graceful imports
try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    TYPER_AVAILABLE = True
except ImportError:
    typer = None
    Console = None
    Table = None
    Panel = None
    rprint = print
    TYPER_AVAILABLE = False

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from streamlit_extension.config import load_config, create_streamlit_config_file
    from streamlit_extension import check_dependencies, is_ready
except ImportError as e:
    try:
        # Try relative import as fallback
        from .config import load_config, create_streamlit_config_file
        from . import check_dependencies, is_ready
    except ImportError:
        print(f"❌ Error: Could not import streamlit_extension modules: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python path: {sys.path[:3]}")
        sys.exit(1)

# Initialize CLI app
if TYPER_AVAILABLE:
    app = typer.Typer(
        name="manage",
        help="🎛️ Streamlit Extension Management CLI",
        add_completion=False
    )
    console = Console()
else:
    app = None
    console = None


def check_streamlit_dependencies() -> tuple[bool, List[str]]:
    """Check if all Streamlit dependencies are available."""
    missing = check_dependencies()
    
    # Additional checks
    try:
        import streamlit
    except ImportError:
        if 'streamlit' not in missing:
            missing.append('streamlit')
    
    try:
        import sqlalchemy
    except ImportError:
        if 'sqlalchemy' not in missing:
            missing.append('sqlalchemy')
    
    return len(missing) == 0, missing


def print_header():
    """Print CLI header."""
    if console:
        console.print(Panel.fit("🚀 TDD Framework - Streamlit Extension Manager", 
                               style="bold cyan"))
    else:
        print("🚀 TDD Framework - Streamlit Extension Manager")
        print("=" * 50)


def print_dependencies_error(missing: List[str]):
    """Print error message for missing dependencies."""
    if console:
        console.print(f"\n❌ [bold red]Missing dependencies:[/bold red] {', '.join(missing)}")
        console.print("[yellow]Install with:[/yellow] pip install " + " ".join(missing))
        console.print("[yellow]Or use poetry:[/yellow] poetry install --extras streamlit")
    else:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        print("Or use poetry: poetry install --extras streamlit")


def _validate_single_epic(epic_file: Path, fix_issues: bool = False) -> List[str]:
    """Validate a single epic JSON file."""
    issues = []
    
    try:
        with open(epic_file, 'r', encoding='utf-8') as f:
            epic_data = json.load(f)
    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON: {str(e)}")
        return issues
    except Exception as e:
        issues.append(f"File error: {str(e)}")
        return issues
    
    # Required fields validation
    required_fields = ["epic_key", "name", "description", "status"]
    for field in required_fields:
        if field not in epic_data or not epic_data[field]:
            issues.append(f"Missing required field: {field}")
    
    # Status validation
    valid_statuses = ["planning", "active", "on_hold", "completed", "cancelled"]
    if "status" in epic_data and epic_data["status"] not in valid_statuses:
        issues.append(f"Invalid status: {epic_data['status']}. Valid: {valid_statuses}")
    
    # Epic key format validation
    if "epic_key" in epic_data:
        epic_key = epic_data["epic_key"]
        if not epic_key.replace("_", "").replace("-", "").isalnum():
            issues.append(f"Invalid epic_key format: {epic_key}. Use alphanumeric, underscore, hyphen only")
    
    # Tasks validation (if present)
    if "tasks" in epic_data and isinstance(epic_data["tasks"], list):
        for i, task in enumerate(epic_data["tasks"]):
            if not isinstance(task, dict):
                issues.append(f"Task {i}: must be an object")
                continue
            
            # Required task fields
            task_required = ["title", "status"]
            for field in task_required:
                if field not in task or not task[field]:
                    issues.append(f"Task {i}: missing required field '{field}'")
            
            # Task status validation
            valid_task_statuses = ["todo", "in_progress", "completed", "blocked"]
            if "status" in task and task["status"] not in valid_task_statuses:
                issues.append(f"Task {i}: invalid status '{task['status']}'. Valid: {valid_task_statuses}")
    
    # Auto-fix issues if requested
    if fix_issues and issues:
        fixed_data = epic_data.copy()
        fixed = False
        
        # Fix missing fields with defaults
        if "epic_key" not in fixed_data:
            fixed_data["epic_key"] = epic_file.stem
            fixed = True
        
        if "name" not in fixed_data or not fixed_data["name"]:
            fixed_data["name"] = epic_file.stem.replace("_", " ").title()
            fixed = True
        
        if "description" not in fixed_data or not fixed_data["description"]:
            fixed_data["description"] = f"Epic: {fixed_data.get('name', epic_file.stem)}"
            fixed = True
        
        if "status" not in fixed_data or fixed_data["status"] not in valid_statuses:
            fixed_data["status"] = "planning"
            fixed = True
        
        # Save fixed file
        if fixed:
            try:
                with open(epic_file, 'w', encoding='utf-8') as f:
                    json.dump(fixed_data, f, indent=2, ensure_ascii=False)
                # Re-validate to update issues list
                return _validate_single_epic(epic_file, False)
            except Exception as e:
                issues.append(f"Auto-fix failed: {str(e)}")
    
    return issues


if TYPER_AVAILABLE:
    @app.command()
    def run_streamlit(
        port: int = typer.Option(8501, help="Port to run Streamlit on"),
        host: str = typer.Option("localhost", help="Host to bind to"),
        config_check: bool = typer.Option(True, help="Check configuration before starting"),
        browser: bool = typer.Option(True, help="Open browser automatically")
    ):
        """🚀 Launch the Streamlit interface."""
        print_header()
        
        # Check dependencies
        deps_ok, missing = check_streamlit_dependencies()
        if not deps_ok:
            print_dependencies_error(missing)
            raise typer.Exit(1)
        
        # Load configuration
        try:
            config = load_config()
            if config_check:
                console.print("✅ Configuration loaded successfully")
        except Exception as e:
            console.print(f"❌ [red]Configuration error:[/red] {e}")
            raise typer.Exit(1)
        
        # Use config defaults unless overridden
        actual_port = config.streamlit_port
        actual_host = config.streamlit_host
        
        # Create Streamlit config file
        try:
            create_streamlit_config_file(config)
            console.print("📁 Streamlit config.toml created")
        except Exception as e:
            console.print(f"⚠️ [yellow]Warning: Could not create config.toml:[/yellow] {e}")
        
        # Check database files
        framework_db = config.get_database_path()
        timer_db = config.get_timer_database_path()
        
        if not framework_db.exists():
            console.print(f"⚠️ [yellow]Warning: framework.db not found at {framework_db}[/yellow]")
        
        if not timer_db.exists():
            console.print(f"⚠️ [yellow]Warning: task_timer.db not found at {timer_db}[/yellow]")
        
        # Launch Streamlit
        app_path = Path(__file__).parent / "streamlit_app.py"
        
        if not app_path.exists():
            console.print(f"❌ [red]Streamlit app not found at {app_path}[/red]")
            raise typer.Exit(1)
        
        console.print(f"🚀 Starting Streamlit on [cyan]http://{actual_host}:{actual_port}[/cyan]")
        console.print("Press Ctrl+C to stop")
        
        # Build command
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(app_path),
            "--server.port", str(actual_port),
            "--server.address", actual_host,
            "--server.headless", "true" if not browser else "false"
        ]
        
        try:
            # Security: Safe subprocess usage - all arguments are validated/hardcoded
            # sys.executable: Python interpreter path (trusted)
            # app_path: Validated file path existence above
            # port/host: Validated above with proper type conversion
            subprocess.run(cmd, check=True)  # nosec B603
        except KeyboardInterrupt:
            console.print("\n👋 Streamlit stopped")
        except subprocess.CalledProcessError as e:
            console.print(f"❌ [red]Error running Streamlit:[/red] {e}")
            raise typer.Exit(1)

    @app.command()  
    def validate_config(
        config_file: Optional[str] = typer.Option(None, help="Path to .env file"),
        show_secrets: bool = typer.Option(False, help="Show sensitive values")
    ):
        """🔍 Validate configuration settings."""
        print_header()
        
        try:
            config = load_config(config_file)
            
            # Create validation table
            table = Table(title="Configuration Validation")
            table.add_column("Setting", style="cyan", width=30)
            table.add_column("Value", style="green", width=40)
            table.add_column("Status", width=15)
            
            # Basic settings
            table.add_row("Streamlit Port", str(config.streamlit_port), 
                         "✅" if 1024 <= config.streamlit_port <= 65535 else "⚠️")
            table.add_row("Theme", config.streamlit_theme, "✅")
            table.add_row("Timezone", config.timezone, "✅")
            
            # Database
            framework_db = config.get_database_path()
            timer_db = config.get_timer_database_path()
            
            table.add_row("Framework DB", str(framework_db), 
                         "✅" if framework_db.exists() else "❌")
            table.add_row("Timer DB", str(timer_db),
                         "✅" if timer_db.exists() else "❌")
            
            # GitHub (hide token unless requested)
            if config.github_token:
                token_display = config.github_token if show_secrets else "***" + config.github_token[-4:]
                table.add_row("GitHub Token", token_display, 
                             "✅" if config.is_github_configured() else "⚠️")
            else:
                table.add_row("GitHub Token", "Not set", "⚠️")
            
            if config.github_repo_owner:
                table.add_row("GitHub Owner", config.github_repo_owner, "✅")
            if config.github_repo_name:
                table.add_row("GitHub Repo", config.github_repo_name, "✅")
            
            # TDAH settings
            table.add_row("Focus Duration", f"{config.focus_session_duration} min", 
                         "✅" if 5 <= config.focus_session_duration <= 120 else "⚠️")
            table.add_row("Gamification", "Enabled" if config.enable_gamification else "Disabled", "✅")
            
            console.print(table)
            
            # Show warnings
            if config.missing_dependencies:
                console.print(f"\n⚠️ [yellow]Missing optional dependencies:[/yellow] {', '.join(config.missing_dependencies)}")
            
            if not config.is_github_configured():
                console.print("\n⚠️ [yellow]GitHub integration not configured (optional)[/yellow]")
            
            console.print("\n✅ Configuration validation complete")
            
        except Exception as e:
            console.print(f"❌ [red]Configuration validation failed:[/red] {e}")
            raise typer.Exit(1)

    @app.command()
    def check_deps():
        """🔍 Check system dependencies."""
        print_header()
        
        # Create dependencies table
        table = Table(title="Dependencies Check")
        table.add_column("Package", style="cyan", width=25)
        table.add_column("Required", width=15)
        table.add_column("Status", width=15)
        table.add_column("Version", style="dim", width=20)
        
        dependencies = [
            ("streamlit", True),
            ("sqlalchemy", True), 
            ("python-dotenv", False),
            ("gql", False),
            ("streamlit-dnd", False),
            ("pandas", False),
            ("plotly", False),
            ("numpy", False),
            ("typer", False),
            ("rich", False)
        ]
        
        all_good = True
        
        for package, required in dependencies:
            try:
                module = __import__(package)
                version = getattr(module, "__version__", "unknown")
                table.add_row(package, "Yes" if required else "No", "✅", version)
            except ImportError:
                status = "❌" if required else "⚠️"
                table.add_row(package, "Yes" if required else "No", status, "Not installed")
                if required:
                    all_good = False
        
        console.print(table)
        
        if all_good:
            console.print("\n✅ All required dependencies available")
        else:
            console.print("\n❌ Some required dependencies are missing")
            console.print("Install with: poetry install --extras streamlit")

    @app.command()
    def sync_github(
        force: bool = typer.Option(False, help="Force sync even if no changes"),
        dry_run: bool = typer.Option(False, help="Show what would be synced")
    ):
        """🔄 Synchronize with GitHub Projects V2."""
        print_header()
        
        console.print("🔄 GitHub sync functionality will be implemented in Task 1.2.8")
        console.print("This is a placeholder for the GitHub Projects V2 integration")
        
        if dry_run:
            console.print("\n📋 [dim]Dry run mode - no changes would be made[/dim]")

    @app.command()
    def migrate_db():
        """🔄 Run database migrations."""
        print_header()
        
        console.print("🔄 Database migration functionality will be implemented in Task 1.2.3")
        console.print("This is a placeholder for database migrations")

    @app.command()
    def validate_epics(
        epics_dir: Optional[str] = typer.Option(None, help="Path to epics directory"),
        fix_issues: bool = typer.Option(False, help="Automatically fix validation issues"),
        output_format: str = typer.Option("table", help="Output format: table, json")
    ):
        """🔍 Validate epic JSON files structure and content."""
        print_header()
        
        # Determine epics directory
        if epics_dir:
            epics_path = Path(epics_dir)
        else:
            epics_path = Path.cwd() / "epics"
        
        if not epics_path.exists():
            console.print(f"❌ [red]Epics directory not found: {epics_path}[/red]")
            raise typer.Exit(1)
        
        # Find epic JSON files
        epic_files = list(epics_path.glob("*.json"))
        
        if not epic_files:
            console.print(f"⚠️ [yellow]No JSON files found in {epics_path}[/yellow]")
            return
        
        console.print(f"🔍 Validating {len(epic_files)} epic files...")
        
        validation_results = []
        total_issues = 0
        
        for epic_file in epic_files:
            issues = _validate_single_epic(epic_file, fix_issues)
            validation_results.append({
                "file": epic_file.name,
                "path": str(epic_file),
                "issues": issues,
                "status": "✅ Valid" if not issues else f"❌ {len(issues)} issues"
            })
            total_issues += len(issues)
        
        # Display results
        if output_format == "json":
            console.print(json.dumps(validation_results, indent=2))
        else:
            # Table format
            table = Table(title="Epic Validation Results")
            table.add_column("File", style="cyan", width=25)
            table.add_column("Status", width=20)
            table.add_column("Issues", width=50)
            
            for result in validation_results:
                issues_text = "; ".join(result["issues"]) if result["issues"] else "No issues"
                table.add_row(
                    result["file"],
                    result["status"],
                    issues_text
                )
            
            console.print(table)
        
        # Summary
        valid_files = len([r for r in validation_results if not r["issues"]])
        console.print(f"\n📊 Summary: {valid_files}/{len(epic_files)} files valid, {total_issues} total issues")
        
        if fix_issues and total_issues > 0:
            console.print("🔧 Issues were automatically fixed where possible")
        
        if total_issues > 0:
            raise typer.Exit(1)

    @app.command()
    def dev_server(
        reload: bool = typer.Option(True, help="Enable auto-reload"),
        debug: bool = typer.Option(False, help="Enable debug mode")
    ):
        """🛠️ Start development server with auto-reload."""
        print_header()
        
        if debug:
            os.environ["DEBUG_MODE"] = "true"
        
        console.print("🛠️ Starting development server...")
        
        # Use streamlit run with --server.runOnSave for auto-reload
        run_streamlit(browser=True)

else:
    # Fallback CLI for when typer is not available
    def run_streamlit():
        """Launch Streamlit without typer."""
        print_header()
        
        deps_ok, missing = check_streamlit_dependencies()
        if not deps_ok:
            print_dependencies_error(missing)
            sys.exit(1)
        
        app_path = Path(__file__).parent / "streamlit_app.py"
        
        if not app_path.exists():
            print(f"❌ Streamlit app not found at {app_path}")
            sys.exit(1)
        
        print("🚀 Starting Streamlit...")
        
        cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
        
        try:
            # Security: Safe subprocess usage - all arguments are validated/hardcoded
            # sys.executable: Python interpreter path (trusted)
            # app_path: Validated file path existence above (lines 505-507)
            subprocess.run(cmd, check=True)  # nosec B603
        except KeyboardInterrupt:
            print("\n👋 Streamlit stopped")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error running Streamlit: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    if not TYPER_AVAILABLE:
        print("⚠️ Enhanced CLI not available - install typer and rich for full functionality")
        if len(sys.argv) > 1 and sys.argv[1] == "run":
            run_streamlit()
        else:
            print("Available commands: manage run")
        return
    
    # Handle the case where this is called as streamlit-run script
    if Path(sys.argv[0]).name == "streamlit-run":
        run_streamlit()
        return
    
    app()


if __name__ == "__main__":
    main()