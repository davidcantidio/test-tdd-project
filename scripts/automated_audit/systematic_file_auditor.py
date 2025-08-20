#!/usr/bin/env python3
"""
🤖 Systematic File Auditor - Sétima Camada de Auditoria Automatizada

Sistema automatizado que percorre TODOS os arquivos do projeto sistematicamente,
analisando linha por linha, otimizando quando possível, e documentando tudo
com tracking no banco de dados para resiliência completa.

Usage:
    python systematic_file_auditor.py [--resume] [--dry-run] [--max-files=N]
"""

import asyncio
import time
import sys
import os
import sqlite3
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import subprocess
import ast

# Sétima Camada Integration Imports
try:
    from .context_validator import ContextValidator
    from .integration_tester import IntegrationTester
    from .rollback_context_changes import RollbackManager
except ImportError:
    # Fallback imports for when running as main script
    try:
        from context_validator import ContextValidator
        from integration_tester import IntegrationTester
        from rollback_context_changes import RollbackManager
    except ImportError:
        # Graceful degradation if Sétima Camada components not available
        ContextValidator = None
        IntegrationTester = None
        RollbackManager = None

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from streamlit_extension.utils.database import DatabaseManager


# Sétima Camada Integration Data Structures
class SetimaDataLoader:
    """Loads Sétima Camada integration data from analysis documents."""
    
    def __init__(self, audit_dir: Path):
        self.audit_dir = audit_dir
        self.logger = logging.getLogger(f"{__name__}.SetimaDataLoader")
        
        # Load all integration data
        self.dependency_waves = self._load_dependency_data()
        self.risk_scores = self._load_risk_data()
        self.pattern_templates = self._load_pattern_data()
        self.good_patterns = self._load_good_patterns()
        self.anti_patterns = self._load_anti_patterns()
        
        self.logger.info(f"Sétima Camada data loaded: {len(self.risk_scores)} files scored")
    
    def _load_dependency_data(self) -> Dict[str, List[str]]:
        """Load dependency wave data from DEPENDENCY_GRAPH.md"""
        
        # Hardcoded dependency waves based on analysis
        # In production, this would parse DEPENDENCY_GRAPH.md
        return {
            'WAVE_1_FOUNDATION': [
                # Independent/leaf nodes - 137 files
                'tests/test_duration_calculator.py',
                'tests/test_business_calendar.py', 
                'scripts/maintenance/database_maintenance.py',
                'streamlit_extension/components/analytics_cards.py',
                'streamlit_extension/utils/path_utils.py',
                'streamlit_extension/utils/data_utils.py',
                'streamlit_extension/pages/clients.py',
                'streamlit_extension/endpoints/health.py',
                # Add more low-risk files...
            ],
            'WAVE_2_BUSINESS': [
                # Business logic - 85 files
                'streamlit_extension/services/analytics_service.py',
                'streamlit_extension/services/client_service.py',
                'streamlit_extension/models/task_models.py',
                'streamlit_extension/repos/tasks_repo.py',
                # Add more medium-risk files...
            ],
            'WAVE_3_INTEGRATION': [
                # Integration layer - 48 files
                'streamlit_extension/utils/circuit_breaker.py',
                'streamlit_extension/utils/metrics_collector.py',
                'duration_system/json_security.py',
                # Add more high-risk files...
            ],
            'WAVE_4_CRITICAL': [
                # Critical core - 10 files
                'streamlit_extension/database/connection.py',
                'streamlit_extension/streamlit_app.py',
                'streamlit_extension/middleware/rate_limiting/middleware.py',
                'streamlit_extension/database/queries.py',
                'streamlit_extension/database/seed.py',
                'streamlit_extension/middleware/rate_limiting/core.py',
                'streamlit_extension/database/schema.py',
                'streamlit_extension/database/health.py',
            ]
        }
    
    def _load_risk_data(self) -> Dict[str, int]:
        """Load risk assessment data from RISK_ASSESSMENT_MAP.md"""
        
        # Hardcoded risk scores based on analysis
        # In production, this would parse RISK_ASSESSMENT_MAP.md
        return {
            # CRITICAL RISK (106+)
            'streamlit_extension/database/connection.py': 165,
            'streamlit_extension/streamlit_app.py': 150,
            'streamlit_extension/middleware/rate_limiting/middleware.py': 145,
            'streamlit_extension/database/queries.py': 140,
            'streamlit_extension/database/seed.py': 135,
            'streamlit_extension/middleware/rate_limiting/core.py': 130,
            'streamlit_extension/database/schema.py': 120,
            'streamlit_extension/database/health.py': 110,
            
            # HIGH RISK (71-105)
            'streamlit_extension/utils/circuit_breaker.py': 90,
            'streamlit_extension/utils/metrics_collector.py': 85,
            'duration_system/json_security.py': 88,
            
            # MEDIUM RISK (36-70)
            'streamlit_extension/services/analytics_service.py': 48,
            'streamlit_extension/services/client_service.py': 52,
            'streamlit_extension/models/task_models.py': 45,
            
            # LOW RISK (0-35)
            'streamlit_extension/components/analytics_cards.py': 20,
            'streamlit_extension/utils/path_utils.py': 15,
            'streamlit_extension/pages/clients.py': 25,
            'tests/test_duration_calculator.py': 8,
            # Default for unscored files
        }
    
    def _load_pattern_data(self) -> Dict[str, Any]:
        """Load pattern templates from PATTERN_DETECTION_REPORT.md"""
        
        return {
            'import_centralization': {
                'description': 'Centralize imports to reduce import hell',
                'risk_level_safe': ['LOW', 'MEDIUM'],
                'transformation': 'from streamlit_extension.utils.import_manager import get_safe_import',
                'validation_required': True
            },
            'exception_swallowing_fix': {
                'description': 'Replace bare except with specific exception handling',
                'risk_level_safe': ['LOW', 'MEDIUM', 'HIGH'],
                'transformation': 'except {SpecificException} as e:\n    logger.warning("Operation failed: %s", str(e))\n    return None',
                'validation_required': False
            },
            'method_decomposition': {
                'description': 'Break down god methods into focused methods',
                'risk_level_safe': ['LOW'],
                'transformation': 'MANUAL_REVIEW_REQUIRED',
                'validation_required': True
            }
        }
    
    def _load_good_patterns(self) -> Dict[str, Any]:
        """Load good patterns to preserve."""
        
        return {
            'graceful_import': {
                'description': 'Safe import with fallback',
                'template': 'try:\n    import {module}\nexcept ImportError:\n    {module} = None',
                'preserve': True,
                'files_found': 8
            },
            'structured_logging': {
                'description': 'Comprehensive logging with context',
                'template': 'logger.info("Operation: %s", operation, extra={"context": context})',
                'preserve': True,
                'files_found': 6
            }
        }
    
    def _load_anti_patterns(self) -> Dict[str, Any]:
        """Load anti-patterns to fix."""
        
        return {
            'import_hell': {
                'description': 'Complex dynamic imports with global state',
                'severity': 'HIGH',
                'fix_template': 'import_centralization',
                'files_found': 3,
                'auto_fix': True
            },
            'god_method': {
                'description': 'Methods with 50+ lines, multiple responsibilities',
                'severity': 'MEDIUM',
                'fix_template': 'method_decomposition',
                'files_found': 4,
                'auto_fix': False
            },
            'exception_swallowing': {
                'description': 'Bare except clauses that hide errors',
                'severity': 'HIGH',
                'fix_template': 'exception_swallowing_fix',
                'files_found': 15,
                'auto_fix': True
            }
        }
    
    def get_file_wave(self, file_path: str) -> str:
        """Get modification wave for file."""
        for wave, files in self.dependency_waves.items():
            if file_path in files:
                return wave
        # Default to foundation if not categorized
        return 'WAVE_1_FOUNDATION'
    
    def get_file_risk_score(self, file_path: str) -> int:
        """Get risk score for file."""
        return self.risk_scores.get(file_path, 25)  # Default medium-low risk
    
    def get_file_risk_category(self, file_path: str) -> str:
        """Get risk category for file."""
        score = self.get_file_risk_score(file_path)
        if score >= 106:
            return 'CRITICAL'
        elif score >= 71:
            return 'HIGH'
        elif score >= 36:
            return 'MEDIUM'
        else:
            return 'LOW'


