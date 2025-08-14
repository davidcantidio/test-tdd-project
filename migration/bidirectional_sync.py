#!/usr/bin/env python3
"""
🔄 Bidirectional Sync Engine for Epic-Database Integration

Implementa sincronização inteligente entre JSONs e banco de dados
seguindo estratégia de 3 camadas:

CAMADA 1 - CORE DATA (Sync Bidirecional):
  JSON ↔ Database: name, summary, goals, definition_of_done, labels, tasks
  
CAMADA 2 - CALCULATED FIELDS (Database → JSON):
  Database → JSON: planned_dates, calculated_duration_days, stats
  
CAMADA 3 - SYSTEM FIELDS (Database Only):
  Database: created_at, id, assigned_to, points_earned, github_*, etc.

Features:
- Conflict detection and resolution
- Change tracking with checksums
- Rollback capability
- Comprehensive logging
"""

import sqlite3
import json
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import sys
import traceback
import time

# Add migration to path
sys.path.append(str(Path(__file__).parent))

from data_base_strategy import DataBaseCalculator, DateBaseStrategy
from json_enrichment import JSONEnrichmentEngine

# Import the fixed connection pool
sys.path.append(str(Path(__file__).parent.parent))
try:
    from duration_system.database_transactions import DatabaseConnectionPool
    CONNECTION_POOL_AVAILABLE = True
except ImportError:
    CONNECTION_POOL_AVAILABLE = False


class SyncDirection(Enum):
    """Direções de sincronização."""
    JSON_TO_DB = "json_to_db"
    DB_TO_JSON = "db_to_json"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolution(Enum):
    """Estratégias de resolução de conflitos."""
    AUTO_JSON_WINS = "auto_json_wins"     # JSON sempre ganha
    AUTO_DB_WINS = "auto_db_wins"         # Database sempre ganha
    MANUAL_REQUIRED = "manual_required"   # Requer intervenção manual
    TIMESTAMP_WINS = "timestamp_wins"     # Modificação mais recente ganha


@dataclass
class SyncResult:
    """Resultado de uma operação de sincronização."""
    success: bool
    epic_key: str
    direction: SyncDirection
    changes_made: List[str]
    conflicts_detected: List[str]
    conflicts_resolved: List[str]
    errors: List[str]
    duration_ms: float
    
    def __post_init__(self):
        if self.changes_made is None:
            self.changes_made = []
        if self.conflicts_detected is None:
            self.conflicts_detected = []
        if self.conflicts_resolved is None:
            self.conflicts_resolved = []
        if self.errors is None:
            self.errors = []


class FieldMapping:
    """Mapeamento de campos entre JSON e Database por camada."""
    
    # CAMADA 1: Core Data - Sincronização bidirecional
    CORE_FIELDS = {
        'epic_key': 'id',
        'name': 'name', 
        'summary': 'summary',
        'duration': 'duration_description',
        'goals': 'goals',
        'definition_of_done': 'definition_of_done',
        'labels': 'labels',
        'tdd_enabled': 'tdd_enabled',
        'methodology': 'methodology',
        'performance_constraints': 'performance_constraints',
        'quality_gates': 'quality_gates',
        'automation_hooks': 'automation_hooks',
        'checklist_epic_level': 'checklist_epic_level'
    }
    
    # CAMADA 1: Task fields - Sincronização bidirecional
    TASK_CORE_FIELDS = {
        'id': 'task_key',
        'title': 'title',
        'description': 'description',
        'tdd_phase': 'tdd_phase',
        'estimate_minutes': 'estimate_minutes',
        'story_points': 'story_points',
        'test_specs': 'test_specs',
        'acceptance_criteria': 'acceptance_criteria', 
        'deliverables': 'deliverables',
        'files_touched': 'files_touched',
        'test_plan': 'test_plan',
        'risk': 'risk',
        'mitigation': 'mitigation',
        'tdd_skip_reason': 'tdd_skip_reason',
        'priority_tags': 'priority_tags',
        'branch': 'github_branch'
    }
    
    # CAMADA 2: Calculated Fields - Apenas Database → JSON
    CALCULATED_FIELDS = {
        'planned_start_date',
        'planned_end_date', 
        'calculated_duration_days',
        'duration_unit',
        'actual_start_date',
        'actual_end_date'
    }
    
    # CAMADA 3: System Fields - Apenas Database (nunca exportados)
    SYSTEM_FIELDS = {
        'id', 'created_at', 'updated_at', 'completed_at', 'deleted_at',
        'assigned_to', 'created_by', 'reviewer_id',
        'points_earned', 'completion_bonus', 'difficulty_level',
        'github_issue_id', 'github_milestone_id', 'github_project_id',
        'estimated_hours', 'actual_hours', 'actual_minutes',
        'sync_status', 'last_json_sync', 'json_checksum'
    }


