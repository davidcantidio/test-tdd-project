#!/usr/bin/env python3
"""
🔧 Step 3.2.2 - Automated Batch 2 Migration Script

Applies the 6 corrected service layer templates to all 15 Batch 2 files
with automatic template detection, backup creation, and validation.

Usage:
    python migrate_batch2_files.py --dry-run    # Preview changes
    python migrate_batch2_files.py --execute    # Apply migrations
    python migrate_batch2_files.py --rollback   # Rollback migrations

Features:
- Automatic template detection per file
- Backup creation before migration
- Pattern-based OLD -> NEW transformations
- Migration validation and testing
- Detailed progress tracking and logging
"""

import os
import re
import shutil
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Import our corrected template system
from service_layer_templates import (
    SERVICE_LAYER_TEMPLATES, 
    get_template_for_file, 
    list_batch2_files
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Batch2MigrationEngine:
    """Enterprise migration engine for Batch 2 files."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.migration_results = []
        self.backup_dir = f"backups/batch2_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.failed_migrations = []
        self.successful_migrations = []
        
        # Create backup directory
        if not dry_run:
            os.makedirs(self.backup_dir, exist_ok=True)
            logger.info(f"📁 Created backup directory: {self.backup_dir}")

    def migrate_all_batch2_files(self) -> Dict[str, any]:
        """Migrate all 15 Batch 2 files using service layer templates."""
        logger.info("🚀 Starting Batch 2 migration with corrected templates...")
        logger.info(f"📊 Migration mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}")
        
        batch2_files = list_batch2_files()
        logger.info(f"📁 Files to migrate: {len(batch2_files)}")
        
        migration_summary = {
            'total_files': len(batch2_files),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'dry_run': self.dry_run,
            'backup_location': self.backup_dir if not self.dry_run else None
        }
        
        # Migrate each file
        for i, file_path in enumerate(batch2_files, 1):
            logger.info(f"\n📄 [{i}/{len(batch2_files)}] Processing: {file_path}")
            
            try:
                result = self._migrate_single_file(file_path)
                
                if result['status'] == 'success':
                    migration_summary['successful'] += 1
                    self.successful_migrations.append(file_path)
                elif result['status'] == 'skipped':
                    migration_summary['skipped'] += 1
                else:
                    migration_summary['failed'] += 1
                    self.failed_migrations.append((file_path, result.get('error')))
                
                self.migration_results.append(result)
                
            except Exception as e:
                logger.error(f"❌ Critical error processing {file_path}: {e}")
                migration_summary['failed'] += 1
                self.failed_migrations.append((file_path, str(e)))
        
        # Generate final summary
        self._print_migration_summary(migration_summary)
        
        return migration_summary

    def _migrate_single_file(self, file_path: str) -> Dict[str, any]:
        """Migrate a single file using appropriate template."""
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"⚠️  File not found: {file_path}")
            return {
                'file_path': file_path,
                'status': 'skipped',
                'reason': 'File not found'
            }
        
        # Get template for this file
        template = get_template_for_file(file_path)
        template_name = self._get_template_name(template)
        
        logger.info(f"🔧 Template detected: {template_name}")
        logger.info(f"📋 Complexity: {template['complexity']}")
        
        # Read current file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            logger.error(f"❌ Failed to read {file_path}: {e}")
            return {
                'file_path': file_path,
                'status': 'failed',
                'error': f'Failed to read file: {e}'
            }
        
        # Apply template transformation
        try:
            transformed_content, changes_made = self._apply_template_transformation(
                original_content, template, file_path
            )
            
            if not changes_made:
                logger.info("✅ File already migrated or no changes needed")
                return {
                    'file_path': file_path,
                    'status': 'skipped',
                    'reason': 'No changes needed'
                }
            
        except Exception as e:
            logger.error(f"❌ Template transformation failed: {e}")
            return {
                'file_path': file_path,
                'status': 'failed',
                'error': f'Template transformation failed: {e}'
            }
        
        # Validate transformation
        validation_result = self._validate_transformation(
            original_content, transformed_content, file_path
        )
        
        if not validation_result['valid']:
            logger.error(f"❌ Validation failed: {validation_result['error']}")
            return {
                'file_path': file_path,
                'status': 'failed',
                'error': f'Validation failed: {validation_result["error"]}'
            }
        
        # Apply changes (if not dry run)
        if not self.dry_run:
            try:
                # Create backup
                backup_path = self._create_backup(file_path, original_content)
                logger.info(f"💾 Backup created: {backup_path}")
                
                # Write migrated content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(transformed_content)
                
                logger.info(f"✅ Migration completed successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to write migrated file: {e}")
                return {
                    'file_path': file_path,
                    'status': 'failed',
                    'error': f'Failed to write migrated file: {e}'
                }
        else:
            logger.info(f"🔍 DRY RUN: Would apply {len(validation_result['changes'])} changes")
        
        return {
            'file_path': file_path,
            'status': 'success',
            'template': template_name,
            'changes_count': len(validation_result['changes']),
            'backup_path': backup_path if not self.dry_run else None,
            'changes': validation_result['changes']
        }

    def _apply_template_transformation(self, content: str, template: Dict, file_path: str) -> Tuple[str, bool]:
        """Apply template OLD -> NEW pattern transformation."""
        
        old_pattern = template['old'].strip()
        new_pattern = template['new'].strip()
        
        # Check if old pattern exists in file
        if old_pattern not in content:
            # Try fuzzy matching for common variations
            fuzzy_matches = self._find_fuzzy_matches(content, old_pattern, file_path)
            
            if not fuzzy_matches:
                logger.info("ℹ️  Old pattern not found - file may already be migrated")
                return content, False
            
            # Apply fuzzy transformations
            transformed_content = content
            changes_made = False
            
            for old_fuzzy, new_fuzzy in fuzzy_matches:
                if old_fuzzy in transformed_content:
                    transformed_content = transformed_content.replace(old_fuzzy, new_fuzzy)
                    changes_made = True
                    logger.info(f"🔄 Fuzzy match applied: {old_fuzzy[:50]}...")
            
            return transformed_content, changes_made
        
        # Direct pattern replacement
        transformed_content = content.replace(old_pattern, new_pattern)
        changes_made = transformed_content != content
        
        if changes_made:
            logger.info(f"🔄 Applied direct pattern transformation")
        
        return transformed_content, changes_made

    def _find_fuzzy_matches(self, content: str, old_pattern: str, file_path: str) -> List[Tuple[str, str]]:
        """Find fuzzy matches for template patterns."""
        fuzzy_matches = []
        
        # Extract key components from old pattern
        old_lines = [line.strip() for line in old_pattern.split('\n') if line.strip()]
        
        # File-specific fuzzy matching rules
        if 'database' in file_path.lower():
            # Database-specific patterns
            if 'from streamlit_extension.utils.database import DatabaseManager' in old_lines[0]:
                # Look for existing DatabaseManager imports
                if 'DatabaseManager' in content and 'from streamlit_extension.utils.database import' not in content:
                    # Pattern variations for database files
                    fuzzy_matches.extend(self._generate_database_fuzzy_patterns())
        
        elif 'test' in file_path.lower():
            # Test-specific patterns
            if 'DatabaseManager' in old_pattern:
                fuzzy_matches.extend(self._generate_test_fuzzy_patterns())
        
        elif 'performance' in file_path.lower():
            # Performance-specific patterns
            fuzzy_matches.extend(self._generate_performance_fuzzy_patterns())
        
        return fuzzy_matches

    def _generate_database_fuzzy_patterns(self) -> List[Tuple[str, str]]:
        """Generate fuzzy patterns for database files."""
        return [
            # DatabaseManager instantiation patterns
            ("db_manager = DatabaseManager()", 
             "# Use modular API\nfrom streamlit_extension.database import get_connection\nconnection = get_connection()"),
            
            # Common database operations
            ("db_manager.get_connection()",
             "get_connection()"),
            
            # Epic operations
            ("db_manager.get_epics()",
             "list_epics()  # Modular API - fast and optimized")
        ]

    def _generate_test_fuzzy_patterns(self) -> List[Tuple[str, str]]:
        """Generate fuzzy patterns for test files."""
        return [
            # Test setup patterns
            ("self.db_manager = DatabaseManager()",
             """# Service layer for business operations
        self.service_container = ServiceContainer()
        
        # Legacy for fallback/hybrid operations
        self.db_manager = DatabaseManager()"""),
            
            # Test method patterns
            ("db_manager.get_epics()",
             "list_epics()  # Use modular API for simple operations")
        ]

    def _generate_performance_fuzzy_patterns(self) -> List[Tuple[str, str]]:
        """Generate fuzzy patterns for performance files."""
        return [
            # Performance testing patterns
            ("DatabaseManager()",
             """# Use direct connection for performance testing
    connection = get_connection()
    performance_tester = PerformanceTester(connection)"""),
            
            # Benchmark patterns
            ("db_manager.benchmark_operations()",
             "performance_tester.benchmark_operations()")
        ]

    def _validate_transformation(self, original: str, transformed: str, file_path: str) -> Dict[str, any]:
        """Validate the transformation was applied correctly."""
        
        if original == transformed:
            return {
                'valid': False,
                'error': 'No transformation applied',
                'changes': []
            }
        
        # Basic syntax validation for Python files
        if file_path.endswith('.py'):
            try:
                compile(transformed, file_path, 'exec')
            except SyntaxError as e:
                return {
                    'valid': False,
                    'error': f'Syntax error in transformed code: {e}',
                    'changes': []
                }
        
        # Analyze changes
        changes = self._analyze_changes(original, transformed)
        
        # Validate changes make sense
        if not self._validate_changes_quality(changes, file_path):
            return {
                'valid': False,
                'error': 'Changes quality validation failed',
                'changes': changes
            }
        
        return {
            'valid': True,
            'changes': changes,
            'changes_count': len(changes)
        }

    def _analyze_changes(self, original: str, transformed: str) -> List[Dict[str, str]]:
        """Analyze specific changes made during transformation."""
        changes = []
        
        original_lines = original.split('\n')
        transformed_lines = transformed.split('\n')
        
        # Simple diff analysis
        for i, (orig_line, new_line) in enumerate(zip(original_lines, transformed_lines)):
            if orig_line != new_line:
                changes.append({
                    'line_number': i + 1,
                    'original': orig_line.strip(),
                    'transformed': new_line.strip(),
                    'type': 'modification'
                })
        
        # Handle added/removed lines
        if len(transformed_lines) > len(original_lines):
            for i in range(len(original_lines), len(transformed_lines)):
                changes.append({
                    'line_number': i + 1,
                    'original': '',
                    'transformed': transformed_lines[i].strip(),
                    'type': 'addition'
                })
        
        return changes

    def _validate_changes_quality(self, changes: List[Dict], file_path: str) -> bool:
        """Validate that changes improve the codebase."""
        
        # Check for expected improvements
        improvement_indicators = [
            'from streamlit_extension.database import',  # Modular API import
            'ServiceContainer',                          # Service layer usage
            'get_connection()',                         # Direct connection access
            'list_epics()',                            # Modular API calls
            '# Service layer for business operations',  # Proper comments
            '# Modular API - fast and optimized'       # Performance comments
        ]
        
        transformed_content = '\n'.join([change['transformed'] for change in changes])
        
        # At least one improvement indicator should be present
        has_improvements = any(indicator in transformed_content for indicator in improvement_indicators)
        
        if not has_improvements:
            logger.warning(f"⚠️  No improvement indicators found in {file_path}")
            return False
        
        # Check for potential regressions
        regression_indicators = [
            'TODO: FIX',
            'BROKEN:',
            'HACK:',
            'undefined',
            'null',
        ]
        
        has_regressions = any(indicator in transformed_content for indicator in regression_indicators)
        
        if has_regressions:
            logger.error(f"❌ Regression indicators found in {file_path}")
            return False
        
        return True

    def _create_backup(self, file_path: str, content: str) -> str:
        """Create backup of original file."""
        
        # Create backup file path
        backup_filename = os.path.basename(file_path) + f".backup_batch2"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        # Ensure backup directory exists for nested files
        backup_dir_path = os.path.dirname(backup_path)
        os.makedirs(backup_dir_path, exist_ok=True)
        
        # Write backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return backup_path

    def _get_template_name(self, template: Dict) -> str:
        """Get template name from template dictionary."""
        for name, tmpl in SERVICE_LAYER_TEMPLATES.items():
            if tmpl == template:
                return name
        return "unknown_template"

    def _print_migration_summary(self, summary: Dict):
        """Print comprehensive migration summary."""
        
        logger.info("\n" + "="*80)
        logger.info("📊 BATCH 2 MIGRATION SUMMARY")
        logger.info("="*80)
        
        logger.info(f"📁 Total files processed: {summary['total_files']}")
        logger.info(f"✅ Successful migrations: {summary['successful']}")
        logger.info(f"❌ Failed migrations: {summary['failed']}")
        logger.info(f"⏭️  Skipped files: {summary['skipped']}")
        
        if summary['dry_run']:
            logger.info("🔍 Mode: DRY RUN (no changes applied)")
        else:
            logger.info(f"💾 Backup location: {summary['backup_location']}")
        
        # Success details
        if self.successful_migrations:
            logger.info(f"\n✅ SUCCESSFUL MIGRATIONS ({len(self.successful_migrations)}):")
            for file_path in self.successful_migrations:
                logger.info(f"   ✓ {file_path}")
        
        # Failure details
        if self.failed_migrations:
            logger.info(f"\n❌ FAILED MIGRATIONS ({len(self.failed_migrations)}):")
            for file_path, error in self.failed_migrations:
                logger.info(f"   ✗ {file_path}: {error}")
        
        # Success rate
        if summary['total_files'] > 0:
            success_rate = (summary['successful'] / summary['total_files']) * 100
            logger.info(f"\n🎯 SUCCESS RATE: {success_rate:.1f}%")
        
        logger.info("="*80)

    def rollback_migrations(self) -> bool:
        """Rollback migrations using backup files."""
        logger.info("🔄 Starting rollback process...")
        
        if not os.path.exists(self.backup_dir):
            logger.error(f"❌ Backup directory not found: {self.backup_dir}")
            return False
        
        backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.backup_batch2')]
        
        if not backup_files:
            logger.error("❌ No backup files found for rollback")
            return False
        
        rollback_count = 0
        
        for backup_file in backup_files:
            original_file = backup_file.replace('.backup_batch2', '')
            backup_path = os.path.join(self.backup_dir, backup_file)
            
            # Find original file path
            for file_path in list_batch2_files():
                if os.path.basename(file_path) == original_file:
                    try:
                        shutil.copy2(backup_path, file_path)
                        logger.info(f"🔄 Restored: {file_path}")
                        rollback_count += 1
                    except Exception as e:
                        logger.error(f"❌ Failed to restore {file_path}: {e}")
                    break
        
        logger.info(f"✅ Rollback completed: {rollback_count} files restored")
        return rollback_count > 0


def main():
    """Main migration script entry point."""
    
    parser = argparse.ArgumentParser(
        description="Batch 2 Migration Script - Step 3.2.2",
        epilog="Apply corrected service layer templates to 15 Batch 2 files"
    )
    
    # Mutually exclusive operation modes
    operation_group = parser.add_mutually_exclusive_group(required=True)
    operation_group.add_argument(
        '--dry-run', 
        action='store_true',
        help='Preview migrations without applying changes'
    )
    operation_group.add_argument(
        '--execute', 
        action='store_true',
        help='Execute migrations and apply changes'
    )
    operation_group.add_argument(
        '--rollback', 
        metavar='BACKUP_DIR',
        help='Rollback migrations from specified backup directory'
    )
    
    # Additional options
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Execute based on mode
    if args.rollback:
        logger.info(f"🔄 Rollback mode: {args.rollback}")
        migration_engine = Batch2MigrationEngine(dry_run=False)
        migration_engine.backup_dir = args.rollback
        success = migration_engine.rollback_migrations()
        return 0 if success else 1
        
    else:
        # Migration mode (dry-run or execute)
        dry_run = args.dry_run
        logger.info(f"🚀 Migration mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
        
        migration_engine = Batch2MigrationEngine(dry_run=dry_run)
        summary = migration_engine.migrate_all_batch2_files()
        
        # Return appropriate exit code
        if summary['failed'] > 0:
            logger.error("❌ Migration completed with failures")
            return 1
        else:
            logger.info("✅ Migration completed successfully")
            return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())