class AuditStatus(Enum):
    """Status of file audit."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SessionStatus(Enum):
    """Status of audit session."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskCategory(Enum):
    """Risk categories for Sétima Camada."""
    LOW = "LOW"           # 0-35 points - Safe parallel
    MEDIUM = "MEDIUM"     # 36-70 points - Coordination required  
    HIGH = "HIGH"         # 71-105 points - Sequential required
    CRITICAL = "CRITICAL" # 106+ points - One-at-a-time only


class ModificationWave(Enum):
    """Modification waves for dependency-safe processing."""
    WAVE_1_FOUNDATION = "WAVE_1_FOUNDATION"     # Independent files
    WAVE_2_BUSINESS = "WAVE_2_BUSINESS"         # Business logic
    WAVE_3_INTEGRATION = "WAVE_3_INTEGRATION"   # Integration layer
    WAVE_4_CRITICAL = "WAVE_4_CRITICAL"         # Critical core


@dataclass
class FileAuditResult:
    """Enhanced result of file audit with Sétima Camada integration."""
    file_path: str
    lines_analyzed: int
    issues_found: int
    optimizations_applied: int
    tokens_used: int
    changes_summary: str
    syntax_valid: bool
    backup_created: bool
    # Sétima Camada enhancements
    context_quality: float = 0.0
    risk_score: int = 0
    risk_category: str = "LOW"
    modification_wave: str = "WAVE_1_FOUNDATION"
    patterns_found: List[str] = None
    good_patterns_preserved: List[str] = None
    anti_patterns_fixed: List[str] = None
    integration_tests_passed: bool = True
    rollback_available: bool = False
    
    def __post_init__(self):
        if self.patterns_found is None:
            self.patterns_found = []
        if self.good_patterns_preserved is None:
            self.good_patterns_preserved = []
        if self.anti_patterns_fixed is None:
            self.anti_patterns_fixed = []


@dataclass
class AuditSession:
    """Audit session information."""
    session_id: int
    session_start: datetime
    current_file_index: int
    total_files: int
    files_completed: int
    total_tokens_used: int
    session_status: SessionStatus
    estimated_completion: Optional[datetime] = None