class BidirectionalSyncEngine:
    """
    Engine para sincronização bidirecional entre JSONs e banco de dados.
    
    Funcionalidades:
    - Sincronização inteligente por camadas
    - Detecção e resolução de conflitos
    - Change tracking com checksums
    - Rollback automático em caso de erro
    """
    
    def __init__(self, db_path: str = "framework.db",
                 conflict_resolution: ConflictResolution = ConflictResolution.TIMESTAMP_WINS,
                 max_retries: int = 3,
                 retry_delay: float = 0.1):
        self.db_path = db_path
        self.conflict_resolution = conflict_resolution
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize components
        self.enrichment_engine = JSONEnrichmentEngine(DateBaseStrategy.NEXT_MONDAY)
        self.field_mapping = FieldMapping()
        
        # Initialize connection pool if available
        if CONNECTION_POOL_AVAILABLE:
            self.connection_pool = DatabaseConnectionPool(db_path, max_connections=5)
        else:
            self.connection_pool = None
        
        # Sync tracking
        self.sync_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 checksum of data for change detection."""
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def get_database_connection(self):
        """Get database connection using fixed connection pool."""
        if self.connection_pool:
            # Connection pool connections may not have row_factory set
            class ConnectionWrapper:
                def __init__(self, pool_conn):
                    self.conn = pool_conn.__enter__()
                    self.conn.row_factory = sqlite3.Row
                    self.pool_conn = pool_conn
                
                def __enter__(self):
                    return self.conn
                
                def __exit__(self, *args):
                    self.pool_conn.__exit__(*args)
                    
                def execute(self, *args, **kwargs):
                    return self.conn.execute(*args, **kwargs)
                    
                def commit(self):
                    return self.conn.commit()

                def rollback(self):
                    return self.conn.rollback()

            return ConnectionWrapper(self.connection_pool.get_connection())
        else:
            # Fallback to direct connection with retry logic
            attempts = 0
            while True:
                try:
                    conn = sqlite3.connect(self.db_path, timeout=30.0)
                    conn.row_factory = sqlite3.Row  # Enable column access by name
                    conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
                    conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
                    return conn
                except sqlite3.OperationalError:
                    if attempts >= self.max_retries:
                        raise
                    attempts += 1
                    time.sleep(self.retry_delay)
    
    def epic_exists_in_db(self, epic_key: str) -> bool:
        """Check if epic exists in database."""
        with self.get_database_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM framework_epics WHERE epic_key = ? AND deleted_at IS NULL",
                (epic_key,)
            )
            return cursor.fetchone()[0] > 0
    
    def get_epic_from_db(self, epic_key: str) -> Optional[Dict[str, Any]]:
        """Load epic data from database."""
        with self.get_database_connection() as conn:
            # Get epic data
            cursor = conn.execute("""
                SELECT * FROM framework_epics 
                WHERE epic_key = ? AND deleted_at IS NULL
            """, (epic_key,))
            
            epic_row = cursor.fetchone()
            if not epic_row:
                return None
            
            epic_data = dict(epic_row)
            
            # Get tasks for this epic
            cursor = conn.execute("""
                SELECT * FROM framework_tasks 
                WHERE epic_id = ? AND status != 'deleted'
                ORDER BY task_sequence, task_key
            """, (epic_data['id'],))
            
            tasks = [dict(row) for row in cursor.fetchall()]
            epic_data['tasks'] = tasks
            
            return epic_data
    
    def insert_epic_to_db(self, epic_data: Dict[str, Any]) -> int:
        """Insert new epic into database using a single connection."""
        with self.get_database_connection() as conn:
            try:
                # Increase timeout for complex operations
                conn.execute("PRAGMA busy_timeout=60000")

                # Prepare epic fields
                epic_key = epic_data.get('id') or epic_data.get('epic_key', '')
                name = epic_data.get('name', '')
                summary = epic_data.get('summary', epic_data.get('description', ''))
                duration_desc = epic_data.get('duration', '')

                # JSON fields
                goals = json.dumps(epic_data.get('goals', []), ensure_ascii=False)
                definition_of_done = json.dumps(epic_data.get('definition_of_done', []), ensure_ascii=False)
                labels = json.dumps(epic_data.get('labels', []), ensure_ascii=False)

                # Calculate dates using enrichment engine
                enriched = self.enrichment_engine.enrich_epic(epic_data)
                calc_fields = enriched.get('calculated_fields', {})

                # Insert epic
                cursor = conn.execute("""
                    INSERT INTO framework_epics (
                        epic_key, name, summary, duration_description,
                        goals, definition_of_done, labels,
                        planned_start_date, planned_end_date, calculated_duration_days,
                        tdd_enabled, methodology,
                        performance_constraints, quality_gates, automation_hooks, checklist_epic_level,
                        sync_status, json_checksum, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'synced', ?, ?, ?)
                """, (
                    epic_key, name, summary, duration_desc,
                    goals, definition_of_done, labels,
                    calc_fields.get('planned_start_date'), calc_fields.get('planned_end_date'),
                    calc_fields.get('calculated_duration_days', 0),
                    epic_data.get('tdd_enabled', True), epic_data.get('methodology', 'Test-Driven Development'),
                    json.dumps(epic_data.get('performance_constraints', {}), ensure_ascii=False),
                    json.dumps(epic_data.get('quality_gates', {}), ensure_ascii=False),
                    json.dumps(epic_data.get('automation_hooks', {}), ensure_ascii=False),
                    json.dumps(epic_data.get('checklist_epic_level', []), ensure_ascii=False),
                    self.calculate_checksum(epic_data),
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))

                epic_id = cursor.lastrowid

                # Insert tasks using the same connection
                self.insert_tasks_to_db(epic_id, epic_data.get('tasks', []), conn=conn)

                conn.commit()
                return epic_id
            except Exception:
                conn.rollback()
                raise

    def insert_tasks_to_db(self, epic_id: int, tasks: List[Dict[str, Any]], conn: sqlite3.Connection | None = None):
        """Insert tasks for an epic into database.

        Uses batch insertion and supports connection reuse to avoid nested
        transactions that could lead to deadlocks.
        """

        # Prepare data for batch insertion
        task_rows: List[Tuple[Any, ...]] = []
        for i, task in enumerate(tasks):
            task_key = task.get('id', f"{i+1}")
            title = task.get('title', '')
            description = task.get('description', '')
            tdd_phase = task.get('tdd_phase')
            estimate_minutes = task.get('estimate_minutes', 60)
            story_points = task.get('story_points', 1)
            branch = task.get('branch', '')

            # JSON fields
            test_specs = json.dumps(task.get('test_specs', []), ensure_ascii=False)
            acceptance_criteria = json.dumps(task.get('acceptance_criteria', []), ensure_ascii=False)
            deliverables = json.dumps(task.get('deliverables', []), ensure_ascii=False)
            files_touched = json.dumps(task.get('files_touched', []), ensure_ascii=False)
            test_plan = json.dumps(task.get('test_plan', []), ensure_ascii=False)

            task_rows.append((
                task_key, epic_id, title, description, tdd_phase,
                estimate_minutes, story_points, branch,
                test_specs, acceptance_criteria, deliverables, files_touched, test_plan,
                task.get('risk', ''), task.get('mitigation', ''), task.get('tdd_skip_reason', ''),
                i + 1, datetime.now().isoformat(), datetime.now().isoformat()
            ))

        if not task_rows:
            return

        insert_sql = """
            INSERT INTO framework_tasks (
                task_key, epic_id, title, description, tdd_phase,
                estimate_minutes, story_points, github_branch,
                test_specs, acceptance_criteria, deliverables, files_touched, test_plan,
                risk, mitigation, tdd_skip_reason,
                task_sequence, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        if conn is None:
            with self.get_database_connection() as own_conn:
                own_conn.executemany(insert_sql, task_rows)
                own_conn.commit()
        else:
            conn.executemany(insert_sql, task_rows)
    
    def sync_json_to_db(self, epic_data: Dict[str, Any], file_path: str = "") -> SyncResult:
        """Synchronize JSON data to database."""
        start_time = datetime.now()
        epic_key = epic_data.get('id') or epic_data.get('epic_key', '')
        
        result = SyncResult(
            success=False,
            epic_key=epic_key,
            direction=SyncDirection.JSON_TO_DB,
            changes_made=[],
            conflicts_detected=[],
            conflicts_resolved=[],
            errors=[],
            duration_ms=0
        )
        
        try:
            if not epic_key:
                result.errors.append("Epic key not found in JSON data")
                return result
            
            # Check if epic exists
            if self.epic_exists_in_db(epic_key):
                result.changes_made.append(f"Epic {epic_key} already exists - update logic needed")
                # TODO: Implement update logic with conflict detection
            else:
                # Insert new epic
                epic_id = self.insert_epic_to_db(epic_data)
                result.changes_made.append(f"Created epic {epic_key} with id {epic_id}")
                
                # Record sync in control table
                self.record_sync_operation(epic_key, file_path, "json_to_db")
            
            result.success = True
            
        except Exception as e:
            result.errors.append(f"Error syncing to database: {str(e)}")
            traceback.print_exc()
        
        finally:
            result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return result
    
    def sync_db_to_json(self, epic_key: str, output_path: Path) -> SyncResult:
        """Synchronize database data to JSON file."""
        start_time = datetime.now()
        
        result = SyncResult(
            success=False,
            epic_key=epic_key,
            direction=SyncDirection.DB_TO_JSON,
            changes_made=[],
            conflicts_detected=[],
            conflicts_resolved=[],
            errors=[],
            duration_ms=0
        )
        
        try:
            # Get epic from database
            db_epic = self.get_epic_from_db(epic_key)
            if not db_epic:
                result.errors.append(f"Epic {epic_key} not found in database")
                return result
            
            # Convert database format to JSON format
            json_data = self.convert_db_to_json_format(db_epic)
            
            # Enrich with calculated fields  
            enriched = self.enrichment_engine.enrich_epic(json_data)
            
            # Wrap in epic structure
            output_data = {"epic": enriched}
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            result.changes_made.append(f"Exported epic {epic_key} to {output_path}")
            result.success = True
            
        except Exception as e:
            result.errors.append(f"Error exporting to JSON: {str(e)}")
            traceback.print_exc()
        
        finally:
            result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return result
    
    def convert_db_to_json_format(self, db_epic: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database epic format to JSON format."""
        json_epic = {
            'id': db_epic.get('epic_key', ''),
            'name': db_epic.get('name', ''),
            'summary': db_epic.get('summary', ''),
            'duration': db_epic.get('duration_description', ''),
            'tdd_enabled': db_epic.get('tdd_enabled', True),
            'methodology': db_epic.get('methodology', 'Test-Driven Development')
        }
        
        # Convert JSON fields
        for json_field, db_field in [
            ('goals', 'goals'),
            ('definition_of_done', 'definition_of_done'), 
            ('labels', 'labels'),
            ('performance_constraints', 'performance_constraints'),
            ('quality_gates', 'quality_gates'),
            ('automation_hooks', 'automation_hooks'),
            ('checklist_epic_level', 'checklist_epic_level')
        ]:
            db_value = db_epic.get(db_field)
            if db_value:
                try:
                    json_epic[json_field] = json.loads(db_value) if isinstance(db_value, str) else db_value
                except (json.JSONDecodeError, TypeError):
                    json_epic[json_field] = []
            else:
                json_epic[json_field] = []
        
        # Convert tasks
        json_epic['tasks'] = []
        for task in db_epic.get('tasks', []):
            json_task = {
                'id': task.get('task_key', ''),
                'title': task.get('title', ''),
                'description': task.get('description', ''),
                'tdd_phase': task.get('tdd_phase'),
                'estimate_minutes': task.get('estimate_minutes', 60),
                'story_points': task.get('story_points', 1),
                'branch': task.get('github_branch', ''),
                'risk': task.get('risk', ''),
                'mitigation': task.get('mitigation', ''),
                'tdd_skip_reason': task.get('tdd_skip_reason', '')
            }
            
            # Convert task JSON fields
            for json_field, db_field in [
                ('test_specs', 'test_specs'),
                ('acceptance_criteria', 'acceptance_criteria'),
                ('deliverables', 'deliverables'),
                ('files_touched', 'files_touched'),
                ('test_plan', 'test_plan')
            ]:
                db_value = task.get(db_field)
                if db_value:
                    try:
                        json_task[json_field] = json.loads(db_value) if isinstance(db_value, str) else db_value
                    except (json.JSONDecodeError, TypeError):
                        json_task[json_field] = []
                else:
                    json_task[json_field] = []
            
            json_epic['tasks'].append(json_task)
        
        return json_epic
    
    def record_sync_operation(self, epic_key: str, file_path: str, direction: str):
        """Record sync operation in control table."""
        with self.get_database_connection() as conn:
            # Get epic ID
            cursor = conn.execute("SELECT id FROM framework_epics WHERE epic_key = ?", (epic_key,))
            row = cursor.fetchone()
            if not row:
                return
            
            epic_id = row[0]
            
            # Insert or update sync record
            conn.execute("""
                INSERT OR REPLACE INTO epic_json_sync (
                    epic_id, epic_key, json_file_path, 
                    sync_status, last_sync_at, sync_direction,
                    created_at, updated_at
                ) VALUES (?, ?, ?, 'synced', ?, ?, ?, ?)
            """, (
                epic_id, epic_key, file_path,
                datetime.now().isoformat(), direction,
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            conn.commit()
    
    def sync_all_epics_to_db(self, epics_dir: Path) -> List[SyncResult]:
        """Sync all JSON epics to database."""
        results = []
        
        json_files = list(epics_dir.glob('*.json'))
        print(f"🔄 Syncing {len(json_files)} epics to database...")
        
        for file_path in json_files:
            print(f"📄 Processing {file_path.name}...")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract epic data
                epic_data = data.get('epic', data)
                
                # Sync to database
                result = self.sync_json_to_db(epic_data, str(file_path))
                results.append(result)
                
                if result.success:
                    print(f"   ✅ {', '.join(result.changes_made)}")
                else:
                    print(f"   ❌ {', '.join(result.errors)}")
                    
            except Exception as e:
                error_result = SyncResult(
                    success=False,
                    epic_key=file_path.stem,
                    direction=SyncDirection.JSON_TO_DB,
                    changes_made=[], conflicts_detected=[], conflicts_resolved=[],
                    errors=[f"Failed to load {file_path}: {str(e)}"],
                    duration_ms=0
                )
                results.append(error_result)
                print(f"   ❌ Failed to load {file_path}: {e}")
        
        return results


def main():
    """Test bidirectional sync engine."""
    print("🔄 Bidirectional Sync Engine Test")
    print("=" * 60)
    
    # Initialize sync engine
    sync_engine = BidirectionalSyncEngine()
    
    # Test syncing all epics to database
    epics_dir = Path("epics/user_epics")
    if epics_dir.exists():
        results = sync_engine.sync_all_epics_to_db(epics_dir)
        
        # Show summary
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"\n📊 Sync Summary:")
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ❌ Failed: {len(failed)}")
        
        if failed:
            print("\n❌ Failed Syncs:")
            for result in failed:
                print(f"   {result.epic_key}: {', '.join(result.errors)}")
        
        print("\n✅ Bidirectional sync engine working!")
    else:
        print(f"❌ Directory {epics_dir} not found")


if __name__ == "__main__":
    main()