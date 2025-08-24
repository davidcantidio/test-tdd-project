#!/usr/bin/env python3
"""
🔧 Step 3.2.2 - Enhanced Batch 2 Migration Script

Real-world migration with granular pattern replacement that handles actual code patterns
instead of exact multi-line template matches.

Usage:
    python migrate_batch2_enhanced.py --analyze    # Analyze files for patterns
    python migrate_batch2_enhanced.py --dry-run   # Preview changes
    python migrate_batch2_enhanced.py --execute   # Apply migrations

Features:
- Granular pattern replacement (imports, method calls, instantiation)
- Real-world code pattern detection
- Intelligent template application
- File-specific migration strategies
"""

import os
import re
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set

from service_layer_templates import list_batch2_files, get_template_for_file, SERVICE_LAYER_TEMPLATES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedBatch2Migrator:
    """Enhanced migrator that handles real-world code patterns."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.backup_dir = f"backups/batch2_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.migration_patterns = self._initialize_migration_patterns()
        
        if not dry_run:
            os.makedirs(self.backup_dir, exist_ok=True)
    
    def _initialize_migration_patterns(self) -> Dict[str, List[Tuple[str, str]]]:
        """Initialize granular migration patterns for real-world code."""
        
        return {
            # Import patterns - most fundamental changes
            'imports': [
                (
                    r'from streamlit_extension\.utils\.database import DatabaseManager',
                    '# Legacy import - keeping for hybrid compatibility\nfrom streamlit_extension.utils.database import DatabaseManager\n# New modular imports\nfrom streamlit_extension.database import get_connection, list_epics, list_tasks\nfrom streamlit_extension.services import ServiceContainer'
                ),
                (
                    r'from streamlit_extension\.utils\.database import DatabaseManager.*',
                    'from streamlit_extension.utils.database import DatabaseManager  # Legacy compatibility\nfrom streamlit_extension.database import get_connection, list_epics, list_tasks\nfrom streamlit_extension.services import ServiceContainer'
                )
            ],
            
            # DatabaseManager instantiation patterns
            'instantiation': [
                (
                    r'db_manager = DatabaseManager\(\)',
                    'db_manager = DatabaseManager()  # Legacy compatibility\nservice_container = ServiceContainer()  # Service layer'
                ),
                (
                    r'self\.db_manager = DatabaseManager\(\)',
                    'self.db_manager = DatabaseManager()  # Legacy fallback\nself.service_container = ServiceContainer()  # Service layer'
                )
            ],
            
            # Epic operations - high priority for migration
            'epic_operations': [
                (
                    r'db_manager\.get_epics\(\)',
                    'list_epics()  # Modular API - fast and optimized'
                ),
                (
                    r'self\.db_manager\.get_epics\(\)',
                    'list_epics()  # Use modular API for simple operations'
                ),
                (
                    r'db_manager\.create_epic\(',
                    'self.service_container.get_epic_service().create('
                ),
                (
                    r'db_manager\.update_epic\(',
                    'self.service_container.get_epic_service().update('
                ),
                (
                    r'db_manager\.delete_epic\(',
                    'self.service_container.get_epic_service().delete('
                )
            ],
            
            # Task operations - hybrid approach
            'task_operations': [
                (
                    r'db_manager\.get_tasks\(\)',
                    'db_manager.get_tasks()  # Keep legacy - modular API broken for tasks'
                ),
                (
                    r'db_manager\.create_task\(',
                    'self.service_container.get_task_service().create('
                ),
                (
                    r'db_manager\.update_task\(',
                    'self.service_container.get_task_service().update('
                )
            ],
            
            # Database connection patterns
            'connection_patterns': [
                (
                    r'db_manager\.get_connection\(\)',
                    'get_connection()  # Direct modular API'
                ),
                (
                    r'self\.db_manager\.get_connection\(\)',
                    'get_connection()  # Use modular connection API'
                )
            ],
            
            # Test setup patterns for test files
            'test_setup': [
                (
                    r'def setUp\(self\):\s*self\.db_manager = DatabaseManager\(\)',
                    '''def setUp(self):
        # Service layer for business operations
        self.service_container = ServiceContainer()
        self.epic_service = self.service_container.get_epic_service()
        
        # Legacy for fallback/hybrid operations
        self.db_manager = DatabaseManager()'''
                )
            ]
        }
    
    def analyze_files(self) -> Dict[str, any]:
        """Analyze all Batch 2 files for migration patterns."""
        logger.info("🔍 Analyzing Batch 2 files for migration patterns...")
        
        analysis_results = {
            'files_needing_migration': [],
            'files_already_migrated': [],
            'pattern_counts': {},
            'migration_complexity': {}
        }
        
        batch2_files = list_batch2_files()
        
        for file_path in batch2_files:
            if not os.path.exists(file_path):
                continue
                
            file_analysis = self._analyze_single_file(file_path)
            
            if file_analysis['needs_migration']:
                analysis_results['files_needing_migration'].append({
                    'path': file_path,
                    'patterns_found': file_analysis['patterns_found'],
                    'complexity': file_analysis['complexity'],
                    'template': file_analysis['template']
                })
            else:
                analysis_results['files_already_migrated'].append(file_path)
            
            # Aggregate pattern counts
            for pattern, count in file_analysis['patterns_found'].items():
                if pattern not in analysis_results['pattern_counts']:
                    analysis_results['pattern_counts'][pattern] = 0
                analysis_results['pattern_counts'][pattern] += count
        
        self._print_analysis_results(analysis_results)
        return analysis_results
    
    def _analyze_single_file(self, file_path: str) -> Dict[str, any]:
        """Analyze a single file for migration patterns."""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return {'needs_migration': False, 'patterns_found': {}, 'complexity': 'ERROR'}
        
        patterns_found = {}
        total_patterns = 0
        
        # Check for patterns in each category
        for category, pattern_list in self.migration_patterns.items():
            category_count = 0
            for pattern, _ in pattern_list:
                matches = len(re.findall(pattern, content))
                if matches > 0:
                    category_count += matches
                    total_patterns += matches
            
            if category_count > 0:
                patterns_found[category] = category_count
        
        # Determine complexity
        complexity = 'LOW'
        if total_patterns > 10:
            complexity = 'HIGH'
        elif total_patterns > 5:
            complexity = 'MEDIUM'
        
        # Get template information
        template = get_template_for_file(file_path)
        template_name = self._get_template_name(template)
        
        return {
            'needs_migration': total_patterns > 0,
            'patterns_found': patterns_found,
            'total_patterns': total_patterns,
            'complexity': complexity,
            'template': template_name
        }
    
    def _get_template_name(self, template: Dict) -> str:
        """Get template name from template dictionary."""
        for name, tmpl in SERVICE_LAYER_TEMPLATES.items():
            if tmpl == template:
                return name
        return "unknown_template"
    
    def migrate_all_files(self) -> Dict[str, any]:
        """Migrate all files that need migration."""
        logger.info("🚀 Starting enhanced Batch 2 migration...")
        logger.info(f"📊 Migration mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}")
        
        # First analyze to see what needs migration
        analysis = self.analyze_files()
        
        if not analysis['files_needing_migration']:
            logger.info("✅ All files are already migrated!")
            return {'status': 'complete', 'files_migrated': 0, 'message': 'No migration needed'}
        
        migration_results = {
            'files_migrated': 0,
            'files_failed': 0,
            'total_patterns_applied': 0,
            'migration_details': []
        }
        
        # Migrate each file that needs it
        for file_info in analysis['files_needing_migration']:
            file_path = file_info['path']
            logger.info(f"\n📄 Migrating: {file_path}")
            logger.info(f"🔧 Template: {file_info['template']}")
            logger.info(f"📊 Complexity: {file_info['complexity']}")
            
            try:
                result = self._migrate_single_file_enhanced(file_path, file_info)
                
                if result['success']:
                    migration_results['files_migrated'] += 1
                    migration_results['total_patterns_applied'] += result['patterns_applied']
                else:
                    migration_results['files_failed'] += 1
                
                migration_results['migration_details'].append(result)
                
            except Exception as e:
                logger.error(f"❌ Critical error migrating {file_path}: {e}")
                migration_results['files_failed'] += 1
        
        self._print_migration_summary(migration_results)
        return migration_results
    
    def _migrate_single_file_enhanced(self, file_path: str, file_info: Dict) -> Dict[str, any]:
        """Migrate a single file using enhanced pattern replacement."""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            return {'success': False, 'error': f'Failed to read file: {e}'}
        
        # Apply migrations based on file type and patterns found
        migrated_content = original_content
        patterns_applied = 0
        applied_changes = []
        
        # Apply patterns in order of importance
        pattern_priority = ['imports', 'instantiation', 'epic_operations', 'task_operations', 
                          'connection_patterns', 'test_setup']
        
        for category in pattern_priority:
            if category in file_info['patterns_found']:
                content_before = migrated_content
                migrated_content, changes = self._apply_pattern_category(
                    migrated_content, category, file_path
                )
                
                if migrated_content != content_before:
                    patterns_applied += changes
                    applied_changes.append({
                        'category': category,
                        'changes': changes
                    })
        
        if patterns_applied == 0:
            return {'success': False, 'error': 'No patterns could be applied'}
        
        # Validate the migrated content
        if not self._validate_migrated_content(migrated_content, file_path):
            return {'success': False, 'error': 'Migration validation failed'}
        
        # Apply changes if not dry run
        if not self.dry_run:
            try:
                # Create backup
                backup_path = self._create_backup(file_path, original_content)
                
                # Write migrated content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(migrated_content)
                
                logger.info(f"✅ Migration successful: {patterns_applied} patterns applied")
                logger.info(f"💾 Backup: {backup_path}")
                
            except Exception as e:
                return {'success': False, 'error': f'Failed to write migrated file: {e}'}
        else:
            logger.info(f"🔍 DRY RUN: Would apply {patterns_applied} pattern changes")
        
        return {
            'success': True,
            'patterns_applied': patterns_applied,
            'applied_changes': applied_changes,
            'backup_path': None if self.dry_run else backup_path
        }
    
    def _apply_pattern_category(self, content: str, category: str, file_path: str) -> Tuple[str, int]:
        """Apply all patterns in a specific category."""
        
        if category not in self.migration_patterns:
            return content, 0
        
        migrated_content = content
        changes_count = 0
        
        for pattern, replacement in self.migration_patterns[category]:
            # Apply replacement
            new_content = re.sub(pattern, replacement, migrated_content)
            
            if new_content != migrated_content:
                changes_count += 1
                migrated_content = new_content
                logger.info(f"✅ Applied {category} pattern: {pattern[:50]}...")
        
        return migrated_content, changes_count
    
    def _validate_migrated_content(self, content: str, file_path: str) -> bool:
        """Validate migrated content for basic correctness."""
        
        # Python syntax validation
        if file_path.endswith('.py'):
            try:
                compile(content, file_path, 'exec')
            except SyntaxError as e:
                logger.error(f"❌ Syntax error in migrated content: {e}")
                return False
        
        # Check for required improvements
        improvement_indicators = [
            'ServiceContainer',
            'from streamlit_extension.database import',
            'list_epics()',
            '# Modular API',
            '# Service layer'
        ]
        
        has_improvements = any(indicator in content for indicator in improvement_indicators)
        
        if not has_improvements:
            logger.warning("⚠️  No improvement indicators found in migrated content")
            return False
        
        return True
    
    def _create_backup(self, file_path: str, content: str) -> str:
        """Create backup of original file."""
        backup_filename = os.path.basename(file_path) + ".backup_enhanced"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return backup_path
    
    def _print_analysis_results(self, results: Dict[str, any]):
        """Print comprehensive analysis results."""
        
        logger.info("\n" + "="*80)
        logger.info("🔍 BATCH 2 ANALYSIS RESULTS")
        logger.info("="*80)
        
        logger.info(f"📁 Files needing migration: {len(results['files_needing_migration'])}")
        logger.info(f"✅ Files already migrated: {len(results['files_already_migrated'])}")
        
        if results['files_needing_migration']:
            logger.info(f"\n📋 FILES NEEDING MIGRATION:")
            for file_info in results['files_needing_migration']:
                logger.info(f"  📄 {file_info['path']}")
                logger.info(f"     Template: {file_info['template']} | Complexity: {file_info['complexity']}")
                logger.info(f"     Patterns: {file_info['patterns_found']}")
        
        if results['pattern_counts']:
            logger.info(f"\n📊 PATTERN DISTRIBUTION:")
            for pattern, count in results['pattern_counts'].items():
                logger.info(f"  {pattern}: {count} occurrences")
        
        logger.info("="*80)
    
    def _print_migration_summary(self, results: Dict[str, any]):
        """Print migration summary."""
        
        logger.info("\n" + "="*80)
        logger.info("📊 ENHANCED MIGRATION SUMMARY")
        logger.info("="*80)
        
        logger.info(f"✅ Files migrated: {results['files_migrated']}")
        logger.info(f"❌ Files failed: {results['files_failed']}")
        logger.info(f"🔄 Total patterns applied: {results['total_patterns_applied']}")
        
        if self.dry_run:
            logger.info("🔍 Mode: DRY RUN (no changes applied)")
        
        success_rate = (results['files_migrated'] / 
                       (results['files_migrated'] + results['files_failed']) * 100 
                       if (results['files_migrated'] + results['files_failed']) > 0 else 100)
        
        logger.info(f"🎯 SUCCESS RATE: {success_rate:.1f}%")
        logger.info("="*80)


def main():
    """Main script entry point."""
    
    parser = argparse.ArgumentParser(
        description="Enhanced Batch 2 Migration - Step 3.2.2",
        epilog="Real-world pattern migration for Batch 2 files"
    )
    
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument('--analyze', action='store_true', help='Analyze files for patterns')
    operation.add_argument('--dry-run', action='store_true', help='Preview migrations')
    operation.add_argument('--execute', action='store_true', help='Execute migrations')
    
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    migrator = EnhancedBatch2Migrator(dry_run=(args.analyze or args.dry_run))
    
    if args.analyze:
        logger.info("🔍 Analysis mode")
        migrator.analyze_files()
    else:
        logger.info(f"🚀 Migration mode: {'DRY RUN' if args.dry_run else 'EXECUTION'}")
        results = migrator.migrate_all_files()
        
        if results.get('files_failed', 0) > 0:
            return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())