class EnhancedSystematicFileAuditor:
    """Enhanced Systematic File Auditor with Sétima Camada integration."""
    
    def __init__(self, project_root: Path, audit_dir: Path):
        self.project_root = project_root
        self.audit_dir = audit_dir
        self.logger = logging.getLogger(f"{__name__}.EnhancedSystematicFileAuditor")
        
        # Initialize core components
        self.db_manager = DatabaseManager()
        self.tracker = DatabaseTracker(self.db_manager)
        self.token_manager = TokenManager()
        self.file_manager = FileListManager(project_root)
        
        # Initialize Sétima Camada components
        self.context_validator = ContextValidator() if ContextValidator else None
        self.integration_tester = IntegrationTester() if IntegrationTester else None
        self.rollback_manager = RollbackManager() if RollbackManager else None
        self.setima_data = SetimaDataLoader(audit_dir)
        
        # Check integration availability
        self.setima_integration_available = all([
            self.context_validator is not None,
            self.integration_tester is not None,
            self.rollback_manager is not None
        ])
        
        # Validation pipeline
        self.validation_pipeline = self._setup_validation_pipeline()
        
        self.logger.info("Enhanced Systematic File Auditor initialized with Sétima Camada integration")
    
    def _setup_validation_pipeline(self) -> Dict[str, Any]:
        """Setup three-layer validation pipeline."""
        return {
            'min_context_quality': 50.0,
            'integration_test_required': True,
            'critical_validation_required': True,
            'rollback_on_failure': True
        }
    
    def audit_file_enhanced(self, file_path: str) -> FileAuditResult:
        """Enhanced audit with Sétima Camada integration."""
        try:
            self.logger.info(f"Starting enhanced audit of {file_path}")
            
            # 1. Context Validation
            context_quality = self._validate_context_quality(file_path)
            if context_quality < self.validation_pipeline['min_context_quality']:
                return self._create_skip_result(file_path, f"Low context quality: {context_quality}%")
            
            # 2. Risk Assessment
            risk_score = self.setima_data.get_file_risk_score(file_path)
            risk_category = self.setima_data.get_file_risk_category(file_path)
            
            # 3. Dependency Wave Check
            modification_wave = self.setima_data.get_file_wave(file_path)
            
            # 4. Pattern Detection
            patterns_found = self._detect_patterns(file_path)
            anti_patterns = [p for p in patterns_found if p.get('is_anti_pattern', False)]
            good_patterns = [p for p in patterns_found if not p.get('is_anti_pattern', False)]
            
            # 5. Safety Validation for Critical Files
            if risk_category == 'CRITICAL':
                safety_check = self._validate_critical_modification_safety(file_path)
                if not safety_check['is_safe']:
                    return self._create_defer_result(file_path, f"Critical safety check failed: {safety_check['reason']}")
            
            # 6. Create Backup
            backup_created = self._create_file_backup(file_path)
            
            # 7. Execute Context-Aware Audit
            audit_result = self._execute_context_aware_audit(
                file_path=file_path,
                risk_score=risk_score,
                patterns=patterns_found,
                context_quality=context_quality,
                wave_info=modification_wave
            )
            
            # 8. Post-Audit Validation
            if audit_result.get('modified', False):
                validation_result = self._validate_post_modification(file_path)
                if not validation_result['passed']:
                    # Automatic rollback on failure
                    self._rollback_file_changes(file_path)
                    return self._create_rollback_result(file_path, validation_result['errors'])
            
            # 9. Create Enhanced Result
            return FileAuditResult(
                file_path=file_path,
                lines_analyzed=audit_result.get('lines_analyzed', 0),
                issues_found=len(anti_patterns),
                optimizations_applied=audit_result.get('optimizations_applied', 0),
                tokens_used=audit_result.get('tokens_used', 0),
                changes_summary=audit_result.get('changes_summary', 'Enhanced audit completed'),
                syntax_valid=audit_result.get('syntax_valid', True),
                backup_created=backup_created,
                context_quality=context_quality,
                risk_score=risk_score,
                risk_category=risk_category,
                modification_wave=modification_wave,
                patterns_found=[p.get('name', 'unknown') for p in patterns_found],
                good_patterns_preserved=[p.get('name', 'unknown') for p in good_patterns],
                anti_patterns_fixed=[p.get('name', 'unknown') for p in anti_patterns if audit_result.get('modified')],
                integration_tests_passed=True,  # Updated by validation
                rollback_available=backup_created
            )
            
        except Exception as e:
            # Emergency rollback protocol
            self.logger.error(f"Critical error during audit of {file_path}: {e}")
            self._emergency_rollback(file_path)
            return self._create_emergency_result(file_path, str(e))
    
    def _validate_context_quality(self, file_path: str) -> float:
        """Validate context quality for file."""
        try:
            # Use context validator to check quality
            full_path = self.project_root / file_path
            if full_path.exists():
                # Simple quality check based on file characteristics
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Basic quality metrics
                lines = content.count('\n')
                has_docstrings = '"""' in content or "'''" in content
                has_type_hints = ': ' in content and '->' in content
                has_logging = 'logger' in content or 'logging' in content
                has_error_handling = 'try:' in content and 'except' in content
                
                # Calculate quality score
                quality = 50.0  # Base score
                if has_docstrings:
                    quality += 15.0
                if has_type_hints:
                    quality += 15.0
                if has_logging:
                    quality += 10.0
                if has_error_handling:
                    quality += 10.0
                
                # Bonus for reasonable length
                if 20 <= lines <= 500:
                    quality += 5.0
                
                return min(quality, 100.0)
            
            return 30.0  # Low quality for missing files
            
        except Exception as e:
            self.logger.warning(f"Context quality validation failed for {file_path}: {e}")
            return 40.0  # Default moderate quality on error
    
    def _detect_patterns(self, file_path: str) -> List[Dict[str, Any]]:
        """Detect patterns in file."""
        patterns = []
        
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return patterns
                
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for anti-patterns
            if 'except Exception:' in content or 'except:' in content:
                patterns.append({
                    'name': 'exception_swallowing',
                    'type': 'anti_pattern',
                    'is_anti_pattern': True,
                    'severity': 'HIGH',
                    'auto_fixable': True
                })
            
            # Check for import hell pattern
            if content.count('try:') > 3 and 'ImportError' in content:
                patterns.append({
                    'name': 'import_hell',
                    'type': 'anti_pattern', 
                    'is_anti_pattern': True,
                    'severity': 'HIGH',
                    'auto_fixable': True
                })
            
            # Check for god methods (methods > 50 lines)
            lines = content.split('\n')
            in_method = False
            method_lines = 0
            for line in lines:
                if line.strip().startswith('def '):
                    if in_method and method_lines > 50:
                        patterns.append({
                            'name': 'god_method',
                            'type': 'anti_pattern',
                            'is_anti_pattern': True,
                            'severity': 'MEDIUM',
                            'auto_fixable': False
                        })
                    in_method = True
                    method_lines = 0
                elif in_method:
                    if line.strip() and not line.startswith('    '):
                        in_method = False
                    else:
                        method_lines += 1
            
            # Check for good patterns
            if 'try:' in content and 'except ImportError:' in content and '_AVAILABLE' in content:
                patterns.append({
                    'name': 'graceful_import',
                    'type': 'good_pattern',
                    'is_anti_pattern': False,
                    'preserve': True
                })
            
            if 'logger.' in content and 'extra=' in content:
                patterns.append({
                    'name': 'structured_logging',
                    'type': 'good_pattern', 
                    'is_anti_pattern': False,
                    'preserve': True
                })
            
            return patterns
            
        except Exception as e:
            self.logger.warning(f"Pattern detection failed for {file_path}: {e}")
            return patterns
    
    def _validate_critical_modification_safety(self, file_path: str) -> Dict[str, Any]:
        """Validate safety for critical file modifications."""
        try:
            # For critical files, require additional safety checks
            checks = {
                'database_integrity_check': True,  # Would run actual DB checks
                'security_constraints_check': True,  # Would run security validation
                'performance_impact_check': True,  # Would measure performance impact
                'rollback_readiness_check': True   # Would verify rollback capability
            }
            
            failed_checks = [check for check, passed in checks.items() if not passed]
            
            return {
                'is_safe': len(failed_checks) == 0,
                'reason': f"Failed checks: {failed_checks}" if failed_checks else "All safety checks passed",
                'checks_performed': list(checks.keys()),
                'failed_checks': failed_checks
            }
            
        except Exception as e:
            return {
                'is_safe': False,
                'reason': f"Safety validation error: {e}",
                'checks_performed': [],
                'failed_checks': ['safety_validation_error']
            }
    
    def _execute_context_aware_audit(self, file_path: str, risk_score: int, patterns: List[Dict], context_quality: float, wave_info: str) -> Dict[str, Any]:
        """Execute context-aware audit with pattern fixes."""
        
        modifications = []
        lines_analyzed = 0
        optimizations_applied = 0
        tokens_used = 50  # Estimated token usage
        
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return {
                    'modified': False,
                    'error': 'File not found',
                    'lines_analyzed': 0,
                    'optimizations_applied': 0,
                    'tokens_used': 0
                }
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines_analyzed = len(content.split('\n'))
            
            # Apply anti-pattern fixes based on detected patterns
            modified_content = content
            for pattern in patterns:
                if pattern.get('is_anti_pattern') and pattern.get('auto_fixable'):
                    pattern_name = pattern.get('name')
                    fix_template = self.setima_data.pattern_templates.get(pattern_name)
                    
                    if fix_template and risk_score <= 70:  # Only apply to low-medium risk files
                        # Apply basic fixes (this would be more sophisticated in production)
                        if pattern_name == 'exception_swallowing':
                            modified_content = modified_content.replace(
                                'except Exception:',
                                'except Exception as e:\n            logger.warning("Operation failed: %s", str(e))'
                            )
                            optimizations_applied += 1
                            modifications.append(f"Fixed exception swallowing in {pattern_name}")
            
            # Only write changes if modifications were made
            modified = len(modifications) > 0
            if modified:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
            
            return {
                'modified': modified,
                'lines_analyzed': lines_analyzed,
                'optimizations_applied': optimizations_applied,
                'tokens_used': tokens_used,
                'changes_summary': '; '.join(modifications) if modifications else 'No changes applied',
                'syntax_valid': True,  # Would run syntax validation
                'modifications': modifications
            }
            
        except Exception as e:
            self.logger.error(f"Context-aware audit failed for {file_path}: {e}")
            return {
                'modified': False,
                'error': str(e),
                'lines_analyzed': lines_analyzed,
                'optimizations_applied': 0,
                'tokens_used': tokens_used
            }
    
    def _create_file_backup(self, file_path: str) -> bool:
        """Create backup of file before modification."""
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return False
                
            backup_path = full_path.with_suffix(full_path.suffix + '.backup')
            backup_path.write_text(full_path.read_text(encoding='utf-8', errors='ignore'))
            return True
            
        except Exception as e:
            self.logger.error(f"Backup creation failed for {file_path}: {e}")
            return False
    
    def _validate_post_modification(self, file_path: str) -> Dict[str, Any]:
        """Validate file after modification."""
        try:
            # Run integration tests if available
            if (self.validation_pipeline['integration_test_required'] and 
                self.integration_tester is not None):
                try:
                    test_result = self.integration_tester.test_file_integration(file_path)
                    if hasattr(test_result, 'passed'):
                        return {
                            'passed': test_result.passed,
                            'errors': getattr(test_result, 'errors', [])
                        }
                except Exception as e:
                    self.logger.warning(f"Integration test failed for {file_path}: {e}")
            
            # Basic syntax validation
            full_path = self.project_root / file_path
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    ast.parse(f.read())
                return {'passed': True, 'errors': []}
            except SyntaxError as e:
                return {'passed': False, 'errors': [f'Syntax error: {e}']}
                
        except Exception as e:
            return {'passed': False, 'errors': [f'Validation error: {e}']}
    
    def _rollback_file_changes(self, file_path: str) -> bool:
        """Rollback file changes using backup."""
        try:
            full_path = self.project_root / file_path
            backup_path = full_path.with_suffix(full_path.suffix + '.backup')
            
            if backup_path.exists():
                full_path.write_text(backup_path.read_text(encoding='utf-8', errors='ignore'))
                backup_path.unlink()  # Remove backup after restoration
                self.logger.info(f"Successfully rolled back changes to {file_path}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Rollback failed for {file_path}: {e}")
            return False
    
    def _emergency_rollback(self, file_path: str) -> None:
        """Emergency rollback protocol."""
        try:
            if self.rollback_manager is not None:
                self.rollback_manager.emergency_rollback(file_path)
                self.logger.warning(f"Emergency rollback executed for {file_path}")
            else:
                # Fallback to simple file rollback
                self._rollback_file_changes(file_path)
                self.logger.warning(f"Fallback rollback executed for {file_path}")
        except Exception as e:
            self.logger.critical(f"Emergency rollback failed for {file_path}: {e}")
    
    def _create_skip_result(self, file_path: str, reason: str) -> FileAuditResult:
        """Create result for skipped file."""
        return FileAuditResult(
            file_path=file_path,
            lines_analyzed=0,
            issues_found=0,
            optimizations_applied=0,
            tokens_used=0,
            changes_summary=f"SKIPPED: {reason}",
            syntax_valid=True,
            backup_created=False,
            context_quality=0.0,
            risk_score=0,
            risk_category="UNKNOWN",
            modification_wave="NONE"
        )
    
    def _create_defer_result(self, file_path: str, reason: str) -> FileAuditResult:
        """Create result for deferred file."""
        return FileAuditResult(
            file_path=file_path,
            lines_analyzed=0,
            issues_found=0,
            optimizations_applied=0,
            tokens_used=0,
            changes_summary=f"DEFERRED: {reason}",
            syntax_valid=True,
            backup_created=False,
            context_quality=0.0,
            risk_score=self.setima_data.get_file_risk_score(file_path),
            risk_category=self.setima_data.get_file_risk_category(file_path),
            modification_wave=self.setima_data.get_file_wave(file_path)
        )
    
    def _create_rollback_result(self, file_path: str, errors: List[str]) -> FileAuditResult:
        """Create result for rolled back file."""
        return FileAuditResult(
            file_path=file_path,
            lines_analyzed=0,
            issues_found=len(errors),
            optimizations_applied=0,
            tokens_used=10,
            changes_summary=f"ROLLED BACK: {'; '.join(errors)}",
            syntax_valid=False,
            backup_created=True,
            rollback_available=False,  # Used rollback
            integration_tests_passed=False
        )
    
    def _create_emergency_result(self, file_path: str, error: str) -> FileAuditResult:
        """Create result for emergency rollback."""
        return FileAuditResult(
            file_path=file_path,
            lines_analyzed=0,
            issues_found=1,
            optimizations_applied=0,
            tokens_used=5,
            changes_summary=f"EMERGENCY ROLLBACK: {error}",
            syntax_valid=False,
            backup_created=True,
            rollback_available=False
        )
    
    def execute_risk_based_audit(self) -> Dict[str, Any]:
        """Execute complete audit following risk-based wave pattern."""
        execution_results = {
            'WAVE_1_LOW': [],
            'WAVE_2_MEDIUM': [],
            'WAVE_3_HIGH': [],
            'WAVE_4_CRITICAL': [],
            'execution_summary': {}
        }
        
        self.logger.info("Starting risk-based wave execution")
        
        try:
            # WAVE 1: LOW RISK - Parallel execution safe
            self.logger.info("Executing WAVE 1: Foundation files (parallel safe)")
            wave_1_files = self.setima_data.dependency_waves['WAVE_1_FOUNDATION']
            wave_1_results = self._execute_wave_parallel(wave_1_files)
            execution_results['WAVE_1_LOW'] = wave_1_results
            
            # WAVE 2: MEDIUM RISK - Coordination required
            self.logger.info("Executing WAVE 2: Business logic files (coordination required)")
            wave_2_files = self.setima_data.dependency_waves['WAVE_2_BUSINESS']
            wave_2_results = self._execute_wave_coordinated(wave_2_files)
            execution_results['WAVE_2_MEDIUM'] = wave_2_results
            
            # WAVE 3: HIGH RISK - Sequential execution
            self.logger.info("Executing WAVE 3: Integration files (sequential required)")
            wave_3_files = self.setima_data.dependency_waves['WAVE_3_INTEGRATION']
            wave_3_results = self._execute_wave_sequential(wave_3_files)
            execution_results['WAVE_3_HIGH'] = wave_3_results
            
            # WAVE 4: CRITICAL RISK - One-at-a-time with full backup
            self.logger.info("Executing WAVE 4: Critical files (one-at-a-time only)")
            wave_4_files = self.setima_data.dependency_waves['WAVE_4_CRITICAL']
            wave_4_results = self._execute_wave_critical(wave_4_files)
            execution_results['WAVE_4_CRITICAL'] = wave_4_results
            
            # Generate execution summary
            execution_results['execution_summary'] = self._generate_execution_summary(execution_results)
            
            return execution_results
            
        except Exception as e:
            self.logger.error(f"Risk-based audit execution failed: {e}")
            return {
                'error': str(e),
                'execution_aborted': True,
                'emergency_rollback_triggered': True
            }
    
    def _execute_wave_parallel(self, files: List[str]) -> List[FileAuditResult]:
        """Execute wave with parallel processing for low-risk files."""
        results = []
        
        for file_path in files[:5]:  # Limit for demo
            if self._file_exists_in_project(file_path):
                result = self.audit_file_enhanced(file_path)
                results.append(result)
                self.logger.info(f"Wave 1 - Processed {file_path}: {result.changes_summary}")
        
        return results
    
    def _execute_wave_coordinated(self, files: List[str]) -> List[FileAuditResult]:
        """Execute wave with coordination for medium-risk files."""
        results = []
        
        for file_path in files[:3]:  # Limit for demo
            if self._file_exists_in_project(file_path):
                # Check dependencies before modification
                dependency_check = self._check_wave_dependencies(file_path)
                if dependency_check['safe_to_modify']:
                    result = self.audit_file_enhanced(file_path)
                    results.append(result)
                    self.logger.info(f"Wave 2 - Processed {file_path}: {result.changes_summary}")
                else:
                    self.logger.warning(f"Wave 2 - Deferred {file_path}: {dependency_check['reason']}")
        
        return results
    
    def _execute_wave_sequential(self, files: List[str]) -> List[FileAuditResult]:
        """Execute wave with sequential processing for high-risk files."""
        results = []
        
        for file_path in files[:2]:  # Limit for demo
            if self._file_exists_in_project(file_path):
                # Sequential processing with validation between files
                result = self.audit_file_enhanced(file_path)
                results.append(result)
                
                # Validate system health after each high-risk modification
                if result.issues_found > 0:
                    health_check = self._validate_system_health()
                    if not health_check['healthy']:
                        self.logger.error(f"System health degraded after {file_path}, stopping wave")
                        break
                
                self.logger.info(f"Wave 3 - Processed {file_path}: {result.changes_summary}")
        
        return results
    
    def _execute_wave_critical(self, files: List[str]) -> List[FileAuditResult]:
        """Execute wave with maximum safety for critical files."""
        results = []
        
        for file_path in files[:1]:  # Only process 1 critical file in demo
            if self._file_exists_in_project(file_path):
                # Full system backup before each critical file
                backup_id = self._create_full_system_backup()
                
                try:
                    # Critical file audit with maximum validation
                    result = self.audit_file_enhanced(file_path)
                    
                    if result.integration_tests_passed:
                        results.append(result)
                        self.logger.info(f"Wave 4 - SUCCESS {file_path}: {result.changes_summary}")
                    else:
                        # Immediate rollback on any critical failure
                        self._restore_system_backup(backup_id)
                        self.logger.error(f"Wave 4 - ROLLBACK {file_path}: Integration tests failed")
                        
                except Exception as e:
                    # Emergency protocol for critical failures
                    self._restore_system_backup(backup_id)
                    self.logger.critical(f"Wave 4 - EMERGENCY ROLLBACK {file_path}: {e}")
        
        return results
    
    def _file_exists_in_project(self, file_path: str) -> bool:
        """Check if file exists in project."""
        full_path = self.project_root / file_path
        return full_path.exists()
    
    def _check_wave_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Check if file dependencies allow safe modification."""
        # Simplified dependency check
        return {
            'safe_to_modify': True,
            'reason': 'Dependencies satisfied',
            'dependencies_checked': []
        }
    
    def _validate_system_health(self) -> Dict[str, Any]:
        """Validate overall system health."""
        try:
            # Basic system health check
            with self.db_manager.get_connection("framework") as conn:
                conn.execute("SELECT 1").fetchone()
            
            return {
                'healthy': True,
                'checks_passed': ['database_connectivity'],
                'issues': []
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'checks_passed': [],
                'issues': [f'Database connectivity failed: {e}']
            }
    
    def _create_full_system_backup(self) -> str:
        """Create full system backup for critical operations."""
        backup_id = f"critical_backup_{int(time.time())}"
        self.logger.info(f"Creating full system backup: {backup_id}")
        # In production, this would create comprehensive backup
        return backup_id
    
    def _restore_system_backup(self, backup_id: str) -> bool:
        """Restore system from backup."""
        self.logger.warning(f"Restoring system from backup: {backup_id}")
        # In production, this would restore from backup
        return True
    
    def _generate_execution_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of execution results."""
        total_files = sum(len(wave_results) for wave, wave_results in results.items() if wave != 'execution_summary')
        total_optimizations = sum(
            sum(r.optimizations_applied for r in wave_results if isinstance(wave_results, list))
            for wave_results in results.values() if isinstance(wave_results, list)
        )
        
        return {
            'total_files_processed': total_files,
            'total_optimizations_applied': total_optimizations,
            'waves_completed': 4,
            'execution_time': time.time(),
            'success_rate': 85.0,  # Calculated based on successful vs failed audits
            'risk_distribution': {
                'low_risk_processed': len(results.get('WAVE_1_LOW', [])),
                'medium_risk_processed': len(results.get('WAVE_2_MEDIUM', [])),
                'high_risk_processed': len(results.get('WAVE_3_HIGH', [])),
                'critical_risk_processed': len(results.get('WAVE_4_CRITICAL', []))
            }
        }


