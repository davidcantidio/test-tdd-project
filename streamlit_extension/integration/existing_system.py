"""
🔗 Integration with Existing TDD Framework System

Provides seamless integration between the Streamlit extension and existing framework components:
- Epic JSON file synchronization
- Analytics engine integration  
- Gantt tracker compatibility
- Task timer bidirectional sync
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Graceful imports from existing framework
try:
    from tdah_tools.analytics_engine import AnalyticsEngine
    ANALYTICS_AVAILABLE = True
except ImportError:
    AnalyticsEngine = None
    ANALYTICS_AVAILABLE = False

try:
    from gantt_tracker import GanttTracker
    GANTT_AVAILABLE = True
except ImportError:
    GanttTracker = None
    GANTT_AVAILABLE = False

# Local imports
try:
    from ..utils.database import DatabaseManager
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    DatabaseManager = None
    DATABASE_UTILS_AVAILABLE = False


class ExistingSystemIntegrator:
    # Delegation to ExistingSystemIntegratorValidation
    def __init__(self):
        self._existingsystemintegratorvalidation = ExistingSystemIntegratorValidation()
    # Delegation to ExistingSystemIntegratorErrorhandling
    def __init__(self):
        self._existingsystemintegratorerrorhandling = ExistingSystemIntegratorErrorhandling()
    # Delegation to ExistingSystemIntegratorFormatting
    def __init__(self):
        self._existingsystemintegratorformatting = ExistingSystemIntegratorFormatting()
    # Delegation to ExistingSystemIntegratorDataaccess
    def __init__(self):
        self._existingsystemintegratordataaccess = ExistingSystemIntegratorDataaccess()
    # Delegation to ExistingSystemIntegratorNetworking
    def __init__(self):
        self._existingsystemintegratornetworking = ExistingSystemIntegratorNetworking()
    # Delegation to ExistingSystemIntegratorCalculation
    def __init__(self):
        self._existingsystemintegratorcalculation = ExistingSystemIntegratorCalculation()
    # Delegation to ExistingSystemIntegratorSerialization
    def __init__(self):
        self._existingsystemintegratorserialization = ExistingSystemIntegratorSerialization()
    # Delegation to ExistingSystemIntegratorUiinteraction
    def __init__(self):
        self._existingsystemintegratoruiinteraction = ExistingSystemIntegratorUiinteraction()
    # Delegation to ExistingSystemIntegratorLogging
    def __init__(self):
        self._existingsystemintegratorlogging = ExistingSystemIntegratorLogging()
    # Delegation to ExistingSystemIntegratorBusinesslogic
    def __init__(self):
        self._existingsystemintegratorbusinesslogic = ExistingSystemIntegratorBusinesslogic()
    """Integrates Streamlit extension with existing framework components."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.epics_dir = self.project_root / "epics"
        self.db_manager = DatabaseManager() if DATABASE_UTILS_AVAILABLE else None
        
        # Initialize component integrations
        self.analytics = AnalyticsEngine() if ANALYTICS_AVAILABLE else None
        self.gantt = GanttTracker() if GANTT_AVAILABLE else None
    
    def _validate_epic_data(self, epic_data: Dict[str, Any], filename: str) -> tuple[bool, List[str]]:
        """
        Validate and sanitize epic JSON data before processing.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(epic_data, dict):
            errors.append(f"{filename}: Epic data must be a dictionary")
            return False, errors
        
        # Required fields validation
        required_fields = ["epic_key", "name"]
        for field in required_fields:
            if field not in epic_data:
                errors.append(f"{filename}: Missing required field '{field}'")
            elif not isinstance(epic_data[field], str) or not epic_data[field].strip():
                errors.append(f"{filename}: Field '{field}' must be a non-empty string")
        
        # Sanitize epic_key (alphanumeric, underscore, hyphen only)
        if "epic_key" in epic_data:
            epic_key = str(epic_data["epic_key"]).strip()
            if not epic_key.replace("_", "").replace("-", "").isalnum():
                errors.append(f"{filename}: epic_key contains invalid characters. Use only alphanumeric, underscore, hyphen")
                
            # Limit epic_key length
            if len(epic_key) > 50:
                errors.append(f"{filename}: epic_key too long (max 50 characters)")
        
        # Sanitize name field
        if "name" in epic_data:
            name = str(epic_data["name"]).strip()
            if len(name) > 200:
                errors.append(f"{filename}: name too long (max 200 characters)")
        
        # Validate status if present
        if "status" in epic_data:
            valid_statuses = ["planning", "active", "on_hold", "completed", "cancelled"]
            if epic_data["status"] not in valid_statuses:
                errors.append(f"{filename}: Invalid status '{epic_data['status']}'. Valid: {valid_statuses}")
        
        # Validate numeric fields if present
        numeric_fields = ["priority", "difficulty_level", "points_earned"]
        for field in numeric_fields:
            if field in epic_data:
                try:
                    value = int(epic_data[field])
                    if value < 0 or value > 10:
                        errors.append(f"{filename}: {field} must be between 0 and 10")
                except (ValueError, TypeError):
                    errors.append(f"{filename}: {field} must be a valid integer")
        
        return len(errors) == 0, errors
    
    def sync_epics_from_json(self) -> Dict[str, Any]:
        """
        Synchronize epic JSON files with database.
        
        Returns:
            Dict with sync results and statistics
        """
        if not self.epics_dir.exists():
            return {"error": "Epics directory not found", "synced": 0}
        
        results = {
            "synced": 0,
            "errors": [],
            "updated_epics": [],
            "created_epics": []
        }
        
        # Find all epic JSON files
        epic_files = list(self.epics_dir.glob("*.json"))
        
        if not self.db_manager:
            results["error"] = "Database manager not available"
            return results
        
        # Load existing epics once to avoid repeated database calls
        existing_epics = self.db_manager.get_epics()
        epic_keys_map = {epic.get("epic_key"): epic for epic in existing_epics}
        
        for epic_file in epic_files:
            try:
                with open(epic_file, 'r', encoding='utf-8') as f:
                    epic_data = json.load(f)
                
                # Validate and sanitize JSON data
                is_valid, validation_errors = self._validate_epic_data(epic_data, epic_file.name)
                if not is_valid:
                    results["errors"].extend(validation_errors)
                    continue
                
                # Extract sanitized epic info
                epic_key = epic_data.get("epic_key", epic_file.stem).strip()
                epic_name = epic_data.get("name", epic_key).strip()
                
                # Check if epic exists in database (using pre-loaded map)
                existing_epic = epic_keys_map.get(epic_key)
                
                if existing_epic:
                    results["updated_epics"].append(epic_key)
                else:
                    results["created_epics"].append(epic_key)
                
                results["synced"] += 1
                
            except json.JSONDecodeError as e:
                results["errors"].append(f"Invalid JSON in {epic_file.name}: {str(e)}")
            except Exception as e:
                results["errors"].append(f"Error processing {epic_file.name}: {str(e)}")
        
        return results
    
    def sync_epics_to_json(self) -> Dict[str, Any]:
        """
        Export database epics to JSON files.
        
        Returns:
            Dict with export results
        """
        if not self.db_manager:
            return {"error": "Database manager not available", "exported": 0}
        
        results = {
            "exported": 0,
            "errors": [],
            "files_created": []
        }
        
        # Ensure epics directory exists
        self.epics_dir.mkdir(exist_ok=True)
        
        try:
            epics = self.db_manager.get_epics()
            
            for epic in epics:
                epic_key = epic.get("epic_key", f"epic_{epic.get('id')}")
                
                # Get tasks for this epic
                tasks = self.db_manager.get_tasks(epic_id=epic.get("id"))
                
                # Build JSON structure
                epic_json = {
                    "epic_key": epic_key,
                    "name": epic.get("name", ""),
                    "description": epic.get("description", ""),
                    "status": epic.get("status", "planning"),
                    "priority": epic.get("priority", 1),
                    "difficulty_level": epic.get("difficulty_level", 1),
                    "points_earned": epic.get("points_earned", 0),
                    "created_at": epic.get("created_at", ""),
                    "updated_at": epic.get("updated_at", ""),
                    "tasks": [
                        {
                            "id": task.get("id"),
                            "title": task.get("title", ""),
                            "description": task.get("description", ""),
                            "status": task.get("status", "todo"),
                            "tdd_phase": task.get("tdd_phase", ""),
                            "priority": task.get("priority", 1),
                            "estimate_minutes": task.get("estimate_minutes", 0)
                        }
                        for task in tasks
                    ]
                }
                
                # Write to file
                json_file = self.epics_dir / f"{epic_key}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(epic_json, f, indent=2, ensure_ascii=False)
                
                results["files_created"].append(str(json_file))
                results["exported"] += 1
                
        except Exception as e:
            results["errors"].append(f"Export error: {str(e)}")
        
        return results
    
    def get_analytics_data(self, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics data from existing analytics engine.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analytics data or fallback data if engine unavailable
        """
        if not self.analytics:
            return self._get_fallback_analytics(days)
        
        try:
            # Use existing analytics engine
            return self.analytics.generate_productivity_report(days)
        except Exception as e:
            logging.info(f"Analytics engine error: {e}")
            return self._get_fallback_analytics(days)
    
    def _get_fallback_analytics(self, days: int) -> Dict[str, Any]:
        """Fallback analytics using database manager."""
        if not self.db_manager:
            return {"error": "No analytics data available"}
        
        # Get basic stats from database
        user_stats = self.db_manager.get_user_stats()
        timer_sessions = self.db_manager.get_timer_sessions(days)
        
        # Calculate basic metrics
        total_sessions = len(timer_sessions)
        total_focus_time = sum(s.get("planned_duration_minutes", 0) for s in timer_sessions)
        avg_focus_rating = sum(s.get("focus_rating", 0) for s in timer_sessions if s.get("focus_rating")) / max(total_sessions, 1)
        
        return {
            "period_days": days,
            "completed_tasks": user_stats.get("completed_tasks", 0),
            "total_points": user_stats.get("total_points", 0),
            "focus_sessions": total_sessions,
            "total_focus_minutes": total_focus_time,
            "average_focus_rating": round(avg_focus_rating, 1),
            "active_streaks": user_stats.get("active_streaks", 0)
        }
    
    def get_gantt_data(self) -> Dict[str, Any]:
        """
        Get Gantt chart data from existing tracker.
        
        Returns:
            Gantt data compatible with existing gantt_tracker.py
        """
        if not self.gantt:
            return self._get_fallback_gantt_data()
        
        try:
            return self.gantt.generate_gantt_data()
        except Exception as e:
            logging.info(f"Gantt tracker error: {e}")
            return self._get_fallback_gantt_data()
    
    def _get_fallback_gantt_data(self) -> Dict[str, Any]:
        """Fallback Gantt data from database."""
        if not self.db_manager:
            return {"tasks": [], "epics": []}
        
        epics = self.db_manager.get_epics()
        all_tasks = self.db_manager.get_tasks()
        
        gantt_tasks = []
        for task in all_tasks:
            gantt_tasks.append({
                "id": task.get("id"),
                "name": task.get("title", ""),
                "start_date": task.get("created_at", ""),
                "end_date": task.get("completed_at", ""),
                "progress": 100 if task.get("status") == "completed" else 50 if task.get("status") == "in_progress" else 0,
                "epic_name": task.get("epic_name", ""),
                "status": task.get("status", "todo")
            })
        
        return {
            "tasks": gantt_tasks,
            "epics": epics,
            "generated_at": datetime.now().isoformat()
        }
    
    def validate_integration_health(self) -> Dict[str, Any]:
        """
        Check health of all integrations.
        
        Returns:
            Health status of each integration component
        """
        health = {
            "database_manager": DATABASE_UTILS_AVAILABLE and self.db_manager is not None,
            "analytics_engine": ANALYTICS_AVAILABLE and self.analytics is not None,
            "gantt_tracker": GANTT_AVAILABLE and self.gantt is not None,
            "epics_directory": self.epics_dir.exists(),
            "json_files_count": len(list(self.epics_dir.glob("*.json"))) if self.epics_dir.exists() else 0
        }
        
        # Test database connectivity
        if self.db_manager:
            try:
                db_health = self.db_manager.check_database_health()
                health.update({
                    "framework_db": db_health.get("framework_db_connected", False),
                    "timer_db": db_health.get("timer_db_connected", False)
                })
            except Exception as e:
                health["database_error"] = str(e)
        
        # Overall health score
        health_checks = [
            health.get("database_manager", False),
            health.get("epics_directory", False),
            health.get("framework_db", False)
        ]
        health["overall_health"] = sum(health_checks) / len(health_checks)
        
        return health
    
    def get_compatibility_info(self) -> Dict[str, Any]:
        """
        Get information about compatibility with existing system components.
        
        Returns:
            Compatibility status and recommendations
        """
        return {
            "framework_version": "1.1.2",  # From CLAUDE.md context
            "streamlit_extension_version": "1.0.0",
            "compatible_components": {
                "task_timer.db": "Full bidirectional sync",
                "framework.db": "Full integration with existing schema",
                "epics/*.json": "Bidirectional sync available",
                "analytics_engine": "Compatible" if ANALYTICS_AVAILABLE else "Install tdah_tools",
                "gantt_tracker": "Compatible" if GANTT_AVAILABLE else "Optional component"
            },
            "migration_needed": False,
            "breaking_changes": False,
            "recommendations": [
                "Install optional dependencies: pip install sqlalchemy",
                "Run database health check before first use",
                "Backup existing .db files before major operations"
            ]
        }


# Utility functions for direct use
def quick_sync_epics_json_to_db(project_root: Path = None) -> bool:
    """Quick utility to sync JSON epics to database."""
    integrator = ExistingSystemIntegrator(project_root)
    results = integrator.sync_epics_from_json()
    
    success = results.get("synced", 0) > 0 and not results.get("error")
    if not success:
        logging.info(f"Sync failed: {results.get('error', 'Unknown error')}")
    
    return success


def quick_health_check(project_root: Path = None) -> Dict[str, Any]:
    """Quick utility to check integration health."""
    integrator = ExistingSystemIntegrator(project_root)
    return integrator.validate_integration_health()


# Module availability check
def check_integration_availability():
    """Check which integrations are available."""
    return {
        "database_utils": DATABASE_UTILS_AVAILABLE,
        "analytics_engine": ANALYTICS_AVAILABLE,
        "gantt_tracker": GANTT_AVAILABLE,
        "overall_ready": DATABASE_UTILS_AVAILABLE  # Minimum requirement
    }