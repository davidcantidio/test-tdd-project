#!/usr/bin/env python3
"""
🚀 TDD Project Template - Production Readiness & Scalability Audit
================================================================

Auditoria rigorosa de prontidão para produção, escalabilidade,
performance, deployment e manutenibilidade.

Uso:
    python scripts/audit_production_readiness.py
    python scripts/audit_production_readiness.py --verbose --performance-test
"""

import argparse
import json
import os
import sys
import re
import subprocess
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import hashlib


class ProductionReadinessAuditor:
    """Auditor rigoroso de prontidão para produção."""
    
    def __init__(self, verbose: bool = False, performance_test: bool = False):
        self.verbose = verbose
        self.performance_test = performance_test
        self.project_root = Path.cwd()
        self.findings = []
        self.metrics = {}
        
    def log_finding(self, level: str, category: str, message: str, details: Optional[Dict] = None):
        """Log audit finding with structured data."""
        finding = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'category': category,
            'message': message,
            'details': details or {}
        }
        self.findings.append(finding)
        
        icons = {'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌', 'CRITICAL': '🔥', 'INFO': 'ℹ️'}
        icon = icons.get(level, 'ℹ️')
        print(f"{icon} [{category}] {message}")
        if self.verbose and details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def audit_deployment_readiness(self) -> Dict[str, Any]:
        """Audit deployment configuration and CI/CD readiness."""
        print("\n🚀 AUDITING DEPLOYMENT READINESS")
        print("=" * 50)
        
        deployment_metrics = {
            'github_actions_quality': {},
            'docker_support': {},
            'environment_management': {},
            'secrets_handling': {}
        }
        
        deployment_score = 0
        
        # Check GitHub Actions workflow quality
        workflow_path = self.project_root / '.github' / 'workflows' / 'update-tdd-gantt.yml'
        if workflow_path.exists():
            try:
                import yaml
                with open(workflow_path, 'r') as f:
                    workflow_config = yaml.safe_load(f)
                
                # Check workflow robustness
                has_error_handling = 'continue-on-error' in str(workflow_config)
                has_timeout = 'timeout-minutes' in str(workflow_config)
                has_dependency_caching = 'cache' in str(workflow_config).lower()
                has_matrix_builds = 'matrix' in str(workflow_config)
                has_environment_gates = 'environment' in str(workflow_config)
                
                workflow_quality_score = 0
                
                if has_dependency_caching:
                    workflow_quality_score += 25
                    self.log_finding('SUCCESS', 'DEPLOYMENT', "Workflow uses dependency caching")
                else:
                    self.log_finding('WARNING', 'DEPLOYMENT', "Missing dependency caching in workflow")
                
                if has_error_handling:
                    workflow_quality_score += 20
                    self.log_finding('SUCCESS', 'DEPLOYMENT', "Workflow has error handling")
                
                if has_timeout:
                    workflow_quality_score += 15
                    self.log_finding('SUCCESS', 'DEPLOYMENT', "Workflow has timeout protection")
                else:
                    self.log_finding('WARNING', 'DEPLOYMENT', "Missing timeout protection")
                
                # Check for production-ready practices
                workflow_content = str(workflow_config)
                if 'secrets.' in workflow_content:
                    workflow_quality_score += 20
                    self.log_finding('SUCCESS', 'DEPLOYMENT', "Proper secrets management")
                
                if 'permissions:' in workflow_content:
                    workflow_quality_score += 20
                    self.log_finding('SUCCESS', 'DEPLOYMENT', "Explicit permissions configured")
                else:
                    self.log_finding('WARNING', 'DEPLOYMENT', "Missing explicit permissions")
                
                deployment_metrics['github_actions_quality'] = {
                    'score': workflow_quality_score,
                    'has_caching': has_dependency_caching,
                    'has_error_handling': has_error_handling,
                    'has_timeout': has_timeout,
                    'has_secrets': 'secrets.' in workflow_content
                }
                
                deployment_score += workflow_quality_score * 0.4
                
            except Exception as e:
                self.log_finding('ERROR', 'DEPLOYMENT', f"Failed to analyze workflow: {str(e)}")
                deployment_score += 0
        else:
            self.log_finding('WARNING', 'DEPLOYMENT', "No GitHub Actions workflow found")
        
        # Check Docker support
        docker_files = [
            'Dockerfile',
            'docker-compose.yml',
            'config/docker/Dockerfile',
            'config/docker/docker-compose.yml'
        ]
        
        docker_score = 0
        docker_found = False
        
        for docker_file in docker_files:
            docker_path = self.project_root / docker_file
            if docker_path.exists():
                docker_found = True
                content = docker_path.read_text()
                
                if 'Dockerfile' in docker_file:
                    # Check Dockerfile best practices
                    has_non_root_user = 'USER ' in content and 'USER root' not in content
                    has_multistage = 'FROM ' in content and content.count('FROM ') > 1
                    has_health_check = 'HEALTHCHECK' in content
                    has_minimal_layers = content.count('RUN ') <= 5
                    
                    if has_non_root_user:
                        docker_score += 25
                        self.log_finding('SUCCESS', 'DEPLOYMENT', "Dockerfile uses non-root user")
                    else:
                        self.log_finding('WARNING', 'DEPLOYMENT', "Dockerfile missing non-root user")
                    
                    if has_multistage:
                        docker_score += 20
                        self.log_finding('SUCCESS', 'DEPLOYMENT', "Dockerfile uses multi-stage build")
                    
                    if has_health_check:
                        docker_score += 15
                        self.log_finding('SUCCESS', 'DEPLOYMENT', "Dockerfile has health check")
                    
                    if has_minimal_layers:
                        docker_score += 10
                        self.log_finding('SUCCESS', 'DEPLOYMENT', "Dockerfile optimized layers")
                        
                elif 'docker-compose' in docker_file:
                    # Check docker-compose best practices
                    has_volumes = 'volumes:' in content
                    has_networks = 'networks:' in content
                    has_env_files = '.env' in content
                    has_restart_policy = 'restart:' in content
                    
                    if has_volumes:
                        docker_score += 15
                    if has_env_files:
                        docker_score += 15
                        self.log_finding('SUCCESS', 'DEPLOYMENT', "Docker Compose uses env files")
                    if has_restart_policy:
                        docker_score += 10
                        self.log_finding('SUCCESS', 'DEPLOYMENT', "Docker Compose has restart policy")
        
        if docker_found:
            self.log_finding('SUCCESS', 'DEPLOYMENT', "Docker support available")
        else:
            self.log_finding('WARNING', 'DEPLOYMENT', "No Docker support found")
        
        deployment_metrics['docker_support'] = {
            'available': docker_found,
            'score': docker_score
        }
        
        deployment_score += docker_score * 0.3
        
        # Check environment management
        env_score = 0
        env_files = ['.env.example', 'config/environment/.env.example']
        
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                content = env_path.read_text()
                
                # Check for comprehensive environment variables
                env_vars = [line for line in content.split('\n') if '=' in line and not line.startswith('#')]
                if len(env_vars) >= 5:
                    env_score += 30
                    self.log_finding('SUCCESS', 'DEPLOYMENT', f"Comprehensive env template: {env_file}")
                elif len(env_vars) > 0:
                    env_score += 15
                    self.log_finding('WARNING', 'DEPLOYMENT', f"Basic env template: {env_file}")
                
                # Check for production-specific variables
                prod_vars = ['DEBUG', 'LOG_LEVEL', 'ENVIRONMENT', 'PORT']
                found_prod_vars = sum(1 for var in prod_vars if var in content)
                if found_prod_vars >= 2:
                    env_score += 20
                    self.log_finding('SUCCESS', 'DEPLOYMENT', "Production environment variables configured")
                
                break
        
        # Check .gitignore for environment security
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            if '.env' in gitignore_content:
                env_score += 30
                self.log_finding('SUCCESS', 'DEPLOYMENT', "Environment files properly ignored")
            else:
                self.log_finding('CRITICAL', 'DEPLOYMENT', "Environment files not in .gitignore")
        
        deployment_metrics['environment_management'] = {
            'score': env_score,
            'has_env_template': any((self.project_root / f).exists() for f in env_files),
            'properly_ignored': '.env' in gitignore_content if gitignore_path.exists() else False
        }
        
        deployment_score += env_score * 0.3
        
        self.metrics['deployment_readiness_score'] = min(100, deployment_score)
        
        return {
            'score': min(100, deployment_score),
            'metrics': deployment_metrics
        }
    
    def audit_scalability_architecture(self) -> Dict[str, Any]:
        """Audit architecture for scalability and maintainability."""
        print("\n📈 AUDITING SCALABILITY ARCHITECTURE")
        print("=" * 50)
        
        scalability_metrics = {
            'code_organization': {},
            'dependency_management': {},
            'configuration_management': {},
            'monitoring_observability': {}
        }
        
        scalability_score = 0
        
        # Check code organization
        python_files = list(self.project_root.rglob("*.py"))
        total_loc = 0
        large_files = []
        
        for py_file in python_files:
            try:
                content = py_file.read_text()
                lines = len(content.split('\n'))
                total_loc += lines
                
                if lines > 500:
                    large_files.append({'file': str(py_file.relative_to(self.project_root)), 'lines': lines})
                    
            except Exception:
                continue
        
        # Calculate code organization score
        org_score = 0
        
        if len(large_files) == 0:
            org_score += 30
            self.log_finding('SUCCESS', 'SCALABILITY', "No overly large files detected")
        elif len(large_files) <= 2:
            org_score += 20
            self.log_finding('WARNING', 'SCALABILITY', f"{len(large_files)} large files found")
        else:
            self.log_finding('ERROR', 'SCALABILITY', f"{len(large_files)} large files may hurt maintainability")
        
        # Check directory structure scalability
        expected_patterns = [
            'scripts/',
            'config/',
            'docs/',
            'tests/' 
        ]
        
        found_patterns = sum(1 for pattern in expected_patterns 
                           if (self.project_root / pattern.rstrip('/')).exists())
        
        if found_patterns >= 3:
            org_score += 30
            self.log_finding('SUCCESS', 'SCALABILITY', "Good modular directory structure")
        elif found_patterns >= 2:
            org_score += 20
            
        # Check for separation of concerns
        config_files = list(self.project_root.rglob("*.yml")) + list(self.project_root.rglob("*.yaml")) + list(self.project_root.rglob("*.json"))
        if len(config_files) >= 3:
            org_score += 20
            self.log_finding('SUCCESS', 'SCALABILITY', "Configuration externalized")
        
        # Check for utility/helper modules
        util_patterns = ['util', 'helper', 'common', 'shared']
        has_utils = any(pattern in str(f).lower() for f in python_files for pattern in util_patterns)
        if has_utils:
            org_score += 20
            self.log_finding('SUCCESS', 'SCALABILITY', "Utility modules for code reuse")
        
        scalability_metrics['code_organization'] = {
            'total_lines_of_code': total_loc,
            'large_files': len(large_files),
            'modular_structure': found_patterns >= 3,
            'score': org_score
        }
        
        scalability_score += org_score * 0.4
        
        # Check dependency management scalability
        dep_score = 0
        
        # Check for lock files (dependency pinning)
        lock_files = ['poetry.lock', 'package-lock.json', 'yarn.lock']
        has_lock_file = any((self.project_root / lock_file).exists() for lock_file in lock_files)
        
        if has_lock_file:
            dep_score += 40
            self.log_finding('SUCCESS', 'SCALABILITY', "Dependencies properly locked")
        else:
            self.log_finding('WARNING', 'SCALABILITY', "No lock file found for dependencies")
        
        # Check for development vs production dependencies separation
        pyproject_path = self.project_root / 'pyproject.toml'
        if pyproject_path.exists():
            try:
                import toml
                config = toml.load(pyproject_path)
                
                has_dev_deps = bool(config.get('tool', {}).get('poetry', {}).get('group', {}).get('dev'))
                has_optional_deps = bool(config.get('tool', {}).get('poetry', {}).get('extras'))
                
                if has_dev_deps:
                    dep_score += 30
                    self.log_finding('SUCCESS', 'SCALABILITY', "Development dependencies separated")
                
                if has_optional_deps:
                    dep_score += 30
                    self.log_finding('SUCCESS', 'SCALABILITY', "Optional dependencies for feature scaling")
                    
            except Exception:
                pass
        
        scalability_metrics['dependency_management'] = {
            'has_lock_file': has_lock_file,
            'score': dep_score
        }
        
        scalability_score += dep_score * 0.3
        
        # Check configuration management
        config_score = 0
        
        # Check for environment-based configuration
        env_patterns = ['.env.example', 'config/', 'settings.py', 'config.py']
        config_files_found = sum(1 for pattern in env_patterns 
                               if list(self.project_root.rglob(pattern)))
        
        if config_files_found >= 2:
            config_score += 50
            self.log_finding('SUCCESS', 'SCALABILITY', "Multiple configuration methods available")
        elif config_files_found >= 1:
            config_score += 30
        
        # Check for configuration validation
        validation_patterns = ['schema', 'validate', 'config_check']
        has_validation = any(pattern in str(f).lower() for f in python_files for pattern in validation_patterns)
        
        if has_validation:
            config_score += 50
            self.log_finding('SUCCESS', 'SCALABILITY', "Configuration validation detected")
        else:
            self.log_finding('WARNING', 'SCALABILITY', "No configuration validation found")
        
        scalability_metrics['configuration_management'] = {
            'config_methods': config_files_found,
            'has_validation': has_validation,
            'score': config_score
        }
        
        scalability_score += config_score * 0.3
        
        self.metrics['scalability_score'] = min(100, scalability_score)
        
        return {
            'score': min(100, scalability_score),
            'metrics': scalability_metrics
        }
    
    def audit_performance_characteristics(self) -> Dict[str, Any]:
        """Audit performance characteristics and optimization potential."""
        print("\n⚡ AUDITING PERFORMANCE CHARACTERISTICS")
        print("=" * 50)
        
        performance_metrics = {
            'script_execution_times': {},
            'memory_usage_patterns': {},
            'io_optimization': {},
            'caching_strategies': {}
        }
        
        performance_score = 0
        
        if self.performance_test:
            # Test script execution times
            test_scripts = [
                'scripts/test_setup.py',
                'scripts/commit_helper.py'
            ]
            
            execution_times = {}
            
            for script in test_scripts:
                script_path = self.project_root / script
                if script_path.exists():
                    try:
                        start_time = time.time()
                        result = subprocess.run([
                            sys.executable, str(script_path), '--help'
                        ], capture_output=True, text=True, timeout=30)
                        execution_time = time.time() - start_time
                        
                        execution_times[script] = {
                            'time_seconds': round(execution_time, 3),
                            'success': result.returncode == 0
                        }
                        
                        if execution_time < 2.0:
                            performance_score += 20
                            self.log_finding('SUCCESS', 'PERFORMANCE', 
                                           f"Fast execution: {script} ({execution_time:.2f}s)")
                        elif execution_time < 5.0:
                            performance_score += 10
                            self.log_finding('WARNING', 'PERFORMANCE',
                                           f"Moderate execution: {script} ({execution_time:.2f}s)")
                        else:
                            self.log_finding('ERROR', 'PERFORMANCE',
                                           f"Slow execution: {script} ({execution_time:.2f}s)")
                            
                    except subprocess.TimeoutExpired:
                        execution_times[script] = {'time_seconds': 30.0, 'success': False}
                        self.log_finding('ERROR', 'PERFORMANCE', f"Timeout: {script}")
                    except Exception as e:
                        self.log_finding('ERROR', 'PERFORMANCE', f"Failed to test {script}: {str(e)}")
            
            performance_metrics['script_execution_times'] = execution_times
        
        # Check for performance optimization patterns
        python_files = list(self.project_root.rglob("*.py"))
        optimization_patterns = {
            'caching': ['cache', '@lru_cache', 'functools.lru_cache', 'memoize'],
            'lazy_loading': ['lazy', 'defer', 'on_demand'],
            'batch_processing': ['batch', 'bulk', 'chunk'],
            'async_patterns': ['async', 'await', 'asyncio'],
            'memory_optimization': ['generator', 'yield', 'itertools']
        }
        
        found_optimizations = {}
        
        for py_file in python_files:
            try:
                content = py_file.read_text()
                
                for pattern_type, patterns in optimization_patterns.items():
                    for pattern in patterns:
                        if pattern in content:
                            if pattern_type not in found_optimizations:
                                found_optimizations[pattern_type] = []
                            found_optimizations[pattern_type].append({
                                'file': str(py_file.relative_to(self.project_root)),
                                'pattern': pattern
                            })
                            
            except Exception:
                continue
        
        # Score optimization patterns
        optimization_score = 0
        for pattern_type, occurrences in found_optimizations.items():
            if len(occurrences) > 0:
                optimization_score += 15
                self.log_finding('SUCCESS', 'PERFORMANCE', 
                               f"Found {pattern_type} optimization patterns")
        
        performance_metrics['optimization_patterns'] = found_optimizations
        performance_score += optimization_score
        
        # Check for potential performance issues
        performance_issues = []
        
        for py_file in python_files:
            try:
                content = py_file.read_text()
                file_rel = str(py_file.relative_to(self.project_root))
                
                # Check for common performance anti-patterns
                if 'import *' in content:
                    performance_issues.append({
                        'file': file_rel,
                        'issue': 'wildcard_import',
                        'impact': 'medium'
                    })
                
                # Check for nested loops (simplified detection)
                nested_for_count = len(re.findall(r'for.*:\s*\n.*for.*:', content, re.MULTILINE))
                if nested_for_count > 2:
                    performance_issues.append({
                        'file': file_rel,
                        'issue': 'nested_loops',
                        'count': nested_for_count,
                        'impact': 'high'
                    })
                
                # Check for string concatenation in loops
                if re.search(r'for.*:\s*.*\+=.*str', content, re.MULTILINE | re.DOTALL):
                    performance_issues.append({
                        'file': file_rel,
                        'issue': 'string_concatenation_in_loop',
                        'impact': 'medium'
                    })
                    
            except Exception:
                continue
        
        # Penalize for performance issues
        performance_penalty = len(performance_issues) * 5
        performance_score = max(0, performance_score - performance_penalty)
        
        if performance_issues:
            self.log_finding('WARNING', 'PERFORMANCE', 
                           f"Found {len(performance_issues)} potential performance issues")
        else:
            performance_score += 20
            self.log_finding('SUCCESS', 'PERFORMANCE', "No obvious performance anti-patterns detected")
        
        performance_metrics['performance_issues'] = performance_issues
        
        self.metrics['performance_score'] = min(100, performance_score)
        
        return {
            'score': min(100, performance_score),
            'metrics': performance_metrics
        }
    
    def audit_monitoring_observability(self) -> Dict[str, Any]:
        """Audit monitoring and observability features."""
        print("\n📊 AUDITING MONITORING & OBSERVABILITY")
        print("=" * 50)
        
        monitoring_metrics = {
            'logging_implementation': {},
            'error_tracking': {},
            'metrics_collection': {},
            'health_checks': {}
        }
        
        monitoring_score = 0
        
        # Check logging implementation
        python_files = list(self.project_root.rglob("*.py"))
        logging_patterns = ['logging', 'logger', 'log.', 'print(']
        
        logging_usage = {}
        total_log_statements = 0
        
        for py_file in python_files:
            try:
                content = py_file.read_text()
                file_rel = str(py_file.relative_to(self.project_root))
                
                file_logging = {}
                for pattern in logging_patterns:
                    count = content.count(pattern)
                    if count > 0:
                        file_logging[pattern] = count
                        total_log_statements += count
                
                if file_logging:
                    logging_usage[file_rel] = file_logging
                    
            except Exception:
                continue
        
        if 'logging' in str(logging_usage) or 'logger' in str(logging_usage):
            monitoring_score += 30
            self.log_finding('SUCCESS', 'MONITORING', "Proper logging framework used")
        elif total_log_statements > 10:
            monitoring_score += 15
            self.log_finding('WARNING', 'MONITORING', "Basic logging with print statements")
        else:
            self.log_finding('WARNING', 'MONITORING', "Limited logging implementation")
        
        monitoring_metrics['logging_implementation'] = {
            'total_log_statements': total_log_statements,
            'files_with_logging': len(logging_usage),
            'uses_logging_framework': 'logging' in str(logging_usage)
        }
        
        # Check error handling and tracking
        error_handling_patterns = ['try:', 'except', 'raise', 'Exception', 'Error']
        error_handling_count = 0
        
        for py_file in python_files:
            try:
                content = py_file.read_text()
                for pattern in error_handling_patterns:
                    error_handling_count += content.count(pattern)
            except Exception:
                continue
        
        if error_handling_count > 20:
            monitoring_score += 25
            self.log_finding('SUCCESS', 'MONITORING', "Comprehensive error handling")
        elif error_handling_count > 10:
            monitoring_score += 15
            self.log_finding('WARNING', 'MONITORING', "Basic error handling")
        else:
            self.log_finding('WARNING', 'MONITORING', "Limited error handling")
        
        monitoring_metrics['error_tracking'] = {
            'error_handling_statements': error_handling_count
        }
        
        # Check for health check endpoints or scripts
        health_check_files = [
            'health_check.py',
            'healthcheck.py',
            'scripts/health_check.py'
        ]
        
        has_health_checks = any((self.project_root / hc).exists() for hc in health_check_files)
        
        # Check Docker health checks
        docker_files = list(self.project_root.rglob("*Dockerfile*"))
        has_docker_health_check = False
        
        for docker_file in docker_files:
            try:
                content = docker_file.read_text()
                if 'HEALTHCHECK' in content:
                    has_docker_health_check = True
                    break
            except Exception:
                continue
        
        if has_health_checks or has_docker_health_check:
            monitoring_score += 25
            self.log_finding('SUCCESS', 'MONITORING', "Health checks implemented")
        else:
            self.log_finding('WARNING', 'MONITORING', "No health checks found")
        
        monitoring_metrics['health_checks'] = {
            'has_health_check_scripts': has_health_checks,
            'has_docker_health_checks': has_docker_health_check
        }
        
        # Check for metrics and monitoring configurations
        monitoring_configs = [
            '.github/workflows/',  # GitHub Actions metrics
            'prometheus.yml',
            'grafana/',
            'monitoring/'
        ]
        
        monitoring_config_count = sum(1 for config in monitoring_configs 
                                    if (self.project_root / config.rstrip('/')).exists())
        
        if monitoring_config_count >= 2:
            monitoring_score += 20
            self.log_finding('SUCCESS', 'MONITORING', "Multiple monitoring systems configured")
        elif monitoring_config_count >= 1:
            monitoring_score += 10
            
        self.metrics['monitoring_score'] = min(100, monitoring_score)
        
        return {
            'score': min(100, monitoring_score),
            'metrics': monitoring_metrics
        }
    
    def generate_production_readiness_report(self) -> Dict[str, Any]:
        """Generate comprehensive production readiness report."""
        print("\n📊 GENERATING PRODUCTION READINESS REPORT")
        print("=" * 50)
        
        # Calculate overall score with weighted components
        weights = {
            'deployment_readiness_score': 0.3,
            'scalability_score': 0.25,
            'performance_score': 0.25,
            'monitoring_score': 0.2
        }
        
        overall_score = 0
        for metric, weight in weights.items():
            score = self.metrics.get(metric, 0)
            overall_score += score * weight
        
        # Categorize findings
        critical_issues = [f for f in self.findings if f['level'] == 'CRITICAL']
        errors = [f for f in self.findings if f['level'] == 'ERROR']
        warnings = [f for f in self.findings if f['level'] == 'WARNING']
        successes = [f for f in self.findings if f['level'] == 'SUCCESS']
        
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'overall_score': round(overall_score, 2),
            'grade': self._calculate_grade(overall_score),
            'production_readiness_level': self._calculate_readiness_level(overall_score),
            'weighted_scores': {k: round(self.metrics.get(k, 0), 2) for k in weights.keys()},
            'metrics': self.metrics,
            'summary': {
                'total_findings': len(self.findings),
                'critical_issues': len(critical_issues),
                'errors': len(errors),
                'warnings': len(warnings),
                'successes': len(successes)
            },
            'findings': self.findings,
            'recommendations': self._generate_production_recommendations()
        }
        
        # Console summary
        grade_colors = {
            'A+': '🟢', 'A': '🟢', 'B+': '🔵', 'B': '🔵', 
            'C+': '🟡', 'C': '🟡', 'D': '🟠', 'F': '🔴'
        }
        readiness_colors = {'PRODUCTION_READY': '🟢', 'NEAR_READY': '🔵', 'NEEDS_WORK': '🟡', 'NOT_READY': '🔴'}
        
        grade_color = grade_colors.get(report['grade'], '⚪')
        readiness_color = readiness_colors.get(report['production_readiness_level'], '⚪')
        
        print(f"\n{grade_color} OVERALL PRODUCTION GRADE: {report['grade']} ({overall_score:.1f}%)")
        print(f"{readiness_color} PRODUCTION READINESS: {report['production_readiness_level']}")
        print(f"📊 Component Scores:")
        for component, score in report['weighted_scores'].items():
            component_name = component.replace('_score', '').replace('_', ' ').title()
            print(f"    {component_name}: {score}%")
        print(f"📋 Total Findings: {len(self.findings)}")
        print(f"🔥 Critical: {len(critical_issues)}")
        print(f"❌ Errors: {len(errors)}")
        print(f"⚠️ Warnings: {len(warnings)}")
        print(f"✅ Successes: {len(successes)}")
        
        return report
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade based on score."""
        if score >= 95: return 'A+'
        elif score >= 90: return 'A'
        elif score >= 87: return 'B+'
        elif score >= 83: return 'B'
        elif score >= 80: return 'C+'
        elif score >= 75: return 'C'
        elif score >= 70: return 'D'
        else: return 'F'
    
    def _calculate_readiness_level(self, score: float) -> str:
        """Calculate production readiness level."""
        if score >= 90: return 'PRODUCTION_READY'
        elif score >= 75: return 'NEAR_READY'
        elif score >= 60: return 'NEEDS_WORK'
        else: return 'NOT_READY'
    
    def _generate_production_recommendations(self) -> List[str]:
        """Generate actionable production readiness recommendations."""
        recommendations = []
        
        critical_count = len([f for f in self.findings if f['level'] == 'CRITICAL'])
        if critical_count > 0:
            recommendations.append(f"🔥 CRITICAL: Fix {critical_count} critical issues before production deployment")
        
        if self.metrics.get('deployment_readiness_score', 0) < 80:
            recommendations.append("🚀 HIGH: Complete deployment configuration and CI/CD pipeline")
        
        if self.metrics.get('scalability_score', 0) < 70:
            recommendations.append("📈 HIGH: Improve code organization and configuration management")
        
        if self.metrics.get('performance_score', 0) < 70:
            recommendations.append("⚡ MEDIUM: Optimize performance and add caching strategies")
        
        if self.metrics.get('monitoring_score', 0) < 60:
            recommendations.append("📊 HIGH: Implement comprehensive logging and monitoring")
        
        error_count = len([f for f in self.findings if f['level'] == 'ERROR'])
        if error_count >= 5:
            recommendations.append(f"❌ MEDIUM: Address {error_count} error-level issues")
        
        if not recommendations:
            recommendations.append("🎉 Excellent! Template is production-ready with good scalability")
        
        return recommendations


def main():
    """Main production readiness audit execution."""
    parser = argparse.ArgumentParser(description="🚀 TDD Template Production Readiness Audit")
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output with detailed findings')
    parser.add_argument('--performance-test', action='store_true',
                       help='Run performance tests (slower but more accurate)')
    parser.add_argument('--report', choices=['console', 'json', 'both'], 
                       default='console', help='Report output format')
    parser.add_argument('--output', '-o', help='Output file for JSON report')
    
    args = parser.parse_args()
    
    print("🚀 TDD PROJECT TEMPLATE - PRODUCTION READINESS AUDIT")
    print("=" * 60)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Project: {Path.cwd()}")
    print(f"⚡ Performance Testing: {'YES' if args.performance_test else 'NO'}")
    
    auditor = ProductionReadinessAuditor(verbose=args.verbose, performance_test=args.performance_test)
    
    try:
        # Run all production readiness audits
        deployment_results = auditor.audit_deployment_readiness()
        scalability_results = auditor.audit_scalability_architecture()
        performance_results = auditor.audit_performance_characteristics()
        monitoring_results = auditor.audit_monitoring_observability()
        
        # Generate final report
        report = auditor.generate_production_readiness_report()
        
        # Output report
        if args.report in ['json', 'both']:
            output_file = args.output or f'production_readiness_audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 JSON report saved: {output_file}")
        
        # Return exit code based on readiness level
        readiness_codes = {'PRODUCTION_READY': 0, 'NEAR_READY': 1, 'NEEDS_WORK': 2, 'NOT_READY': 3}
        return readiness_codes.get(report['production_readiness_level'], 3)
        
    except KeyboardInterrupt:
        print("\n❌ Production readiness audit cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Production readiness audit failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())