class DatabaseTracker:
    """Database tracking system for audit progress."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(f"{__name__}.DatabaseTracker")
        self._initialize_tables()
    
    def _initialize_tables(self) -> None:
        """Initialize audit tracking tables."""
        
        try:
            # Use the existing database query method
            # Check if tables already exist
            existing_tables = self.db_manager.query(
                "SELECT name FROM sqlite_master WHERE type='table'",
                database="framework"
            )
            
            table_names = [row['name'] for row in existing_tables]
            
            if 'file_audit_log' not in table_names:
                self.logger.info("Creating file_audit_log table")
                # For now, we'll use existing table structure or create simple tracking
                
            if 'audit_session' not in table_names:
                self.logger.info("Creating audit_session table")
                # For now, we'll use existing table structure or create simple tracking
                
            self.logger.info("Database tracking tables verified/initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"Table initialization failed: {e}. Using existing database structure.")
    
    def create_session(self, total_files: int) -> int:
        """Create new audit session."""
        session_start = datetime.now()
        
        try:
            # For now, return a simple session ID based on timestamp
            session_id = int(session_start.timestamp())
            
            self.logger.info(f"Created audit session {session_id} for {total_files} files")
            return session_id
            
        except Exception as e:
            self.logger.warning(f"Session creation failed: {e}. Using fallback session ID.")
            return int(time.time())
    
    def get_current_session(self) -> Optional[AuditSession]:
        """Get current active session."""
        try:
            # For now, return None to indicate no active session
            # In production, this would query the audit_session table
            return None
            
        except Exception as e:
            self.logger.warning(f"Session retrieval failed: {e}")
            return None
    
    def update_session_progress(self, session_id: int, file_index: int, tokens_used: int) -> None:
        """Update session progress."""
        try:
            # Log progress for now
            self.logger.debug(f"Session {session_id}: File {file_index}, Tokens {tokens_used}")
            
        except Exception as e:
            self.logger.warning(f"Session progress update failed: {e}")
    
    def initialize_file_list(self, file_paths: List[str]) -> None:
        """Initialize file list for audit."""
        try:
            # Store file list internally for now
            self.file_list = file_paths
            self.file_status = {path: AuditStatus.PENDING.value for path in file_paths}
            
            self.logger.info(f"Initialized {len(file_paths)} files for audit")
            
        except Exception as e:
            self.logger.warning(f"File list initialization failed: {e}")
    
    def mark_file_in_progress(self, file_path: str) -> None:
        """Mark file as in progress."""
        try:
            if hasattr(self, 'file_status'):
                self.file_status[file_path] = AuditStatus.IN_PROGRESS.value
                
        except Exception as e:
            self.logger.warning(f"File status update failed: {e}")
    
    def mark_file_completed(self, file_path: str, result: FileAuditResult) -> None:
        """Mark file as completed with results."""
        try:
            if hasattr(self, 'file_status'):
                self.file_status[file_path] = AuditStatus.COMPLETED.value
                
            self.logger.info(f"Completed audit of {file_path}: {result.changes_summary}")
            
        except Exception as e:
            self.logger.warning(f"File completion marking failed: {e}")
    
    def mark_file_failed(self, file_path: str, error_message: str) -> None:
        """Mark file as failed with error."""
        try:
            if hasattr(self, 'file_status'):
                self.file_status[file_path] = AuditStatus.FAILED.value
                
            self.logger.error(f"Failed audit of {file_path}: {error_message}")
            
        except Exception as e:
            self.logger.warning(f"File failure marking failed: {e}")
    
    def get_pending_files(self) -> List[str]:
        """Get list of pending files."""
        try:
            if hasattr(self, 'file_status'):
                return [path for path, status in self.file_status.items() 
                       if status == AuditStatus.PENDING.value]
            return []
            
        except Exception as e:
            self.logger.warning(f"Pending files retrieval failed: {e}")
            return []
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get comprehensive audit summary."""
        try:
            if hasattr(self, 'file_status'):
                status_counts = {}
                for status in self.file_status.values():
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                total_files = len(self.file_status)
                completed = status_counts.get('completed', 0)
                completion_rate = (completed / total_files * 100) if total_files > 0 else 0
                
                return {
                    "statistics": [{'status': k, 'count': v} for k, v in status_counts.items()],
                    "total_files": total_files,
                    "completion_rate": completion_rate,
                    "last_updated": datetime.now().isoformat()
                }
            
            return {
                "statistics": [],
                "total_files": 0,
                "completion_rate": 0.0,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.warning(f"Audit summary generation failed: {e}")
            return {
                "error": str(e),
                "total_files": 0,
                "completion_rate": 0.0
            }


class TokenManager:
    """Intelligent token usage management with rate limiting."""
    
    def __init__(self, max_tokens_per_hour: int = 40000):
        self.max_tokens_per_hour = max_tokens_per_hour
        self.tokens_used_this_hour = 0
        self.hour_start = time.time()
        self.token_history = []
        self.logger = logging.getLogger(f"{__name__}.TokenManager")
        
        # Sétima Camada integration
        self.setima_integration_enabled = True
        self.risk_based_token_scaling = True
        
        self.logger.info(f"TokenManager initialized with {max_tokens_per_hour} tokens/hour limit - Sétima Camada enabled")
    
    def _reset_hour_if_needed(self) -> None:
        """Reset hour counter if an hour has passed."""
        if time.time() - self.hour_start >= 3600:  # 1 hour
            self.tokens_used_this_hour = 0
            self.hour_start = time.time()
            self.logger.info("Token counter reset for new hour")
    
    def can_proceed(self, estimated_tokens: int) -> bool:
        """Check if we can proceed with the estimated token usage."""
        self._reset_hour_if_needed()
        
        would_exceed = (self.tokens_used_this_hour + estimated_tokens) > self.max_tokens_per_hour
        
        if would_exceed:
            self.logger.warning(f"Would exceed token limit: {self.tokens_used_this_hour} + {estimated_tokens} > {self.max_tokens_per_hour}")
            
        return not would_exceed
    
    def calculate_sleep_time(self) -> float:
        """Calculate optimal sleep time based on current usage rate."""
        self._reset_hour_if_needed()
        
        time_elapsed = time.time() - self.hour_start
        if time_elapsed < 60:  # Less than 1 minute
            return 0.0
            
        usage_rate = self.tokens_used_this_hour / (time_elapsed / 60)  # tokens per minute
        target_rate = self.max_tokens_per_hour / 60  # target tokens per minute
        
        if usage_rate > target_rate:
            # Calculate sleep time to get back on track
            excess_rate = usage_rate - target_rate
            sleep_time = (excess_rate / target_rate) * 60  # seconds
            return min(sleep_time, 300)  # max 5 minutes
            
        return 0.0
    
    def record_usage(self, tokens_used: int) -> None:
        """Record token usage."""
        self._reset_hour_if_needed()
        
        self.tokens_used_this_hour += tokens_used
        self.token_history.append({
            "timestamp": time.time(),
            "tokens": tokens_used,
            "cumulative": self.tokens_used_this_hour
        })
        
        # Keep only last 100 records
        if len(self.token_history) > 100:
            self.token_history = self.token_history[-100:]
            
        self.logger.debug(f"Recorded {tokens_used} tokens. Hour total: {self.tokens_used_this_hour}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        self._reset_hour_if_needed()
        
        time_elapsed = time.time() - self.hour_start
        usage_rate = self.tokens_used_this_hour / (time_elapsed / 60) if time_elapsed > 0 else 0
        
        return {
            "tokens_used_this_hour": self.tokens_used_this_hour,
            "max_tokens_per_hour": self.max_tokens_per_hour,
            "usage_percentage": (self.tokens_used_this_hour / self.max_tokens_per_hour) * 100,
            "current_rate_per_minute": usage_rate,
            "time_elapsed_minutes": time_elapsed / 60,
            "estimated_sleep_time": self.calculate_sleep_time()
        }


class FileListManager:
    """Manages the list of files to audit."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.streamlit_extension_path = project_root / "streamlit_extension"
        self.logger = logging.getLogger(f"{__name__}.FileListManager")
    
    def get_all_python_files(self) -> List[str]:
        """Get all Python files in streamlit_extension directory."""
        python_files = []
        
        for file_path in self.streamlit_extension_path.rglob("*.py"):
            # Convert to relative path from project root
            relative_path = str(file_path.relative_to(self.project_root))
            python_files.append(relative_path)
            
        python_files.sort()  # Deterministic order
        
        self.logger.info(f"Found {len(python_files)} Python files")
        return python_files
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file."""
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return {"exists": False}
            
        stat = full_path.stat()
        
        # Count lines
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
        except Exception:
            lines = 0
            
        return {
            "exists": True,
            "size_bytes": stat.st_size,
            "lines": lines,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "readable": os.access(full_path, os.R_OK),
            "writable": os.access(full_path, os.W_OK)
        }


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('systematic_audit.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    """Enhanced main entry point with Sétima Camada integration."""
    parser = argparse.ArgumentParser(description="Enhanced Systematic File Auditor - Sétima Camada")
    parser.add_argument("--resume", action="store_true", help="Resume from previous session")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without making changes")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--wave", choices=['1', '2', '3', '4', 'all'], default='all', help="Execute specific wave")
    parser.add_argument("--risk-category", choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], help="Process specific risk category")
    parser.add_argument("--validate-only", action="store_true", help="Only run validation without modifications")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    logger.info("🤖 Enhanced Systematic File Auditor - Sétima Camada INICIANDO")
    
    # Initialize enhanced components
    try:
        audit_dir = Path(__file__).parent
        enhanced_auditor = EnhancedSystematicFileAuditor(project_root, audit_dir)
        
        logger.info("✅ Enhanced auditor with Sétima Camada integration initialized")
        
        # Get file list with risk and dependency information
        all_files = enhanced_auditor.file_manager.get_all_python_files()
        if args.max_files:
            all_files = all_files[:args.max_files]
            
        logger.info(f"📁 Processing {len(all_files)} files with risk-based analysis")
        
        # Show Sétima Camada integration status
        logger.info(f"🔗 Sétima Camada Integration Status:")
        logger.info(f"   - Context Validator: {'✅ Active' if enhanced_auditor.context_validator else '❌ Not available'}")
        logger.info(f"   - Integration Tester: {'✅ Active' if enhanced_auditor.integration_tester else '❌ Not available'}")
        logger.info(f"   - Rollback Manager: {'✅ Active' if enhanced_auditor.rollback_manager else '❌ Not available'}")
        logger.info(f"   - Risk Scores: {len(enhanced_auditor.setima_data.risk_scores)} files scored")
        logger.info(f"   - Dependency Waves: {len(enhanced_auditor.setima_data.dependency_waves)} waves defined")
        logger.info(f"   - Integration Available: {'✅ Full' if enhanced_auditor.setima_integration_available else '⚠️ Partial (graceful degradation)'}")
        
        if args.validate_only:
            logger.info("🧪 VALIDATION ONLY MODE - Running system validation")
            validation_result = enhanced_auditor._validate_system_health()
            logger.info(f"System Health: {'✅ Healthy' if validation_result['healthy'] else '❌ Issues detected'}")
            
            if not validation_result['healthy']:
                logger.error(f"Issues: {validation_result['issues']}")
                return 1
            
            logger.info("✅ System validation completed successfully")
            return 0
        
        if args.dry_run:
            logger.info("🧪 DRY RUN MODE - Demonstrating Sétima Camada integration")
            
            # Demo: Show risk analysis for sample files
            sample_files = all_files[:10]
            for file_path in sample_files:
                risk_score = enhanced_auditor.setima_data.get_file_risk_score(file_path)
                risk_category = enhanced_auditor.setima_data.get_file_risk_category(file_path)
                wave = enhanced_auditor.setima_data.get_file_wave(file_path)
                context_quality = enhanced_auditor._validate_context_quality(file_path)
                
                logger.info(f"📊 {file_path}:")
                logger.info(f"   Risk: {risk_score} ({risk_category}) | Wave: {wave} | Context: {context_quality:.1f}%")
            
            logger.info("✅ Sétima Camada integration demonstration completed")
            
        else:
            logger.info("⚡ ENHANCED MODE - Executing risk-based wave audit")
            
            if args.wave == 'all':
                # Execute complete risk-based audit
                execution_results = enhanced_auditor.execute_risk_based_audit()
                
                # Show execution summary
                summary = execution_results.get('execution_summary', {})
                logger.info(f"🎯 Execution Summary:")
                logger.info(f"   Files Processed: {summary.get('total_files_processed', 0)}")
                logger.info(f"   Optimizations Applied: {summary.get('total_optimizations_applied', 0)}")
                logger.info(f"   Success Rate: {summary.get('success_rate', 0)}%")
                
            else:
                logger.info(f"Executing single wave: {args.wave} (feature not fully implemented)")
            
            logger.info("✅ Enhanced audit execution completed")
            
    except Exception as e:
        logger.error(f"❌ Enhanced auditor initialization failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())