#!/usr/bin/env python3
"""
🔄 Rollback Context Changes - Automated Rollback System

Sistema automatizado de rollback para desfazer mudanças do context extraction system
em caso de falhas ou problemas detectados durante a implementação.

Usage:
    python scripts/automated_audit/rollback_context_changes.py [options]

Features:
- Granular rollback by component
- Automatic rollback triggers
- Safe rollback procedures
- Verification of rollback success
- Emergency restore capabilities
- Rollback history tracking

Created: 2025-08-19 (Sétima Camada - Context Extraction System)
"""

import os
import sys
import json
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import tempfile
import hashlib


class RollbackComponent(Enum):
    """Components that can be rolled back."""
    CONTEXT_VALIDATOR = "context_validator"
    INTEGRATION_TESTER = "integration_tester"
    CLAUDE_MD_FILES = "claude_md_files"
    CONTEXT_EXTRACTION_SCRIPTS = "context_extraction_scripts"
    INDEX_MD_ENHANCEMENTS = "index_md_enhancements"
    INTEGRATION_DOCUMENTS = "integration_documents"
    SYSTEMATIC_AUDITOR_CHANGES = "systematic_auditor_changes"
    ALL_COMPONENTS = "all_components"


class RollbackType(Enum):
    """Types of rollback operations."""
    PARTIAL = "partial"          # Rollback specific component
    INCREMENTAL = "incremental"  # Rollback last change only
    COMPLETE = "complete"        # Full rollback to golden state
    EMERGENCY = "emergency"      # Emergency restore


