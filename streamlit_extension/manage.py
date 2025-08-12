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
import subprocess
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
            subprocess.run(cmd, check=True)
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
            subprocess.run(cmd, check=True)
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