#!/usr/bin/env python3
"""
⚙️ TDD Project Template - Functionality Core Audit
=================================================

Auditoria rigorosa da funcionalidade core do template.
Testa scripts, configurações, integrações e workflows.

Uso:
    python scripts/audit_functionality.py
    python scripts/audit_functionality.py --verbose --full-test
"""

import argparse
import json
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import re
from datetime import datetime
import importlib.util


class FunctionalityAuditor:
    """Auditor rigoroso da funcionalidade core do template TDD."""
    
    def __init__(self, verbose: bool = False, full_test: bool = False):
        self.verbose = verbose
        self.full_test = full_test
        self.project_root = Path.cwd()
        self.findings = []
        self.metrics = {}
        self.test_results = {}
        
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
    
    def test_python_scripts_syntax(self) -> Dict[str, Any]:
        """Test all Python scripts for syntax errors."""
        print("\n🐍 TESTING PYTHON SCRIPTS SYNTAX")
        print("=" * 50)
        
        python_files = list(self.project_root.rglob("*.py"))
        syntax_results = {}
        syntax_errors = 0
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try to compile
                compile(content, str(py_file), 'exec')
                
                syntax_results[str(py_file.relative_to(self.project_root))] = {
                    'syntax_valid': True,
                    'size_bytes': len(content),
                    'lines': len(content.split('\n')),
                    'has_shebang': content.startswith('#!'),
                    'has_docstring': '"""' in content,
                    'imports_count': len(re.findall(r'^import\s+\w+|^from\s+\w+', content, re.MULTILINE))
                }
                
                self.log_finding('SUCCESS', 'SYNTAX', 
                               f"Python syntax valid: {py_file.name}",
                               syntax_results[str(py_file.relative_to(self.project_root))])
                
            except SyntaxError as e:
                syntax_errors += 1
                error_details = {
                    'error': str(e),
                    'line': getattr(e, 'lineno', 'unknown'),
                    'offset': getattr(e, 'offset', 'unknown')
                }
                syntax_results[str(py_file.relative_to(self.project_root))] = {
                    'syntax_valid': False,
                    'error_details': error_details
                }
                self.log_finding('ERROR', 'SYNTAX',
                               f"Python syntax error: {py_file.name}",
                               error_details)
            except Exception as e:
                syntax_errors += 1
                self.log_finding('ERROR', 'SYNTAX',
                               f"Failed to read {py_file.name}: {str(e)}")
        
        syntax_score = max(0, ((len(python_files) - syntax_errors) / len(python_files)) * 100) if python_files else 100
        self.metrics['python_syntax_score'] = syntax_score
        
        return {
            'score': syntax_score,
            'total_files': len(python_files),
            'syntax_errors': syntax_errors,
            'results': syntax_results
        }
    
    def test_commit_helper_functionality(self) -> Dict[str, Any]:
        """Test commit helper script functionality."""
        print("\n🧪 TESTING COMMIT HELPER FUNCTIONALITY")  
        print("=" * 50)
        
        commit_helper_path = self.project_root / 'scripts' / 'commit_helper.py'
        
        if not commit_helper_path.exists():
            self.log_finding('ERROR', 'COMMIT_HELPER', "commit_helper.py not found")
            return {'score': 0, 'tests_passed': 0, 'total_tests': 0}
        
        test_results = {}
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Help command
        total_tests += 1
        try:
            result = subprocess.run([sys.executable, str(commit_helper_path), '--help'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'TDD' in result.stdout:
                tests_passed += 1
                self.log_finding('SUCCESS', 'COMMIT_HELPER', "Help command works")
                test_results['help_command'] = {'passed': True, 'output_length': len(result.stdout)}
            else:
                self.log_finding('ERROR', 'COMMIT_HELPER', 
                               f"Help command failed: {result.stderr}")
                test_results['help_command'] = {'passed': False, 'error': result.stderr}
        except Exception as e:
            self.log_finding('ERROR', 'COMMIT_HELPER', f"Help command exception: {str(e)}")
            test_results['help_command'] = {'passed': False, 'exception': str(e)}
        
        # Test 2: Guide command  
        total_tests += 1
        try:
            result = subprocess.run([sys.executable, str(commit_helper_path), '--guide'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'TDD Workflow' in result.stdout:
                tests_passed += 1
                self.log_finding('SUCCESS', 'COMMIT_HELPER', "Guide command works")
                test_results['guide_command'] = {'passed': True}
            else:
                self.log_finding('WARNING', 'COMMIT_HELPER', "Guide command issues")
                test_results['guide_command'] = {'passed': False, 'stderr': result.stderr}
        except Exception as e:
            self.log_finding('WARNING', 'COMMIT_HELPER', f"Guide command exception: {str(e)}")
            test_results['guide_command'] = {'passed': False, 'exception': str(e)}
        
        # Test 3: Validation command
        total_tests += 1
        test_message = "[EPIC-1] red: test: add login test [Task 1.1 | 30min]"
        try:
            result = subprocess.run([sys.executable, str(commit_helper_path), '--validate', test_message],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'Valid' in result.stdout:
                tests_passed += 1
                self.log_finding('SUCCESS', 'COMMIT_HELPER', "Validation command works")
                test_results['validation_command'] = {'passed': True}
            else:
                self.log_finding('WARNING', 'COMMIT_HELPER', "Validation command issues")
                test_results['validation_command'] = {'passed': False, 'stderr': result.stderr}
        except Exception as e:
            self.log_finding('WARNING', 'COMMIT_HELPER', f"Validation exception: {str(e)}")
            test_results['validation_command'] = {'passed': False, 'exception': str(e)}
        
        # Test 4: Quick commit (dry run)
        if self.full_test:
            total_tests += 1
            try:
                result = subprocess.run([
                    sys.executable, str(commit_helper_path), '--quick', '--no-commit',
                    '--epic', '1', '--phase', 'red', '--type', 'test',
                    '--desc', 'test commit message'
                ], capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    tests_passed += 1
                    self.log_finding('SUCCESS', 'COMMIT_HELPER', "Quick commit generation works")
                    test_results['quick_commit'] = {'passed': True}
                else:
                    self.log_finding('WARNING', 'COMMIT_HELPER', "Quick commit issues")
                    test_results['quick_commit'] = {'passed': False, 'stderr': result.stderr}
            except Exception as e:
                self.log_finding('WARNING', 'COMMIT_HELPER', f"Quick commit exception: {str(e)}")
                test_results['quick_commit'] = {'passed': False, 'exception': str(e)}
        
        commit_score = (tests_passed / total_tests) * 100 if total_tests > 0 else 0
        self.metrics['commit_helper_score'] = commit_score
        
        return {
            'score': commit_score,
            'tests_passed': tests_passed,
            'total_tests': total_tests,
            'test_results': test_results
        }
    
    def test_gantt_tracker_functionality(self) -> Dict[str, Any]:
        """Test TDD Gantt tracker functionality."""
        print("\n📊 TESTING GANTT TRACKER FUNCTIONALITY")
        print("=" * 50)
        
        gantt_path = self.project_root / 'scripts' / 'visualization' / 'tdd_gantt_tracker.py'
        
        if not gantt_path.exists():
            self.log_finding('ERROR', 'GANTT', "tdd_gantt_tracker.py not found")
            return {'score': 0, 'tests_passed': 0, 'total_tests': 0}
        
        test_results = {}
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Help command
        total_tests += 1
        try:
            result = subprocess.run([sys.executable, str(gantt_path), '--help'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'TDD' in result.stdout:
                tests_passed += 1
                self.log_finding('SUCCESS', 'GANTT', "Gantt help command works")
                test_results['help'] = {'passed': True}
            else:
                self.log_finding('WARNING', 'GANTT', 
                               f"Gantt help issues: {result.stderr}")
                test_results['help'] = {'passed': False, 'stderr': result.stderr}
        except Exception as e:
            self.log_finding('WARNING', 'GANTT', f"Gantt help exception: {str(e)}")
            test_results['help'] = {'passed': False, 'exception': str(e)}
        
        # Test 2: Import dependencies check
        total_tests += 1
        try:
            # Try to import key modules that the script needs
            plotly_available = self._check_module_import('plotly.graph_objects')
            pandas_available = self._check_module_import('pandas')
            
            if plotly_available and pandas_available:
                tests_passed += 1
                self.log_finding('SUCCESS', 'GANTT', "Required dependencies available")
                test_results['dependencies'] = {'passed': True, 'plotly': True, 'pandas': True}
            else:
                self.log_finding('WARNING', 'GANTT', 
                               f"Missing dependencies - plotly: {plotly_available}, pandas: {pandas_available}")
                test_results['dependencies'] = {'passed': False, 'plotly': plotly_available, 'pandas': pandas_available}
        except Exception as e:
            self.log_finding('WARNING', 'GANTT', f"Dependency check exception: {str(e)}")
            test_results['dependencies'] = {'passed': False, 'exception': str(e)}
        
        # Test 3: Text report generation (no dependencies needed)
        if self.full_test:
            total_tests += 1
            try:
                result = subprocess.run([sys.executable, str(gantt_path), '--report', '--output', '-'],
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    tests_passed += 1
                    self.log_finding('SUCCESS', 'GANTT', "Text report generation works")
                    test_results['text_report'] = {'passed': True, 'output_length': len(result.stdout)}
                else:
                    self.log_finding('WARNING', 'GANTT', "Text report generation issues")
                    test_results['text_report'] = {'passed': False, 'stderr': result.stderr}
            except Exception as e:
                self.log_finding('WARNING', 'GANTT', f"Text report exception: {str(e)}")
                test_results['text_report'] = {'passed': False, 'exception': str(e)}
        
        gantt_score = (tests_passed / total_tests) * 100 if total_tests > 0 else 0
        self.metrics['gantt_tracker_score'] = gantt_score
        
        return {
            'score': gantt_score,
            'tests_passed': tests_passed,
            'total_tests': total_tests,
            'test_results': test_results
        }
    
    def test_setup_validation(self) -> Dict[str, Any]:
        """Test setup validation script."""
        print("\n🔧 TESTING SETUP VALIDATION")
        print("=" * 50)
        
        setup_path = self.project_root / 'scripts' / 'test_setup.py'
        
        if not setup_path.exists():
            self.log_finding('ERROR', 'SETUP', "test_setup.py not found")
            return {'score': 0, 'tests_passed': 0, 'total_tests': 0}
        
        tests_passed = 0
        total_tests = 1
        
        try:
            result = subprocess.run([sys.executable, str(setup_path)],
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode in [0, 1]:  # 0 = perfect, 1 = some issues but functional
                tests_passed += 1
                self.log_finding('SUCCESS', 'SETUP', "Setup validation runs successfully")
                
                # Parse output for metrics
                output_lines = result.stdout.split('\n')
                overall_line = [line for line in output_lines if 'Overall:' in line]
                if overall_line:
                    # Extract success rate
                    match = re.search(r'(\d+)/(\d+) tests passed', overall_line[0])
                    if match:
                        passed, total = match.groups()
                        success_rate = (int(passed) / int(total)) * 100
                        self.log_finding('INFO', 'SETUP', 
                                       f"Setup validation success rate: {success_rate:.1f}%")
                
                return {
                    'score': 100,
                    'tests_passed': tests_passed,
                    'total_tests': total_tests,
                    'validation_output': result.stdout,
                    'exit_code': result.returncode
                }
            else:
                self.log_finding('ERROR', 'SETUP', f"Setup validation failed: {result.stderr}")
                return {
                    'score': 0,
                    'tests_passed': 0,
                    'total_tests': total_tests,
                    'error': result.stderr,
                    'exit_code': result.returncode
                }
                
        except Exception as e:
            self.log_finding('ERROR', 'SETUP', f"Setup validation exception: {str(e)}")
            return {
                'score': 0,
                'tests_passed': 0,
                'total_tests': total_tests,
                'exception': str(e)
            }
    
    def test_epic_json_validation(self) -> Dict[str, Any]:
        """Test Epic JSON files validation."""
        print("\n📋 TESTING EPIC JSON VALIDATION")
        print("=" * 50)
        
        epics_dir = self.project_root / 'epics'
        
        if not epics_dir.exists():
            self.log_finding('ERROR', 'EPICS', "epics directory not found")
            return {'score': 0, 'tests_passed': 0, 'total_tests': 0}
        
        json_files = list(epics_dir.glob('*.json'))
        if not json_files:
            self.log_finding('WARNING', 'EPICS', "No JSON files found in epics directory")
            return {'score': 50, 'tests_passed': 0, 'total_tests': 0}  # Partial score for having directory
        
        tests_passed = 0
        total_tests = len(json_files)
        epic_results = {}
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    epic_data = json.load(f)
                
                # Validate epic structure
                required_fields = ['epic_id', 'title', 'description', 'status', 'tasks']
                missing_fields = [field for field in required_fields if field not in epic_data]
                
                if not missing_fields:
                    tests_passed += 1
                    self.log_finding('SUCCESS', 'EPICS', f"Epic JSON valid: {json_file.name}")
                    
                    epic_results[json_file.name] = {
                        'valid': True,
                        'epic_id': epic_data.get('epic_id'),
                        'task_count': len(epic_data.get('tasks', [])),
                        'has_tdd_metrics': 'tdd_metrics' in epic_data
                    }
                else:
                    self.log_finding('WARNING', 'EPICS', 
                                   f"Epic JSON missing fields: {json_file.name}",
                                   {'missing_fields': missing_fields})
                    epic_results[json_file.name] = {
                        'valid': False,
                        'missing_fields': missing_fields
                    }
                    
            except json.JSONDecodeError as e:
                self.log_finding('ERROR', 'EPICS', f"Epic JSON syntax error: {json_file.name}",
                               {'error': str(e)})
                epic_results[json_file.name] = {'valid': False, 'json_error': str(e)}
            except Exception as e:
                self.log_finding('ERROR', 'EPICS', f"Epic JSON read error: {json_file.name}",
                               {'error': str(e)})
                epic_results[json_file.name] = {'valid': False, 'read_error': str(e)}
        
        epic_score = (tests_passed / total_tests) * 100 if total_tests > 0 else 100
        self.metrics['epic_json_score'] = epic_score
        
        return {
            'score': epic_score,
            'tests_passed': tests_passed,
            'total_tests': total_tests,
            'epic_files': list(epic_results.keys()),
            'results': epic_results
        }
    
    def test_jekyll_configuration(self) -> Dict[str, Any]:
        """Test Jekyll configuration and files."""
        print("\n📖 TESTING JEKYLL CONFIGURATION")
        print("=" * 50)
        
        docs_dir = self.project_root / 'docs'
        
        if not docs_dir.exists():
            self.log_finding('ERROR', 'JEKYLL', "docs directory not found")
            return {'score': 0, 'tests_passed': 0, 'total_tests': 0}
        
        tests_passed = 0
        total_tests = 0
        jekyll_results = {}
        
        # Test 1: _config.yml validation
        total_tests += 1
        config_path = docs_dir / '_config.yml'
        if config_path.exists():
            try:
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                required_keys = ['title', 'description']
                if all(key in config for key in required_keys):
                    tests_passed += 1
                    self.log_finding('SUCCESS', 'JEKYLL', "_config.yml is valid")
                    jekyll_results['config'] = {'valid': True, 'keys': list(config.keys())}
                else:
                    self.log_finding('WARNING', 'JEKYLL', "_config.yml missing required keys")
                    jekyll_results['config'] = {'valid': False, 'missing_keys': required_keys}
            except Exception as e:
                self.log_finding('ERROR', 'JEKYLL', f"_config.yml error: {str(e)}")
                jekyll_results['config'] = {'valid': False, 'error': str(e)}
        else:
            self.log_finding('ERROR', 'JEKYLL', "_config.yml not found")
            jekyll_results['config'] = {'valid': False, 'missing': True}
        
        # Test 2: Gemfile validation
        total_tests += 1
        gemfile_path = docs_dir / 'Gemfile'
        if gemfile_path.exists():
            content = gemfile_path.read_text()
            if 'github-pages' in content and 'jekyll' in content:
                tests_passed += 1
                self.log_finding('SUCCESS', 'JEKYLL', "Gemfile is properly configured")
                jekyll_results['gemfile'] = {'valid': True, 'has_github_pages': True}
            else:
                self.log_finding('WARNING', 'JEKYLL', "Gemfile missing required gems")
                jekyll_results['gemfile'] = {'valid': False, 'missing_gems': True}
        else:
            self.log_finding('ERROR', 'JEKYLL', "Gemfile not found")
            jekyll_results['gemfile'] = {'valid': False, 'missing': True}
        
        # Test 3: Essential markdown files
        total_tests += 1
        index_path = docs_dir / 'index.md'
        if index_path.exists() and index_path.stat().st_size > 1000:  # Should be substantial
            tests_passed += 1
            self.log_finding('SUCCESS', 'JEKYLL', "index.md exists and has good content")
            jekyll_results['index'] = {'valid': True, 'size': index_path.stat().st_size}
        else:
            self.log_finding('WARNING', 'JEKYLL', "index.md missing or too short")
            jekyll_results['index'] = {'valid': False}
        
        # Test 4: HTML dashboard
        total_tests += 1
        dashboard_path = docs_dir / 'dashboard.html'
        if dashboard_path.exists():
            content = dashboard_path.read_text()
            if 'TDD' in content and 'plotly' in content.lower():
                tests_passed += 1
                self.log_finding('SUCCESS', 'JEKYLL', "dashboard.html is properly configured")
                jekyll_results['dashboard'] = {'valid': True, 'has_plotly': True}
            else:
                self.log_finding('WARNING', 'JEKYLL', "dashboard.html missing key features")
                jekyll_results['dashboard'] = {'valid': False}
        else:
            self.log_finding('WARNING', 'JEKYLL', "dashboard.html not found")
            jekyll_results['dashboard'] = {'valid': False, 'missing': True}
        
        jekyll_score = (tests_passed / total_tests) * 100 if total_tests > 0 else 0
        self.metrics['jekyll_score'] = jekyll_score
        
        return {
            'score': jekyll_score,
            'tests_passed': tests_passed,
            'total_tests': total_tests,
            'results': jekyll_results
        }
    
    def test_github_workflow(self) -> Dict[str, Any]:
        """Test GitHub Actions workflow configuration."""
        print("\n🤖 TESTING GITHUB WORKFLOW")
        print("=" * 50)
        
        workflow_path = self.project_root / '.github' / 'workflows' / 'update-tdd-gantt.yml'
        
        if not workflow_path.exists():
            self.log_finding('ERROR', 'WORKFLOW', "GitHub workflow file not found")
            return {'score': 0, 'tests_passed': 0, 'total_tests': 0}
        
        tests_passed = 0
        total_tests = 0
        workflow_results = {}
        
        try:
            import yaml
            with open(workflow_path, 'r') as f:
                workflow = yaml.safe_load(f)
            
            # Test 1: Basic structure
            total_tests += 1
            if all(key in workflow for key in ['name', 'on', 'jobs']):
                tests_passed += 1
                self.log_finding('SUCCESS', 'WORKFLOW', "Workflow has basic structure")
                workflow_results['structure'] = {'valid': True}
            else:
                self.log_finding('ERROR', 'WORKFLOW', "Workflow missing basic structure")
                workflow_results['structure'] = {'valid': False}
            
            # Test 2: Triggers configuration
            total_tests += 1
            triggers = workflow.get('on', {})
            if isinstance(triggers, dict) and any(key in triggers for key in ['push', 'workflow_dispatch']):
                tests_passed += 1
                self.log_finding('SUCCESS', 'WORKFLOW', "Workflow has proper triggers")
                workflow_results['triggers'] = {'valid': True, 'triggers': list(triggers.keys())}
            else:
                self.log_finding('WARNING', 'WORKFLOW', "Workflow triggers might be incomplete")
                workflow_results['triggers'] = {'valid': False}
            
            # Test 3: Jobs configuration
            total_tests += 1
            jobs = workflow.get('jobs', {})
            if jobs and isinstance(jobs, dict):
                job_names = list(jobs.keys())
                if any('tdd' in name.lower() for name in job_names):
                    tests_passed += 1
                    self.log_finding('SUCCESS', 'WORKFLOW', f"Workflow has TDD job: {job_names}")
                    workflow_results['jobs'] = {'valid': True, 'job_names': job_names}
                else:
                    self.log_finding('WARNING', 'WORKFLOW', f"Workflow jobs might not be TDD-specific: {job_names}")
                    workflow_results['jobs'] = {'valid': False, 'job_names': job_names}
            else:
                self.log_finding('ERROR', 'WORKFLOW', "Workflow has no jobs")
                workflow_results['jobs'] = {'valid': False}
                
            # Test 4: Steps validation
            total_tests += 1
            first_job = list(jobs.values())[0] if jobs else {}
            steps = first_job.get('steps', [])
            if len(steps) >= 5:  # Should have multiple meaningful steps
                tests_passed += 1
                self.log_finding('SUCCESS', 'WORKFLOW', f"Workflow has {len(steps)} steps")
                workflow_results['steps'] = {'valid': True, 'count': len(steps)}
            else:
                self.log_finding('WARNING', 'WORKFLOW', f"Workflow has only {len(steps)} steps")
                workflow_results['steps'] = {'valid': False, 'count': len(steps)}
                
        except yaml.YAMLError as e:
            self.log_finding('ERROR', 'WORKFLOW', f"Workflow YAML syntax error: {str(e)}")
            workflow_results['yaml_error'] = str(e)
        except Exception as e:
            self.log_finding('ERROR', 'WORKFLOW', f"Workflow validation error: {str(e)}")
            workflow_results['error'] = str(e)
        
        workflow_score = (tests_passed / total_tests) * 100 if total_tests > 0 else 0
        self.metrics['workflow_score'] = workflow_score
        
        return {
            'score': workflow_score,
            'tests_passed': tests_passed,
            'total_tests': total_tests,
            'results': workflow_results
        }
    
    def _check_module_import(self, module_name: str) -> bool:
        """Check if a Python module can be imported."""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False
    
    def generate_functionality_report(self) -> Dict[str, Any]:
        """Generate comprehensive functionality audit report."""
        print("\n📊 GENERATING FUNCTIONALITY REPORT")
        print("=" * 50)
        
        # Calculate overall score
        scores = [v for k, v in self.metrics.items() if k.endswith('_score')]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Categorize findings
        critical_issues = [f for f in self.findings if f['level'] == 'CRITICAL']
        errors = [f for f in self.findings if f['level'] == 'ERROR']
        warnings = [f for f in self.findings if f['level'] == 'WARNING']
        successes = [f for f in self.findings if f['level'] == 'SUCCESS']
        
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'overall_score': round(overall_score, 2),
            'grade': self._calculate_grade(overall_score),
            'metrics': self.metrics,
            'summary': {
                'total_findings': len(self.findings),
                'critical_issues': len(critical_issues),
                'errors': len(errors),
                'warnings': len(warnings),
                'successes': len(successes)
            },
            'findings': self.findings,
            'test_results': self.test_results,
            'recommendations': self._generate_recommendations()
        }
        
        # Console summary
        grade_colors = {
            'A+': '🟢', 'A': '🟢', 'B+': '🔵', 'B': '🔵', 
            'C+': '🟡', 'C': '🟡', 'D': '🟠', 'F': '🔴'
        }
        grade_color = grade_colors.get(report['grade'], '⚪')
        
        print(f"\n{grade_color} OVERALL FUNCTIONALITY GRADE: {report['grade']} ({overall_score:.1f}%)")
        print(f"📊 Total Findings: {len(self.findings)}")
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
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on findings."""
        recommendations = []
        
        errors = [f for f in self.findings if f['level'] == 'ERROR']
        if errors:
            recommendations.append("🔥 CRITICAL: Fix ERROR level issues - core functionality broken")
        
        if self.metrics.get('python_syntax_score', 100) < 100:
            recommendations.append("🐍 HIGH: Fix Python syntax errors immediately")
        
        if self.metrics.get('commit_helper_score', 0) < 75:
            recommendations.append("🧪 HIGH: Improve commit helper functionality for TDD workflow")
        
        if self.metrics.get('jekyll_score', 0) < 80:
            recommendations.append("📖 MEDIUM: Complete Jekyll configuration for GitHub Pages")
        
        if self.metrics.get('workflow_score', 0) < 70:
            recommendations.append("🤖 MEDIUM: Fix GitHub Actions workflow configuration")
        
        if not recommendations:
            recommendations.append("🎉 Excellent! All core functionality is working properly")
        
        return recommendations


def main():
    """Main functionality audit execution."""
    parser = argparse.ArgumentParser(description="⚙️ TDD Template Functionality Audit")
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output with detailed findings')
    parser.add_argument('--full-test', action='store_true',
                       help='Run comprehensive tests (slower but more thorough)')
    parser.add_argument('--report', choices=['console', 'json', 'both'], 
                       default='console', help='Report output format')
    parser.add_argument('--output', '-o', help='Output file for JSON report')
    
    args = parser.parse_args()
    
    print("⚙️ TDD PROJECT TEMPLATE - FUNCTIONALITY AUDIT")
    print("=" * 60)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Project: {Path.cwd()}")
    print(f"🔍 Full Test Mode: {'YES' if args.full_test else 'NO'}")
    
    auditor = FunctionalityAuditor(verbose=args.verbose, full_test=args.full_test)
    
    try:
        # Run all functionality tests
        syntax_results = auditor.test_python_scripts_syntax()
        commit_results = auditor.test_commit_helper_functionality()
        gantt_results = auditor.test_gantt_tracker_functionality()
        setup_results = auditor.test_setup_validation()
        epic_results = auditor.test_epic_json_validation()
        jekyll_results = auditor.test_jekyll_configuration()
        workflow_results = auditor.test_github_workflow()
        
        # Generate final report
        report = auditor.generate_functionality_report()
        
        # Output report
        if args.report in ['json', 'both']:
            output_file = args.output or f'functionality_audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 JSON report saved: {output_file}")
        
        # Return exit code based on grade
        grade_scores = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C+': 1, 'C': 1, 'D': 2, 'F': 3}
        return grade_scores.get(report['grade'], 3)
        
    except KeyboardInterrupt:
        print("\n❌ Functionality audit cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Functionality audit failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())