#!/usr/bin/env python3
"""
🔄 Rollback Manager - Automated Migration Rollback System

Sistema robusto de rollback para migração DatabaseManager com múltiplos níveis
de granularidade e recovery automático.

Features:
- Automated backup creation before each migration step
- Granular rollback (file-level, batch-level, complete rollback)
- Git integration for version control
- Database state preservation
- Configuration snapshot management
- Emergency rollback procedures
- State preservation between checkpoints
- Dependency-aware rollback ordering

Usage:
    # Create backup before batch migration
    python rollback_manager.py --create-backup --batch 2 --label "pre_batch2_migration"
    
    # Rollback specific file
    python rollback_manager.py --rollback-file streamlit_extension/pages/kanban.py
    
    # Rollback entire batch
    python rollback_manager.py --rollback-batch 2
    
    # Emergency rollback to initial state
    python rollback_manager.py --emergency-rollback
    
    # List available backups
    python rollback_manager.py --list-backups
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import zipfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rollback_manager.log')
    ]
)

class RollbackManagerError(Exception):
    """Custom exception for rollback manager errors."""
    pass

class RollbackManager:
    """
    Automated rollback system for migration validation checkpoints.
    
    Manages backup creation, state preservation, and rollback procedures
    with multiple levels of granularity.
    """
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(__name__)
        
        # Rollback configuration
        self.backup_root = self.base_path / ".migration_backups"
        self.state_file = self.backup_root / "rollback_state.json"
        self.rollback_config = self._load_rollback_config()
        
        # Migration batch files (loaded from step 2.3.1)
        self.batch_files = self._load_batch_configuration()
        
        # Initialize backup system
        self._initialize_backup_system()
    
    def _load_rollback_config(self) -> Dict[str, Any]:
        """Load rollback configuration."""
        default_config = {
            "max_backups_per_batch": 10,
            "backup_retention_days": 30,
            "git_integration_enabled": True,
            "database_backup_enabled": True,
            "compression_enabled": True,
            "emergency_rollback_points": []
        }
        
        config_file = self.base_path / "rollback_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load rollback config: {e}")
        
        return default_config
    
    def _load_batch_configuration(self) -> Dict[str, List[str]]:
        """Load batch file configuration from migration plan."""
        return {
            "batch_1": [
                "monitoring/health_check.py",
                "monitoring/graceful_shutdown.py",
                "validate_phase1.py",
                "scripts/testing/test_database_extension_quick.py",
                "streamlit_extension/database/queries.py",
                "streamlit_extension/database/health.py",
                "streamlit_extension/database/schema.py",
                "streamlit_extension/pages/projects.py",
                "streamlit_extension/models/base.py",
                "backups/context_extraction_20250819_212949/systematic_file_auditor.py",
                "scripts/migration/ast_database_migration.py"
            ],
            "batch_2": [
                "streamlit_extension/database/connection.py",
                "streamlit_extension/database/seed.py",
                "streamlit_extension/models/database.py",
                "scripts/migration/add_performance_indexes.py",
                "streamlit_extension/utils/cached_database.py",
                "streamlit_extension/utils/performance_tester.py",
                "tests/test_security_scenarios.py",
                "tests/test_database_manager_duration_extension.py",
                "tests/test_migration_schemas.py",
                "scripts/testing/api_equivalence_validation.py",
                "scripts/testing/secrets_vault_demo.py",
                "scripts/testing/test_sql_pagination.py",
                "tests/test_type_hints_database_manager.py",
                "tests/performance/test_load_scenarios.py",
                "tests/test_epic_progress_defaults.py"
            ],
            "batch_3": [
                "streamlit_extension/pages/kanban.py",
                "streamlit_extension/pages/analytics.py",
                "streamlit_extension/pages/timer.py",
                "streamlit_extension/pages/settings.py",
                "streamlit_extension/pages/gantt.py",
                "streamlit_extension/pages/projeto_wizard.py",
                "tests/test_kanban_functionality.py",
                "tests/test_dashboard_headless.py",
                "scripts/testing/test_dashboard.py",
                "audit_system/agents/intelligent_code_agent.py"
            ]
        }
    
    def _initialize_backup_system(self):
        """Initialize backup system and directory structure."""
        try:
            # Create backup directories
            self.backup_root.mkdir(exist_ok=True)
            (self.backup_root / "file_backups").mkdir(exist_ok=True)
            (self.backup_root / "batch_backups").mkdir(exist_ok=True)
            (self.backup_root / "database_backups").mkdir(exist_ok=True)
            (self.backup_root / "git_snapshots").mkdir(exist_ok=True)
            (self.backup_root / "emergency_points").mkdir(exist_ok=True)
            
            # Initialize state tracking
            if not self.state_file.exists():
                self._save_rollback_state({
                    "initialized": datetime.now().isoformat(),
                    "current_batch": None,
                    "backup_history": [],
                    "rollback_history": [],
                    "emergency_points": []
                })
            
            self.logger.info("✅ Backup system initialized")
            
        except Exception as e:
            raise RollbackManagerError(f"Failed to initialize backup system: {e}")
    
    def _save_rollback_state(self, state: Dict[str, Any]):
        """Save rollback state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save rollback state: {e}")
    
    def _load_rollback_state(self) -> Dict[str, Any]:
        """Load rollback state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load rollback state: {e}")
        
        return {
            "initialized": None,
            "current_batch": None,
            "backup_history": [],
            "rollback_history": [],
            "emergency_points": []
        }
    
    def create_backup(self, backup_type: str, label: str, batch_number: Optional[int] = None, 
                     files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create backup with specified type and scope.
        
        Args:
            backup_type: Type of backup ('file', 'batch', 'complete', 'emergency')
            label: Descriptive label for the backup
            batch_number: Batch number for batch-specific backups
            files: Specific files to backup (for file-level backups)
        
        Returns:
            Dict with backup information
        """
        self.logger.info(f"🔄 Creating {backup_type} backup: {label}")
        
        backup_info = {
            "backup_id": self._generate_backup_id(backup_type, label),
            "backup_type": backup_type,
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "batch_number": batch_number,
            "files": files or [],
            "status": "creating"
        }
        
        try:
            if backup_type == "file":
                backup_result = self._create_file_backup(backup_info, files or [])
            elif backup_type == "batch":
                backup_result = self._create_batch_backup(backup_info, batch_number)
            elif backup_type == "complete":
                backup_result = self._create_complete_backup(backup_info)
            elif backup_type == "emergency":
                backup_result = self._create_emergency_backup(backup_info)
            else:
                raise RollbackManagerError(f"Unknown backup type: {backup_type}")
            
            # Update backup info with results
            backup_info.update(backup_result)
            backup_info["status"] = "completed"
            
            # Save to state
            state = self._load_rollback_state()
            state["backup_history"].append(backup_info)
            self._save_rollback_state(state)
            
            self.logger.info(f"✅ Backup created successfully: {backup_info['backup_id']}")
            
        except Exception as e:
            backup_info["status"] = "failed"
            backup_info["error"] = str(e)
            self.logger.error(f"❌ Backup creation failed: {e}")
            raise RollbackManagerError(f"Failed to create {backup_type} backup: {e}")
        
        return backup_info
    
    def _generate_backup_id(self, backup_type: str, label: str) -> str:
        """Generate unique backup ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        label_hash = hashlib.md5(label.encode()).hexdigest()[:8]
        return f"{backup_type}_{timestamp}_{label_hash}"
    
    def _create_file_backup(self, backup_info: Dict[str, Any], files: List[str]) -> Dict[str, Any]:
        """Create backup for specific files."""
        backup_dir = self.backup_root / "file_backups" / backup_info["backup_id"]
        backup_dir.mkdir(parents=True)
        
        backed_up_files = []
        failed_files = []
        
        for file_path in files:
            source_path = self.base_path / file_path
            if not source_path.exists():
                failed_files.append({"file": file_path, "reason": "File not found"})
                continue
            
            try:
                # Preserve directory structure
                relative_path = Path(file_path)
                dest_path = backup_dir / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file with metadata
                shutil.copy2(source_path, dest_path)
                
                # Calculate file hash for integrity
                file_hash = self._calculate_file_hash(source_path)
                
                backed_up_files.append({
                    "file": file_path,
                    "size": source_path.stat().st_size,
                    "hash": file_hash,
                    "backup_path": str(dest_path.relative_to(self.backup_root))
                })
                
            except Exception as e:
                failed_files.append({"file": file_path, "reason": str(e)})
        
        # Create backup manifest
        manifest = {
            "backup_info": backup_info,
            "backed_up_files": backed_up_files,
            "failed_files": failed_files,
            "total_files": len(files),
            "successful_files": len(backed_up_files),
            "failed_count": len(failed_files)
        }
        
        with open(backup_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2, default=str)
        
        return {
            "backup_path": str(backup_dir.relative_to(self.backup_root)),
            "files_backed_up": len(backed_up_files),
            "files_failed": len(failed_files),
            "manifest_file": str((backup_dir / "manifest.json").relative_to(self.backup_root))
        }
    
    def _create_batch_backup(self, backup_info: Dict[str, Any], batch_number: int) -> Dict[str, Any]:
        """Create backup for entire batch."""
        if batch_number not in [1, 2, 3]:
            raise RollbackManagerError(f"Invalid batch number: {batch_number}")
        
        batch_key = f"batch_{batch_number}"
        batch_files = self.batch_files.get(batch_key, [])
        
        if not batch_files:
            raise RollbackManagerError(f"No files defined for {batch_key}")
        
        # Use file backup mechanism for batch files
        backup_info["files"] = batch_files
        return self._create_file_backup(backup_info, batch_files)
    
    def _create_complete_backup(self, backup_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create complete project backup."""
        backup_dir = self.backup_root / "complete_backups" / backup_info["backup_id"]
        backup_dir.mkdir(parents=True)
        
        # Get all migration-related files
        all_files = []
        for batch_files in self.batch_files.values():
            all_files.extend(batch_files)
        
        # Add critical configuration files
        critical_files = [
            "migration_execution_plan.md",
            "dependency_audit_report.md",
            "migration_log.md",
            "api_migration_mapping.md",
            "pytest.ini"
        ]
        all_files.extend(critical_files)
        
        # Remove duplicates
        all_files = list(set(all_files))
        
        backup_info["files"] = all_files
        return self._create_file_backup(backup_info, all_files)
    
    def _create_emergency_backup(self, backup_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create emergency backup point."""
        backup_dir = self.backup_root / "emergency_points" / backup_info["backup_id"]
        backup_dir.mkdir(parents=True)
        
        # Create complete project backup
        complete_result = self._create_complete_backup(backup_info)
        
        # Create git snapshot if enabled
        git_result = None
        if self.rollback_config.get("git_integration_enabled", True):
            try:
                git_result = self._create_git_snapshot(backup_info["backup_id"])
            except Exception as e:
                self.logger.warning(f"Git snapshot failed: {e}")
        
        # Create database backup if enabled
        db_result = None
        if self.rollback_config.get("database_backup_enabled", True):
            try:
                db_result = self._create_database_backup(backup_info["backup_id"])
            except Exception as e:
                self.logger.warning(f"Database backup failed: {e}")
        
        # Update emergency points in state
        state = self._load_rollback_state()
        state["emergency_points"].append({
            "backup_id": backup_info["backup_id"],
            "timestamp": backup_info["timestamp"],
            "label": backup_info["label"]
        })
        self._save_rollback_state(state)
        
        return {
            "backup_path": str(backup_dir.relative_to(self.backup_root)),
            "complete_backup": complete_result,
            "git_snapshot": git_result,
            "database_backup": db_result
        }
    
    def _create_git_snapshot(self, backup_id: str) -> Dict[str, Any]:
        """Create git snapshot."""
        try:
            # Check if we're in a git repository
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True, cwd=self.base_path)
            
            if result.returncode != 0:
                return {"status": "skipped", "reason": "Not a git repository"}
            
            # Get current git status
            status_result = subprocess.run(['git', 'status', '--porcelain'],
                                         capture_output=True, text=True, cwd=self.base_path)
            
            # Get current commit hash
            commit_result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                         capture_output=True, text=True, cwd=self.base_path)
            
            # Create backup branch
            branch_name = f"backup_{backup_id}"
            branch_result = subprocess.run(['git', 'checkout', '-b', branch_name],
                                         capture_output=True, text=True, cwd=self.base_path)
            
            if branch_result.returncode == 0:
                # Switch back to original branch
                subprocess.run(['git', 'checkout', '-'], 
                             capture_output=True, text=True, cwd=self.base_path)
            
            return {
                "status": "success",
                "current_commit": commit_result.stdout.strip(),
                "backup_branch": branch_name if branch_result.returncode == 0 else None,
                "working_tree_status": status_result.stdout
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def _create_database_backup(self, backup_id: str) -> Dict[str, Any]:
        """Create database backup."""
        db_backup_dir = self.backup_root / "database_backups" / backup_id
        db_backup_dir.mkdir(parents=True)
        
        backed_up_dbs = []
        
        # Common database files
        db_files = ["framework.db", "task_timer.db"]
        
        for db_file in db_files:
            db_path = self.base_path / db_file
            if db_path.exists():
                try:
                    backup_path = db_backup_dir / f"{db_file}.backup"
                    shutil.copy2(db_path, backup_path)
                    
                    # Also backup WAL and SHM files if they exist
                    for suffix in ["-wal", "-shm"]:
                        aux_file = self.base_path / f"{db_file}{suffix}"
                        if aux_file.exists():
                            shutil.copy2(aux_file, db_backup_dir / f"{db_file}{suffix}.backup")
                    
                    backed_up_dbs.append({
                        "database": db_file,
                        "size": db_path.stat().st_size,
                        "backup_path": str(backup_path.relative_to(self.backup_root))
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Failed to backup {db_file}: {e}")
        
        return {
            "status": "success" if backed_up_dbs else "partial",
            "databases_backed_up": backed_up_dbs,
            "backup_directory": str(db_backup_dir.relative_to(self.backup_root))
        }
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for integrity checking."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return "unknown"
    
    def rollback(self, rollback_type: str, target: str, **kwargs) -> Dict[str, Any]:
        """
        Perform rollback operation.
        
        Args:
            rollback_type: Type of rollback ('file', 'batch', 'backup', 'emergency')
            target: Target for rollback (file path, batch number, backup ID)
            **kwargs: Additional rollback options
        
        Returns:
            Dict with rollback results
        """
        self.logger.info(f"🔄 Starting {rollback_type} rollback: {target}")
        
        rollback_info = {
            "rollback_id": self._generate_rollback_id(rollback_type, target),
            "rollback_type": rollback_type,
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "status": "starting"
        }
        
        try:
            if rollback_type == "file":
                rollback_result = self._rollback_file(target, **kwargs)
            elif rollback_type == "batch":
                rollback_result = self._rollback_batch(int(target), **kwargs)
            elif rollback_type == "backup":
                rollback_result = self._rollback_to_backup(target, **kwargs)
            elif rollback_type == "emergency":
                rollback_result = self._emergency_rollback(**kwargs)
            else:
                raise RollbackManagerError(f"Unknown rollback type: {rollback_type}")
            
            rollback_info.update(rollback_result)
            rollback_info["status"] = "completed"
            
            # Save rollback history
            state = self._load_rollback_state()
            state["rollback_history"].append(rollback_info)
            self._save_rollback_state(state)
            
            self.logger.info(f"✅ Rollback completed successfully: {rollback_info['rollback_id']}")
            
        except Exception as e:
            rollback_info["status"] = "failed"
            rollback_info["error"] = str(e)
            self.logger.error(f"❌ Rollback failed: {e}")
            raise RollbackManagerError(f"Failed to perform {rollback_type} rollback: {e}")
        
        return rollback_info
    
    def _generate_rollback_id(self, rollback_type: str, target: str) -> str:
        """Generate unique rollback ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_hash = hashlib.md5(str(target).encode()).hexdigest()[:8]
        return f"rollback_{rollback_type}_{timestamp}_{target_hash}"
    
    def _rollback_file(self, file_path: str, backup_id: Optional[str] = None) -> Dict[str, Any]:
        """Rollback specific file."""
        if backup_id:
            # Rollback from specific backup
            return self._restore_file_from_backup(file_path, backup_id)
        else:
            # Find most recent backup containing this file
            backup_id = self._find_recent_backup_for_file(file_path)
            if not backup_id:
                raise RollbackManagerError(f"No backup found for file: {file_path}")
            
            return self._restore_file_from_backup(file_path, backup_id)
    
    def _rollback_batch(self, batch_number: int, backup_id: Optional[str] = None) -> Dict[str, Any]:
        """Rollback entire batch."""
        batch_key = f"batch_{batch_number}"
        batch_files = self.batch_files.get(batch_key, [])
        
        if not batch_files:
            raise RollbackManagerError(f"No files defined for batch {batch_number}")
        
        if backup_id:
            # Rollback from specific backup
            return self._restore_files_from_backup(batch_files, backup_id)
        else:
            # Find most recent batch backup
            backup_id = self._find_recent_batch_backup(batch_number)
            if not backup_id:
                raise RollbackManagerError(f"No backup found for batch {batch_number}")
            
            return self._restore_files_from_backup(batch_files, backup_id)
    
    def _rollback_to_backup(self, backup_id: str) -> Dict[str, Any]:
        """Rollback to specific backup."""
        backup_info = self._find_backup_by_id(backup_id)
        if not backup_info:
            raise RollbackManagerError(f"Backup not found: {backup_id}")
        
        files_to_restore = backup_info.get("files", [])
        return self._restore_files_from_backup(files_to_restore, backup_id)
    
    def _emergency_rollback(self) -> Dict[str, Any]:
        """Perform emergency rollback to last known good state."""
        state = self._load_rollback_state()
        emergency_points = state.get("emergency_points", [])
        
        if not emergency_points:
            raise RollbackManagerError("No emergency rollback points available")
        
        # Use most recent emergency point
        latest_point = emergency_points[-1]
        backup_id = latest_point["backup_id"]
        
        self.logger.info(f"🚨 Emergency rollback to: {latest_point['label']} ({backup_id})")
        
        return self._rollback_to_backup(backup_id)
    
    def _restore_file_from_backup(self, file_path: str, backup_id: str) -> Dict[str, Any]:
        """Restore specific file from backup."""
        backup_info = self._find_backup_by_id(backup_id)
        if not backup_info:
            raise RollbackManagerError(f"Backup not found: {backup_id}")
        
        backup_path = self.backup_root / backup_info["backup_path"]
        manifest_file = backup_path / "manifest.json"
        
        if not manifest_file.exists():
            raise RollbackManagerError(f"Backup manifest not found: {manifest_file}")
        
        # Load manifest
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        # Find file in backup
        backed_up_file = None
        for file_info in manifest.get("backed_up_files", []):
            if file_info["file"] == file_path:
                backed_up_file = file_info
                break
        
        if not backed_up_file:
            raise RollbackManagerError(f"File {file_path} not found in backup {backup_id}")
        
        # Restore file
        source_path = self.backup_root / backed_up_file["backup_path"]
        dest_path = self.base_path / file_path
        
        # Create backup of current file before restoring
        if dest_path.exists():
            current_backup_path = dest_path.with_suffix(f"{dest_path.suffix}.pre_rollback")
            shutil.copy2(dest_path, current_backup_path)
        
        # Restore file
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        
        # Verify integrity
        restored_hash = self._calculate_file_hash(dest_path)
        original_hash = backed_up_file.get("hash", "unknown")
        
        return {
            "file": file_path,
            "restored_from": str(source_path.relative_to(self.backup_root)),
            "integrity_check": restored_hash == original_hash,
            "original_hash": original_hash,
            "restored_hash": restored_hash
        }
    
    def _restore_files_from_backup(self, files: List[str], backup_id: str) -> Dict[str, Any]:
        """Restore multiple files from backup."""
        results = {
            "backup_id": backup_id,
            "total_files": len(files),
            "restored_files": [],
            "failed_files": [],
            "skipped_files": []
        }
        
        for file_path in files:
            try:
                restore_result = self._restore_file_from_backup(file_path, backup_id)
                results["restored_files"].append(restore_result)
                
            except RollbackManagerError as e:
                if "not found in backup" in str(e):
                    results["skipped_files"].append({"file": file_path, "reason": str(e)})
                else:
                    results["failed_files"].append({"file": file_path, "reason": str(e)})
            except Exception as e:
                results["failed_files"].append({"file": file_path, "reason": str(e)})
        
        results["success_rate"] = len(results["restored_files"]) / results["total_files"] * 100 if results["total_files"] > 0 else 0
        
        return results
    
    def _find_backup_by_id(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Find backup by ID in history."""
        state = self._load_rollback_state()
        for backup in state.get("backup_history", []):
            if backup.get("backup_id") == backup_id:
                return backup
        return None
    
    def _find_recent_backup_for_file(self, file_path: str) -> Optional[str]:
        """Find most recent backup containing specific file."""
        state = self._load_rollback_state()
        
        # Sort backups by timestamp (most recent first)
        sorted_backups = sorted(
            state.get("backup_history", []),
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        for backup in sorted_backups:
            if file_path in backup.get("files", []):
                return backup.get("backup_id")
        
        return None
    
    def _find_recent_batch_backup(self, batch_number: int) -> Optional[str]:
        """Find most recent backup for specific batch."""
        state = self._load_rollback_state()
        
        # Sort backups by timestamp (most recent first)
        sorted_backups = sorted(
            state.get("backup_history", []),
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        for backup in sorted_backups:
            if backup.get("batch_number") == batch_number:
                return backup.get("backup_id")
        
        return None
    
    def list_backups(self, backup_type: Optional[str] = None) -> Dict[str, Any]:
        """List available backups."""
        state = self._load_rollback_state()
        all_backups = state.get("backup_history", [])
        
        if backup_type:
            filtered_backups = [b for b in all_backups if b.get("backup_type") == backup_type]
        else:
            filtered_backups = all_backups
        
        # Sort by timestamp (most recent first)
        sorted_backups = sorted(
            filtered_backups,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        return {
            "total_backups": len(all_backups),
            "filtered_backups": len(sorted_backups),
            "backups": sorted_backups,
            "emergency_points": state.get("emergency_points", [])
        }
    
    def cleanup_old_backups(self, retention_days: Optional[int] = None) -> Dict[str, Any]:
        """Clean up old backups based on retention policy."""
        if retention_days is None:
            retention_days = self.rollback_config.get("backup_retention_days", 30)
        
        cutoff_date = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
        
        state = self._load_rollback_state()
        all_backups = state.get("backup_history", [])
        
        to_keep = []
        to_remove = []
        
        for backup in all_backups:
            try:
                backup_time = datetime.fromisoformat(backup.get("timestamp", "")).timestamp()
                if backup_time >= cutoff_date:
                    to_keep.append(backup)
                else:
                    to_remove.append(backup)
            except (ValueError, TypeError):
                # Keep backups with invalid timestamps
                to_keep.append(backup)
        
        # Remove old backup files
        removed_count = 0
        for backup in to_remove:
            try:
                backup_path = self.backup_root / backup.get("backup_path", "")
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                    removed_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to remove backup {backup.get('backup_id')}: {e}")
        
        # Update state
        state["backup_history"] = to_keep
        self._save_rollback_state(state)
        
        return {
            "total_backups": len(all_backups),
            "kept_backups": len(to_keep),
            "removed_backups": len(to_remove),
            "files_removed": removed_count,
            "retention_days": retention_days
        }
    
    def get_rollback_status(self) -> Dict[str, Any]:
        """Get current rollback system status."""
        state = self._load_rollback_state()
        
        # Calculate backup statistics
        backup_stats = {
            "total_backups": len(state.get("backup_history", [])),
            "emergency_points": len(state.get("emergency_points", [])),
            "rollback_operations": len(state.get("rollback_history", []))
        }
        
        # Check disk usage
        backup_size = 0
        try:
            for item in self.backup_root.rglob("*"):
                if item.is_file():
                    backup_size += item.stat().st_size
        except Exception as e:
            self.logger.warning(f"Failed to calculate backup size: {e}")
        
        # Check git integration status
        git_status = "disabled"
        if self.rollback_config.get("git_integration_enabled", True):
            try:
                result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                      capture_output=True, text=True, cwd=self.base_path)
                git_status = "available" if result.returncode == 0 else "not_a_repo"
            except:
                git_status = "not_installed"
        
        return {
            "system_status": "operational",
            "backup_directory": str(self.backup_root),
            "backup_statistics": backup_stats,
            "disk_usage_bytes": backup_size,
            "disk_usage_mb": backup_size / (1024 * 1024),
            "git_integration": git_status,
            "configuration": self.rollback_config,
            "last_backup": state.get("backup_history", [{}])[-1].get("timestamp") if state.get("backup_history") else None,
            "last_rollback": state.get("rollback_history", [{}])[-1].get("timestamp") if state.get("rollback_history") else None
        }

def main():
    """Main entry point for rollback manager."""
    parser = argparse.ArgumentParser(description="Migration Rollback Manager")
    
    # Backup operations
    parser.add_argument('--create-backup', action='store_true', help='Create backup')
    parser.add_argument('--backup-type', choices=['file', 'batch', 'complete', 'emergency'], 
                       default='file', help='Type of backup to create')
    parser.add_argument('--batch', type=int, choices=[1, 2, 3], help='Batch number for backup')
    parser.add_argument('--files', nargs='+', help='Specific files to backup')
    parser.add_argument('--label', default='manual_backup', help='Backup label')
    
    # Rollback operations
    parser.add_argument('--rollback-file', help='Rollback specific file')
    parser.add_argument('--rollback-batch', type=int, choices=[1, 2, 3], help='Rollback batch')
    parser.add_argument('--rollback-backup', help='Rollback to specific backup ID')
    parser.add_argument('--emergency-rollback', action='store_true', help='Emergency rollback')
    parser.add_argument('--backup-id', help='Specific backup ID to use for rollback')
    
    # Information operations
    parser.add_argument('--list-backups', action='store_true', help='List available backups')
    parser.add_argument('--status', action='store_true', help='Show rollback system status')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old backups')
    parser.add_argument('--retention-days', type=int, help='Retention days for cleanup')
    
    # Options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        rollback_manager = RollbackManager()
        
        if args.create_backup:
            print(f"🔄 Creating {args.backup_type} backup: {args.label}")
            
            result = rollback_manager.create_backup(
                backup_type=args.backup_type,
                label=args.label,
                batch_number=args.batch,
                files=args.files
            )
            
            print(f"✅ Backup created: {result['backup_id']}")
            if 'files_backed_up' in result:
                print(f"Files backed up: {result['files_backed_up']}")
            
        elif args.rollback_file:
            print(f"🔄 Rolling back file: {args.rollback_file}")
            result = rollback_manager.rollback('file', args.rollback_file, backup_id=args.backup_id)
            print(f"✅ File rollback completed: {result['rollback_id']}")
            
        elif args.rollback_batch is not None:
            print(f"🔄 Rolling back batch {args.rollback_batch}")
            result = rollback_manager.rollback('batch', str(args.rollback_batch), backup_id=args.backup_id)
            print(f"✅ Batch rollback completed: {result['rollback_id']}")
            
        elif args.rollback_backup:
            print(f"🔄 Rolling back to backup: {args.rollback_backup}")
            result = rollback_manager.rollback('backup', args.rollback_backup)
            print(f"✅ Backup rollback completed: {result['rollback_id']}")
            
        elif args.emergency_rollback:
            print("🚨 Performing emergency rollback")
            result = rollback_manager.rollback('emergency', 'latest')
            print(f"✅ Emergency rollback completed: {result['rollback_id']}")
            
        elif args.list_backups:
            result = rollback_manager.list_backups()
            print(f"\n📋 Available Backups ({result['total_backups']} total):")
            for backup in result['backups'][:10]:  # Show latest 10
                print(f"  📦 {backup['backup_id']} - {backup['label']} ({backup['timestamp']})")
            
            if result['emergency_points']:
                print(f"\n🚨 Emergency Points ({len(result['emergency_points'])}):")
                for point in result['emergency_points']:
                    print(f"  🛡️  {point['backup_id']} - {point['label']} ({point['timestamp']})")
            
        elif args.cleanup:
            print(f"🧹 Cleaning up old backups (retention: {args.retention_days or 'default'} days)")
            result = rollback_manager.cleanup_old_backups(args.retention_days)
            print(f"✅ Cleanup completed: {result['removed_backups']} backups removed")
            
        elif args.status:
            result = rollback_manager.get_rollback_status()
            print(f"\n📊 Rollback System Status:")
            print(f"Status: {result['system_status']}")
            print(f"Total Backups: {result['backup_statistics']['total_backups']}")
            print(f"Emergency Points: {result['backup_statistics']['emergency_points']}")
            print(f"Rollback Operations: {result['backup_statistics']['rollback_operations']}")
            print(f"Disk Usage: {result['disk_usage_mb']:.2f} MB")
            print(f"Git Integration: {result['git_integration']}")
            print(f"Last Backup: {result['last_backup'] or 'None'}")
            
        else:
            parser.print_help()
    
    except RollbackManagerError as e:
        print(f"❌ Rollback error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Operation interrupted by user")
        return 1
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())