class RollbackStatus(Enum):
    """Status of rollback operations."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"
    VERIFICATION_FAILED = "verification_failed"


@dataclass
class RollbackOperation:
    """Details of a rollback operation."""
    component: RollbackComponent
    rollback_type: RollbackType
    timestamp: str
    files_affected: List[str]
    backup_source: str
    verification_passed: bool
    status: RollbackStatus
    error_message: Optional[str] = None


@dataclass
class RollbackPlan:
    """Plan for rollback operations."""
    operations: List[RollbackOperation]
    total_components: int
    estimated_time_minutes: int
    risks: List[str]
    verification_steps: List[str]


class RollbackManager:
    """Main rollback management system."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize rollback manager."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.logger = logging.getLogger(f"{__name__}.RollbackManager")
        
        # Backup directory
        self.backup_dir = self.project_root / "backups"
        
        # Context extraction backup (created during validation phase)
        self.context_backup_dir = self.backup_dir / "context_extraction_20250819_212949"
        
        # Emergency restore script
        self.emergency_restore_script = self.backup_dir / "EMERGENCY_RESTORE_context_extraction_20250819_212949.sh"
        
        # Rollback history
        self.rollback_history_file = self.backup_dir / "rollback_history.json"
        self.rollback_history = self._load_rollback_history()
        
        # Component file mappings
        self.component_files = {
            RollbackComponent.CONTEXT_VALIDATOR: [
                "scripts/automated_audit/context_validator.py"
            ],
            RollbackComponent.INTEGRATION_TESTER: [
                "scripts/automated_audit/integration_tester.py"
            ],
            RollbackComponent.CLAUDE_MD_FILES: [
                "streamlit_extension/utils/CLAUDE.md",
                "streamlit_extension/models/CLAUDE.md", 
                "streamlit_extension/endpoints/CLAUDE.md",
                "streamlit_extension/auth/CLAUDE.md"  # If modified
            ],
            RollbackComponent.CONTEXT_EXTRACTION_SCRIPTS: [
                "scripts/automated_audit/context_extractors/context_root.sh",
                "scripts/automated_audit/context_extractors/context_streamlit.sh",
                "scripts/automated_audit/context_extractors/context_duration.sh",
                # Add more as they're created
            ],
            RollbackComponent.INDEX_MD_ENHANCEMENTS: [
                "INDEX.md"
            ],
            RollbackComponent.INTEGRATION_DOCUMENTS: [
                "scripts/automated_audit/CONTEXT_INTEGRATION_MAP.md",
                "scripts/automated_audit/CONTEXT_VALIDATION_RULES.md",
                "scripts/automated_audit/CONTEXT_DEPENDENCY_GRAPH.md"
            ],
            RollbackComponent.SYSTEMATIC_AUDITOR_CHANGES: [
                "scripts/automated_audit/systematic_file_auditor.py"
            ]
        }
        
    def _load_rollback_history(self) -> List[Dict[str, Any]]:
        """Load rollback history from file."""
        if self.rollback_history_file.exists():
            try:
                with open(self.rollback_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load rollback history: {e}")
        return []
    
    def _save_rollback_history(self) -> None:
        """Save rollback history to file."""
        try:
            self.backup_dir.mkdir(exist_ok=True)
            with open(self.rollback_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.rollback_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save rollback history: {e}")
    
    def create_rollback_plan(self, components: List[RollbackComponent], rollback_type: RollbackType) -> RollbackPlan:
        """Create a rollback plan for specified components."""
        self.logger.info(f"Creating rollback plan for {len(components)} components")
        
        operations = []
        risks = []
        verification_steps = []
        
        for component in components:
            if component == RollbackComponent.ALL_COMPONENTS:
                # Handle ALL_COMPONENTS specially
                all_components = [c for c in RollbackComponent if c != RollbackComponent.ALL_COMPONENTS]
                return self.create_rollback_plan(all_components, rollback_type)
            
            # Get files for this component
            files = self.component_files.get(component, [])
            
            # Check which files exist and need rollback
            files_to_rollback = []
            for file_path in files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    files_to_rollback.append(file_path)
            
            if files_to_rollback:
                operation = RollbackOperation(
                    component=component,
                    rollback_type=rollback_type,
                    timestamp=self._get_timestamp(),
                    files_affected=files_to_rollback,
                    backup_source=str(self.context_backup_dir),
                    verification_passed=False,
                    status=RollbackStatus.SUCCESS
                )
                operations.append(operation)
                
                # Add component-specific risks
                if component == RollbackComponent.SYSTEMATIC_AUDITOR_CHANGES:
                    risks.append("Rolling back systematic auditor may affect ongoing audit processes")
                elif component == RollbackComponent.INDEX_MD_ENHANCEMENTS:
                    risks.append("INDEX.md rollback may break navigation")
                
                # Add verification steps
                verification_steps.append(f"Verify {component.value} functionality after rollback")
        
        # General risks
        if rollback_type == RollbackType.COMPLETE:
            risks.append("Complete rollback will lose all context extraction work")
        
        # Estimated time (rough estimate)
        estimated_time = len(operations) * 2  # 2 minutes per component
        
        plan = RollbackPlan(
            operations=operations,
            total_components=len(operations),
            estimated_time_minutes=estimated_time,
            risks=risks,
            verification_steps=verification_steps
        )
        
        self.logger.info(f"Rollback plan created: {len(operations)} operations, ~{estimated_time} minutes")
        return plan
    
    def execute_rollback_plan(self, plan: RollbackPlan, dry_run: bool = False) -> List[RollbackOperation]:
        """Execute rollback plan."""
        self.logger.info(f"Executing rollback plan: {plan.total_components} operations (dry_run={dry_run})")
        
        if dry_run:
            self.logger.info("DRY RUN MODE - No actual changes will be made")
        
        executed_operations = []
        
        for operation in plan.operations:
            try:
                self.logger.info(f"Executing rollback for {operation.component.value}")
                
                if not dry_run:
                    # Perform actual rollback
                    success = self._rollback_component(operation)
                    operation.verification_passed = success
                    operation.status = RollbackStatus.SUCCESS if success else RollbackStatus.FAILED
                else:
                    # Simulate rollback
                    operation.verification_passed = True
                    operation.status = RollbackStatus.SUCCESS
                
                executed_operations.append(operation)
                
                # Record in history
                if not dry_run:
                    self.rollback_history.append(asdict(operation))
                
            except Exception as e:
                self.logger.error(f"Rollback failed for {operation.component.value}: {e}")
                operation.status = RollbackStatus.FAILED
                operation.error_message = str(e)
                executed_operations.append(operation)
                
                # Continue with other operations
                continue
        
        # Save history
        if not dry_run:
            self._save_rollback_history()
        
        # Summary
        success_count = sum(1 for op in executed_operations if op.status == RollbackStatus.SUCCESS)
        self.logger.info(f"Rollback execution complete: {success_count}/{len(executed_operations)} successful")
        
        return executed_operations
    
    def _rollback_component(self, operation: RollbackOperation) -> bool:
        """Rollback a specific component."""
        try:
            # Verify backup exists
            if not self.context_backup_dir.exists():
                self.logger.error(f"Backup directory not found: {self.context_backup_dir}")
                return False
            
            success_count = 0
            total_files = len(operation.files_affected)
            
            for file_path in operation.files_affected:
                if self._rollback_single_file(file_path):
                    success_count += 1
                else:
                    self.logger.warning(f"Failed to rollback file: {file_path}")
            
            # Consider successful if majority of files were rolled back
            return success_count >= (total_files * 0.8)  # 80% success threshold
            
        except Exception as e:
            self.logger.error(f"Component rollback failed: {e}")
            return False
    
    def _rollback_single_file(self, file_path: str) -> bool:
        """Rollback a single file."""
        try:
            target_file = self.project_root / file_path
            
            # Determine backup file name based on component
            backup_file_name = self._get_backup_file_name(file_path)
            backup_file = self.context_backup_dir / backup_file_name
            
            if not backup_file.exists():
                # Try alternative backup naming
                backup_file = self.context_backup_dir / Path(file_path).name
                
                if not backup_file.exists():
                    self.logger.warning(f"Backup file not found for: {file_path}")
                    return False
            
            # Create parent directory if needed
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy backup to target location
            shutil.copy2(backup_file, target_file)
            
            self.logger.debug(f"Rolled back: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback file {file_path}: {e}")
            return False
    
    def _get_backup_file_name(self, file_path: str) -> str:
        """Get backup file name for given file path."""
        # Convert file path to backup name (from backup creation logic)
        if file_path == "CLAUDE.md":
            return "CLAUDE.md"
        elif file_path == "INDEX.md":
            return "INDEX.md"
        elif file_path == "NAVIGATION.md":
            return "NAVIGATION.md"
        elif "streamlit_extension/services/CLAUDE.md" in file_path:
            return "CLAUDE_streamlit_services.md"
        elif "streamlit_extension/database/CLAUDE.md" in file_path:
            return "CLAUDE_streamlit_database.md"
        elif "streamlit_extension/components/CLAUDE.md" in file_path:
            return "CLAUDE_streamlit_components.md"
        elif "streamlit_extension/auth/CLAUDE.md" in file_path:
            return "CLAUDE_streamlit_auth.md"
        elif "streamlit_extension/CLAUDE.md" in file_path:
            return "CLAUDE_streamlit_main.md"
        elif "scripts/CLAUDE.md" in file_path:
            return "CLAUDE_scripts.md"
        elif "systematic_file_auditor.py" in file_path:
            return "systematic_file_auditor.py"
        else:
            # Default: use just the filename
            return Path(file_path).name
    
    def emergency_restore(self) -> bool:
        """Execute emergency restore using restore script."""
        self.logger.warning("Executing EMERGENCY RESTORE")
        
        if not self.emergency_restore_script.exists():
            self.logger.error(f"Emergency restore script not found: {self.emergency_restore_script}")
            return False
        
        try:
            # Make script executable
            os.chmod(self.emergency_restore_script, 0o755)
            
            # Execute restore script
            result = subprocess.run(
                ["/bin/bash", str(self.emergency_restore_script)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info("Emergency restore completed successfully")
                
                # Record in history
                emergency_op = RollbackOperation(
                    component=RollbackComponent.ALL_COMPONENTS,
                    rollback_type=RollbackType.EMERGENCY,
                    timestamp=self._get_timestamp(),
                    files_affected=["*"],
                    backup_source=str(self.context_backup_dir),
                    verification_passed=True,
                    status=RollbackStatus.SUCCESS
                )
                
                self.rollback_history.append(asdict(emergency_op))
                self._save_rollback_history()
                
                return True
            else:
                self.logger.error(f"Emergency restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Emergency restore exception: {e}")
            return False
    
    def verify_rollback_success(self, operations: List[RollbackOperation]) -> bool:
        """Verify that rollback was successful."""
        self.logger.info("Verifying rollback success")
        
        try:
            # Run basic system integrity test
            result = subprocess.run(
                [sys.executable, "scripts/testing/comprehensive_integrity_test.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            # Check if system is back to working state
            if result.returncode == 0:
                self.logger.info("System integrity verification passed")
                return True
            else:
                self.logger.warning("System integrity verification failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Rollback verification failed: {e}")
            return False
    
    def rollback_last_change(self) -> bool:
        """Rollback only the last change made."""
        self.logger.info("Rolling back last change")
        
        if not self.rollback_history:
            self.logger.warning("No rollback history found")
            return False
        
        # Get the last successful operation
        last_operations = []
        last_timestamp = None
        
        for record in reversed(self.rollback_history):
            if record.get('status') == RollbackStatus.SUCCESS.value:
                if last_timestamp is None:
                    last_timestamp = record.get('timestamp')
                
                if record.get('timestamp') == last_timestamp:
                    last_operations.append(record)
                else:
                    break
        
        if not last_operations:
            self.logger.warning("No successful operations to rollback")
            return False
        
        # Create rollback plan for last operations
        components = [RollbackComponent(op['component']) for op in last_operations]
        plan = self.create_rollback_plan(components, RollbackType.INCREMENTAL)
        
        # Execute rollback
        executed_ops = self.execute_rollback_plan(plan)
        
        # Verify success
        return self.verify_rollback_success(executed_ops)
    
    def list_rollback_options(self) -> Dict[str, Any]:
        """List available rollback options."""
        options = {
            "available_components": [comp.value for comp in RollbackComponent],
            "rollback_types": [rt.value for rt in RollbackType],
            "backup_available": self.context_backup_dir.exists(),
            "emergency_restore_available": self.emergency_restore_script.exists(),
            "rollback_history_count": len(self.rollback_history),
            "last_rollback": self.rollback_history[-1] if self.rollback_history else None
        }
        
        return options
    
    def generate_rollback_report(self, operations: List[RollbackOperation], output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Generate rollback report."""
        success_count = sum(1 for op in operations if op.status == RollbackStatus.SUCCESS)
        failed_count = sum(1 for op in operations if op.status == RollbackStatus.FAILED)
        
        report = {
            "rollback_summary": {
                "total_operations": len(operations),
                "successful_operations": success_count,
                "failed_operations": failed_count,
                "overall_success": success_count == len(operations)
            },
            "operations": [asdict(op) for op in operations],
            "rollback_history": self.rollback_history,
            "system_status": {
                "backup_available": self.context_backup_dir.exists(),
                "emergency_restore_available": self.emergency_restore_script.exists()
            },
            "generated_at": self._get_timestamp(),
            "rollback_manager_version": "1.0.0"
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Rollback report saved to: {output_path}")
        
        return report
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        return datetime.now().isoformat()


def main():
    """Main entry point for rollback manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Context Changes Rollback Manager")
    parser.add_argument("--component", choices=[c.value for c in RollbackComponent], 
                       help="Component to rollback")
    parser.add_argument("--rollback-type", choices=[rt.value for rt in RollbackType],
                       default="partial", help="Type of rollback")
    parser.add_argument("--dry-run", action="store_true", help="Simulate rollback without changes")
    parser.add_argument("--emergency", action="store_true", help="Execute emergency restore")
    parser.add_argument("--rollback-last", action="store_true", help="Rollback last change only")
    parser.add_argument("--list-options", action="store_true", help="List rollback options")
    parser.add_argument("--output-report", help="Output rollback report path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    manager = RollbackManager()
    
    try:
        if args.list_options:
            # List available options
            options = manager.list_rollback_options()
            print("📋 Rollback Options:")
            print(f"   Available Components: {options['available_components']}")
            print(f"   Rollback Types: {options['rollback_types']}")
            print(f"   Backup Available: {options['backup_available']}")
            print(f"   Emergency Restore Available: {options['emergency_restore_available']}")
            print(f"   Rollback History: {options['rollback_history_count']} operations")
            return 0
        
        elif args.emergency:
            # Emergency restore
            print("🚨 Executing EMERGENCY RESTORE...")
            success = manager.emergency_restore()
            
            if success:
                print("✅ Emergency restore completed successfully")
                return 0
            else:
                print("❌ Emergency restore failed")
                return 1
        
        elif args.rollback_last:
            # Rollback last change
            print("🔄 Rolling back last change...")
            success = manager.rollback_last_change()
            
            if success:
                print("✅ Last change rolled back successfully")
                return 0
            else:
                print("❌ Failed to rollback last change")
                return 1
        
        elif args.component:
            # Component-specific rollback
            component = RollbackComponent(args.component)
            rollback_type = RollbackType(args.rollback_type)
            
            print(f"🔄 Rolling back {component.value} ({rollback_type.value})")
            
            # Create rollback plan
            plan = manager.create_rollback_plan([component], rollback_type)
            
            print(f"📋 Rollback Plan:")
            print(f"   Operations: {plan.total_components}")
            print(f"   Estimated Time: {plan.estimated_time_minutes} minutes")
            print(f"   Risks: {len(plan.risks)}")
            
            if plan.risks:
                print("   ⚠️ Risks:")
                for risk in plan.risks:
                    print(f"     - {risk}")
            
            if not args.dry_run:
                confirm = input("Proceed with rollback? (y/N): ")
                if confirm.lower() != 'y':
                    print("Rollback cancelled")
                    return 0
            
            # Execute rollback
            operations = manager.execute_rollback_plan(plan, args.dry_run)
            
            # Display results
            success_count = sum(1 for op in operations if op.status == RollbackStatus.SUCCESS)
            print(f"✅ Rollback complete: {success_count}/{len(operations)} successful")
            
            # Generate report if requested
            if args.output_report:
                report = manager.generate_rollback_report(operations, Path(args.output_report))
                print(f"📊 Rollback report saved to: {args.output_report}")
            
            # Verify rollback
            if not args.dry_run and success_count > 0:
                print("🔍 Verifying rollback success...")
                verification_success = manager.verify_rollback_success(operations)
                if verification_success:
                    print("✅ Rollback verification passed")
                else:
                    print("⚠️ Rollback verification failed")
            
            return 0 if success_count == len(operations) else 1
        
        else:
            print("❌ No rollback action specified. Use --help for options.")
            return 1
    
    except Exception as e:
        logging.error(f"Rollback operation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())