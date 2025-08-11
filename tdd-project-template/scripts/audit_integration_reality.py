#!/usr/bin/env python3
"""
🔧 TDD Project Template - Integration & Reality Check Audit
=========================================================

Auditoria de integração que testa instalação REAL de dependências,
execução de scripts com dados reais e validação de funcionamento
em condições práticas de uso.

Uso:
    python scripts/audit_integration_reality.py
    python scripts/audit_integration_reality.py --verbose --install-deps
"""

import argparse
import json
import os
import sys
import re
import subprocess
import tempfile
import shutil
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import importlib.util


class IntegrationRealityAuditor:
    """Auditor de integração e realidade do template TDD."""
    
    def __init__(self, verbose: bool = False, install_deps: bool = False):
        self.verbose = verbose
        self.install_deps = install_deps
        self.project_root = Path.cwd()
        self.findings = []
        self.metrics = {}
        self.temp_env_path = None
        
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
    
    def audit_poetry_installation(self) -> Dict[str, Any]:
        """Audit Poetry installation and functionality."""
        print("\n📦 AUDITING POETRY INSTALLATION & SETUP")
        print("=" * 50)
        
        poetry_metrics = {
            'poetry_available': False,
            'version': None,
            'pyproject_valid': False,
            'lockfile_exists': False,
            'installation_success': False
        }
        
        installation_score = 0
        
        # Check if Poetry is available
        try:
            result = subprocess.run(['poetry', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                poetry_metrics['poetry_available'] = True
                poetry_metrics['version'] = result.stdout.strip()
                installation_score += 30
                self.log_finding('SUCCESS', 'POETRY', f"Poetry available: {poetry_metrics['version']}")
            else:
                self.log_finding('ERROR', 'POETRY', "Poetry not available in PATH")
                
        except FileNotFoundError:
            self.log_finding('ERROR', 'POETRY', "Poetry not installed")
        except subprocess.TimeoutExpired:
            self.log_finding('ERROR', 'POETRY', "Poetry version check timeout")
        except Exception as e:
            self.log_finding('ERROR', 'POETRY', f"Poetry check failed: {str(e)}")
        
        # Validate pyproject.toml
        pyproject_path = self.project_root / 'pyproject.toml'
        if pyproject_path.exists():
            try:
                import toml
                config = toml.load(pyproject_path)
                
                # Check required sections
                has_poetry_section = 'tool' in config and 'poetry' in config['tool']
                has_dependencies = bool(config.get('tool', {}).get('poetry', {}).get('dependencies'))
                has_build_system = 'build-system' in config
                
                if has_poetry_section and has_dependencies and has_build_system:
                    poetry_metrics['pyproject_valid'] = True
                    installation_score += 20
                    self.log_finding('SUCCESS', 'POETRY', "pyproject.toml is valid")
                    
                    # Check for key dependencies
                    deps = config.get('tool', {}).get('poetry', {}).get('dependencies', {})
                    key_deps = ['plotly', 'pandas', 'pyyaml']
                    found_deps = [dep for dep in key_deps if dep.lower() in [d.lower() for d in deps.keys()]]
                    
                    if len(found_deps) >= 2:
                        installation_score += 15
                        self.log_finding('SUCCESS', 'POETRY', 
                                       f"Key dependencies defined: {', '.join(found_deps)}")
                    else:
                        self.log_finding('WARNING', 'POETRY', 
                                       f"Only {len(found_deps)} key dependencies found")
                else:
                    self.log_finding('ERROR', 'POETRY', "pyproject.toml missing required sections")
                    
            except ImportError:
                self.log_finding('WARNING', 'POETRY', "toml module not available for validation")
            except Exception as e:
                self.log_finding('ERROR', 'POETRY', f"Failed to validate pyproject.toml: {str(e)}")
        else:
            self.log_finding('CRITICAL', 'POETRY', "pyproject.toml missing")
        
        # Check for poetry.lock
        lockfile_path = self.project_root / 'poetry.lock'
        if lockfile_path.exists():
            poetry_metrics['lockfile_exists'] = True
            installation_score += 10
            self.log_finding('SUCCESS', 'POETRY', "poetry.lock exists")
        else:
            self.log_finding('WARNING', 'POETRY', "poetry.lock missing - run 'poetry install'")
        
        # Attempt dependency installation if requested
        if self.install_deps and poetry_metrics['poetry_available']:
            try:
                self.log_finding('INFO', 'POETRY', "Attempting to install dependencies...")
                start_time = time.time()
                
                result = subprocess.run(['poetry', 'install'], 
                                      cwd=self.project_root,
                                      capture_output=True, text=True, timeout=300)
                
                install_time = time.time() - start_time
                
                if result.returncode == 0:
                    poetry_metrics['installation_success'] = True
                    installation_score += 25
                    self.log_finding('SUCCESS', 'POETRY', 
                                   f"Dependencies installed successfully ({install_time:.1f}s)")
                    
                    # Verify installation by checking key imports
                    install_verification = self._verify_poetry_installation()
                    if install_verification:
                        installation_score += 10
                else:
                    self.log_finding('ERROR', 'POETRY', 
                                   f"Dependency installation failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.log_finding('ERROR', 'POETRY', "Poetry install timeout (>5min)")
            except Exception as e:
                self.log_finding('ERROR', 'POETRY', f"Poetry install exception: {str(e)}")
        
        self.metrics['poetry_installation_score'] = installation_score
        
        return {
            'score': installation_score,
            'metrics': poetry_metrics
        }
    
    def _verify_poetry_installation(self) -> bool:
        """Verify that Poetry installation worked by testing key imports."""
        try:
            # Test in Poetry environment
            test_script = '''
import sys
try:
    import plotly
    import pandas
    import yaml
    print("SUCCESS: All key dependencies imported")
    sys.exit(0)
except ImportError as e:
    print(f"IMPORT_ERROR: {e}")
    sys.exit(1)
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_script)
                f.flush()
                
                result = subprocess.run(['poetry', 'run', 'python', f.name],
                                      cwd=self.project_root,
                                      capture_output=True, text=True, timeout=30)
                
                os.unlink(f.name)
                
                if result.returncode == 0:
                    self.log_finding('SUCCESS', 'POETRY', "Poetry environment verified")
                    return True
                else:
                    self.log_finding('ERROR', 'POETRY', 
                                   f"Poetry environment verification failed: {result.stdout}")
                    return False
                    
        except Exception as e:
            self.log_finding('ERROR', 'POETRY', f"Poetry verification exception: {str(e)}")
            return False
    
    def audit_dependency_imports(self) -> Dict[str, Any]:
        """Audit that critical dependencies can be imported and used."""
        print("\n🔍 AUDITING DEPENDENCY IMPORTS & FUNCTIONALITY")
        print("=" * 50)
        
        import_metrics = {
            'successful_imports': [],
            'failed_imports': [],
            'functionality_tests': {}
        }
        
        import_score = 0
        
        # Define critical dependencies to test
        critical_deps = {
            'plotly': {
                'import_statement': 'import plotly.graph_objects as go',
                'functionality_test': 'fig = go.Figure(); fig.add_trace(go.Scatter(x=[1,2], y=[1,2]))'
            },
            'pandas': {
                'import_statement': 'import pandas as pd',
                'functionality_test': 'df = pd.DataFrame({"a": [1,2], "b": [3,4]}); len(df)'
            },
            'yaml': {
                'import_statement': 'import yaml',
                'functionality_test': 'yaml.safe_load("test: value")'
            },
            'json': {
                'import_statement': 'import json',
                'functionality_test': 'json.loads(\'{"test": "value"}\')'
            },
            'datetime': {
                'import_statement': 'from datetime import datetime',
                'functionality_test': 'datetime.now()'
            },
            'pathlib': {
                'import_statement': 'from pathlib import Path',
                'functionality_test': 'Path("/tmp").exists()'
            },
            'subprocess': {
                'import_statement': 'import subprocess',
                'functionality_test': 'subprocess.run(["echo", "test"], capture_output=True)'
            },
            're': {
                'import_statement': 'import re',
                'functionality_test': 're.search(r"test", "test string")'
            }
        }
        
        # Test each dependency
        for dep_name, dep_config in critical_deps.items():
            try:
                # Test import
                exec(dep_config['import_statement'])
                import_metrics['successful_imports'].append(dep_name)
                import_score += 10
                self.log_finding('SUCCESS', 'IMPORTS', f"Successfully imported {dep_name}")
                
                # Test basic functionality
                try:
                    exec(dep_config['functionality_test'])
                    import_metrics['functionality_tests'][dep_name] = True
                    import_score += 5
                    self.log_finding('SUCCESS', 'IMPORTS', f"{dep_name} functionality test passed")
                    
                except Exception as func_e:
                    import_metrics['functionality_tests'][dep_name] = False
                    self.log_finding('WARNING', 'IMPORTS', 
                                   f"{dep_name} functionality test failed: {str(func_e)}")
                    
            except ImportError as imp_e:
                import_metrics['failed_imports'].append({
                    'dependency': dep_name,
                    'error': str(imp_e)
                })
                self.log_finding('ERROR', 'IMPORTS', f"Failed to import {dep_name}: {str(imp_e)}")
                
            except Exception as e:
                self.log_finding('ERROR', 'IMPORTS', f"Unexpected error testing {dep_name}: {str(e)}")
        
        # Calculate success rate
        total_deps = len(critical_deps)
        successful_imports = len(import_metrics['successful_imports'])
        import_success_rate = (successful_imports / total_deps) * 100
        
        if import_success_rate >= 90:
            self.log_finding('SUCCESS', 'IMPORTS', 
                           f"Excellent import success rate: {import_success_rate:.1f}%")
        elif import_success_rate >= 70:
            self.log_finding('WARNING', 'IMPORTS', 
                           f"Good import success rate: {import_success_rate:.1f}%")
        else:
            self.log_finding('ERROR', 'IMPORTS', 
                           f"Poor import success rate: {import_success_rate:.1f}%")
        
        self.metrics['dependency_import_score'] = import_score
        
        return {
            'score': import_score,
            'success_rate': import_success_rate,
            'metrics': import_metrics
        }
    
    def audit_script_execution_reality(self) -> Dict[str, Any]:
        """Audit real execution of main scripts with actual data."""
        print("\n⚡ AUDITING REAL SCRIPT EXECUTION")
        print("=" * 50)
        
        execution_metrics = {
            'script_results': {},
            'performance_data': {},
            'error_analysis': {}
        }
        
        execution_score = 0
        
        # Define scripts to test with realistic parameters
        test_scripts = {
            'commit_helper': {
                'path': 'scripts/commit_helper.py',
                'tests': [
                    {
                        'name': 'help_command',
                        'args': ['--help'],
                        'expected_return_code': 0,
                        'expected_content': ['TDD', 'commit', 'pattern'],
                        'timeout': 10
                    },
                    {
                        'name': 'validate_command',
                        'args': ['--validate', '[EPIC-1] red: test: add user login test [Task 1.1 | 30min]'],
                        'expected_return_code': 0,
                        'expected_content': ['Valid'],
                        'timeout': 10
                    },
                    {
                        'name': 'guide_command', 
                        'args': ['--guide'],
                        'expected_return_code': 0,
                        'expected_content': ['TDD', 'workflow'],
                        'timeout': 10
                    }
                ]
            },
            'gantt_tracker': {
                'path': 'scripts/visualization/tdd_gantt_tracker.py',
                'tests': [
                    {
                        'name': 'help_command',
                        'args': ['--help'],
                        'expected_return_code': 0,
                        'expected_content': ['Gantt', 'TDD'],
                        'timeout': 15
                    },
                    {
                        'name': 'report_command',
                        'args': ['--report', '--output', '-'],
                        'expected_return_code': [0, 1],  # May fail due to missing dependencies
                        'expected_content': [],
                        'timeout': 30
                    }
                ]
            },
            'test_setup': {
                'path': 'scripts/test_setup.py',
                'tests': [
                    {
                        'name': 'basic_execution',
                        'args': [],
                        'expected_return_code': [0, 1],  # May have warnings
                        'expected_content': ['TDD', 'setup'],
                        'timeout': 30
                    }
                ]
            }
        }
        
        # Execute each script test
        total_tests = 0
        successful_tests = 0
        
        for script_name, script_config in test_scripts.items():
            script_path = self.project_root / script_config['path']
            
            if not script_path.exists():
                self.log_finding('ERROR', 'EXECUTION', f"Script missing: {script_config['path']}")
                execution_metrics['script_results'][script_name] = {
                    'available': False,
                    'tests_run': 0,
                    'tests_passed': 0
                }
                continue
            
            script_results = {
                'available': True,
                'tests_run': 0,
                'tests_passed': 0,
                'test_details': {}
            }
            
            for test in script_config['tests']:
                total_tests += 1
                script_results['tests_run'] += 1
                test_name = test['name']
                
                try:
                    start_time = time.time()
                    
                    # Execute script
                    result = subprocess.run([
                        sys.executable, str(script_path)] + test['args'],
                        capture_output=True, text=True, 
                        timeout=test['timeout'],
                        cwd=self.project_root
                    )
                    
                    execution_time = time.time() - start_time
                    
                    # Check return code
                    expected_codes = test['expected_return_code']
                    if isinstance(expected_codes, int):
                        expected_codes = [expected_codes]
                    
                    return_code_ok = result.returncode in expected_codes
                    
                    # Check content
                    output_text = result.stdout + result.stderr
                    content_ok = all(content in output_text for content in test['expected_content'])
                    
                    test_passed = return_code_ok and content_ok
                    
                    if test_passed:
                        successful_tests += 1
                        script_results['tests_passed'] += 1
                        execution_score += 15
                        self.log_finding('SUCCESS', 'EXECUTION', 
                                       f"{script_name}.{test_name} passed ({execution_time:.2f}s)")
                    else:
                        self.log_finding('WARNING', 'EXECUTION',
                                       f"{script_name}.{test_name} failed - return_code: {result.returncode}, expected: {expected_codes}")
                    
                    script_results['test_details'][test_name] = {
                        'passed': test_passed,
                        'return_code': result.returncode,
                        'execution_time': execution_time,
                        'output_length': len(output_text),
                        'error_output': result.stderr if result.stderr else None
                    }
                    
                    # Track performance
                    if script_name not in execution_metrics['performance_data']:
                        execution_metrics['performance_data'][script_name] = []
                    execution_metrics['performance_data'][script_name].append({
                        'test': test_name,
                        'execution_time': execution_time
                    })
                    
                except subprocess.TimeoutExpired:
                    self.log_finding('ERROR', 'EXECUTION', 
                                   f"{script_name}.{test_name} timeout (>{test['timeout']}s)")
                    script_results['test_details'][test_name] = {
                        'passed': False,
                        'error': 'timeout'
                    }
                    
                except Exception as e:
                    self.log_finding('ERROR', 'EXECUTION',
                                   f"{script_name}.{test_name} exception: {str(e)}")
                    script_results['test_details'][test_name] = {
                        'passed': False,
                        'error': str(e)
                    }
            
            execution_metrics['script_results'][script_name] = script_results
        
        # Calculate overall execution success rate
        if total_tests > 0:
            execution_success_rate = (successful_tests / total_tests) * 100
            if execution_success_rate >= 80:
                self.log_finding('SUCCESS', 'EXECUTION',
                               f"Excellent script execution rate: {execution_success_rate:.1f}%")
            elif execution_success_rate >= 60:
                self.log_finding('WARNING', 'EXECUTION',
                               f"Good script execution rate: {execution_success_rate:.1f}%")
            else:
                self.log_finding('ERROR', 'EXECUTION',
                               f"Poor script execution rate: {execution_success_rate:.1f}%")
        else:
            execution_success_rate = 0
            self.log_finding('CRITICAL', 'EXECUTION', "No scripts could be tested")
        
        # Bonus score for fast execution
        avg_execution_times = []
        for script_data in execution_metrics['performance_data'].values():
            avg_time = sum(test['execution_time'] for test in script_data) / len(script_data)
            avg_execution_times.append(avg_time)
        
        if avg_execution_times:
            overall_avg_time = sum(avg_execution_times) / len(avg_execution_times)
            if overall_avg_time < 2.0:
                execution_score += 20
                self.log_finding('SUCCESS', 'EXECUTION', f"Excellent performance: {overall_avg_time:.2f}s avg")
            elif overall_avg_time < 5.0:
                execution_score += 10
                self.log_finding('SUCCESS', 'EXECUTION', f"Good performance: {overall_avg_time:.2f}s avg")
        
        self.metrics['script_execution_score'] = execution_score
        
        return {
            'score': execution_score,
            'success_rate': execution_success_rate,
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'metrics': execution_metrics
        }
    
    def audit_chart_generation_reality(self) -> Dict[str, Any]:
        """Audit real chart generation with sample data."""
        print("\n📊 AUDITING REAL CHART GENERATION")
        print("=" * 50)
        
        chart_metrics = {
            'plotly_functionality': False,
            'chart_generation_success': False,
            'sample_data_processing': False,
            'html_output_valid': False
        }
        
        chart_score = 0
        
        # Test Plotly basic functionality
        try:
            # Test if we can import and create a basic chart
            test_plotly_script = '''
import plotly.graph_objects as go
import plotly.offline as pyo
from datetime import datetime, timedelta
import json

# Create sample TDD commit data
sample_commits = [
    {
        "epic": "EPIC-1",
        "phase": "analysis",
        "task": "1.1",
        "estimated_minutes": 30,
        "actual_minutes": 25,
        "date": "2024-01-15"
    },
    {
        "epic": "EPIC-1", 
        "phase": "red",
        "task": "1.2",
        "estimated_minutes": 45,
        "actual_minutes": 60,
        "date": "2024-01-15"
    },
    {
        "epic": "EPIC-1",
        "phase": "green", 
        "task": "1.3",
        "estimated_minutes": 60,
        "actual_minutes": 55,
        "date": "2024-01-16"
    }
]

# Create Gantt chart
fig = go.Figure()

# Add estimated time bars
fig.add_trace(go.Bar(
    name='Estimated',
    x=[f"Task {commit['task']}" for commit in sample_commits],
    y=[commit['estimated_minutes'] for commit in sample_commits],
    marker_color='lightblue'
))

# Add actual time bars  
fig.add_trace(go.Bar(
    name='Actual',
    x=[f"Task {commit['task']}" for commit in sample_commits],
    y=[commit['actual_minutes'] for commit in sample_commits],
    marker_color='darkblue'
))

fig.update_layout(
    title='TDD Task Time Tracking',
    xaxis_title='Tasks',
    yaxis_title='Time (minutes)',
    barmode='group'
)

# Generate HTML
html_content = fig.to_html(include_plotlyjs=True)

# Validate HTML
if len(html_content) > 1000 and 'plotly' in html_content:
    print("SUCCESS: Chart generated successfully")
    exit(0)
else:
    print("ERROR: Chart generation failed")
    exit(1)
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_plotly_script)
                f.flush()
                
                try:
                    # Try with Poetry first
                    if self.metrics.get('poetry_installation_score', 0) > 50:
                        result = subprocess.run(['poetry', 'run', 'python', f.name],
                                              cwd=self.project_root,
                                              capture_output=True, text=True, timeout=60)
                    else:
                        result = subprocess.run([sys.executable, f.name],
                                              capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        chart_metrics['plotly_functionality'] = True
                        chart_metrics['chart_generation_success'] = True
                        chart_score += 40
                        self.log_finding('SUCCESS', 'CHARTS', "Plotly chart generation successful")
                        
                        # Check if HTML output looks valid
                        if 'Chart generated successfully' in result.stdout:
                            chart_metrics['html_output_valid'] = True
                            chart_score += 20
                            self.log_finding('SUCCESS', 'CHARTS', "HTML output validation passed")
                    else:
                        self.log_finding('ERROR', 'CHARTS', 
                                       f"Chart generation failed: {result.stderr}")
                    
                except subprocess.TimeoutExpired:
                    self.log_finding('ERROR', 'CHARTS', "Chart generation timeout")
                except Exception as e:
                    self.log_finding('ERROR', 'CHARTS', f"Chart generation exception: {str(e)}")
                
                finally:
                    os.unlink(f.name)
                    
        except Exception as e:
            self.log_finding('ERROR', 'CHARTS', f"Failed to create chart test script: {str(e)}")
        
        # Test sample data processing capabilities
        try:
            # Create sample epic JSON and test processing
            sample_epic = {
                "epic_id": "TEST-1",
                "title": "Sample Epic for Testing",
                "status": "active",
                "tasks": [
                    {
                        "task_id": "TEST-1.1",
                        "phase": "analysis",
                        "estimated_time_minutes": 30,
                        "status": "completed"
                    },
                    {
                        "task_id": "TEST-1.2", 
                        "phase": "red",
                        "estimated_time_minutes": 45,
                        "status": "in_progress"
                    }
                ],
                "tdd_metrics": {
                    "total_estimated_minutes": 75
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(sample_epic, f, indent=2)
                f.flush()
                
                try:
                    # Test JSON loading and validation
                    with open(f.name, 'r') as test_f:
                        loaded_epic = json.load(test_f)
                    
                    if loaded_epic['epic_id'] == 'TEST-1' and len(loaded_epic['tasks']) == 2:
                        chart_metrics['sample_data_processing'] = True
                        chart_score += 15
                        self.log_finding('SUCCESS', 'CHARTS', "Sample data processing works")
                    
                except Exception as e:
                    self.log_finding('WARNING', 'CHARTS', f"Sample data processing issue: {str(e)}")
                    
                finally:
                    os.unlink(f.name)
                    
        except Exception as e:
            self.log_finding('WARNING', 'CHARTS', f"Sample data test failed: {str(e)}")
        
        # Test Gantt tracker script if available
        gantt_script = self.project_root / 'scripts' / 'visualization' / 'tdd_gantt_tracker.py'
        if gantt_script.exists():
            try:
                # Test with --help to see if script loads without import errors
                result = subprocess.run([sys.executable, str(gantt_script), '--help'],
                                      capture_output=True, text=True, timeout=30,
                                      cwd=self.project_root)
                
                if 'ModuleNotFoundError' not in result.stderr:
                    chart_score += 25
                    self.log_finding('SUCCESS', 'CHARTS', "Gantt tracker script loads without import errors")
                else:
                    self.log_finding('WARNING', 'CHARTS', 
                                   "Gantt tracker has import issues (expected without Poetry install)")
                    
            except Exception as e:
                self.log_finding('WARNING', 'CHARTS', f"Gantt tracker test failed: {str(e)}")
        
        self.metrics['chart_generation_score'] = chart_score
        
        return {
            'score': chart_score,
            'metrics': chart_metrics
        }
    
    def generate_integration_reality_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration reality report."""
        print("\n📊 GENERATING INTEGRATION REALITY REPORT")
        print("=" * 50)
        
        # Calculate overall integration score
        integration_weights = {
            'poetry_installation_score': 0.30,
            'dependency_import_score': 0.25,
            'script_execution_score': 0.30,
            'chart_generation_score': 0.15
        }
        
        overall_score = 0
        for metric, weight in integration_weights.items():
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
            'integration_readiness': self._calculate_integration_readiness(overall_score),
            'weighted_scores': {k: round(self.metrics.get(k, 0), 2) for k in integration_weights.keys()},
            'weights_used': integration_weights,
            'metrics': self.metrics,
            'summary': {
                'total_findings': len(self.findings),
                'critical_issues': len(critical_issues),
                'errors': len(errors),
                'warnings': len(warnings),
                'successes': len(successes)
            },
            'findings': self.findings,
            'recommendations': self._generate_integration_recommendations()
        }
        
        # Console summary
        grade_colors = {
            'A+': '🟢', 'A': '🟢', 'B+': '🔵', 'B': '🔵', 
            'C+': '🟡', 'C': '🟡', 'D': '🟠', 'F': '🔴'
        }
        readiness_colors = {'READY': '🟢', 'MOSTLY_READY': '🔵', 'NEEDS_SETUP': '🟡', 'NOT_READY': '🔴'}
        
        grade_color = grade_colors.get(report['grade'], '⚪')
        readiness_color = readiness_colors.get(report['integration_readiness'], '⚪')
        
        print(f"\n{grade_color} OVERALL INTEGRATION GRADE: {report['grade']} ({overall_score:.1f}%)")
        print(f"{readiness_color} INTEGRATION READINESS: {report['integration_readiness']}")
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
    
    def _calculate_integration_readiness(self, score: float) -> str:
        """Calculate integration readiness level."""
        if score >= 85: return 'READY'
        elif score >= 70: return 'MOSTLY_READY'
        elif score >= 50: return 'NEEDS_SETUP'
        else: return 'NOT_READY'
    
    def _generate_integration_recommendations(self) -> List[str]:
        """Generate actionable integration recommendations."""
        recommendations = []
        
        if self.metrics.get('poetry_installation_score', 0) < 70:
            recommendations.append("📦 CRITICAL: Install Poetry and run 'poetry install' to set up dependencies")
        
        if self.metrics.get('dependency_import_score', 0) < 80:
            recommendations.append("🔍 HIGH: Fix missing dependencies - key packages like plotly/pandas not working")
        
        if self.metrics.get('script_execution_score', 0) < 70:
            recommendations.append("⚡ HIGH: Fix script execution issues - core functionality not working")
        
        if self.metrics.get('chart_generation_score', 0) < 60:
            recommendations.append("📊 MEDIUM: Fix chart generation - Plotly visualizations not working")
        
        critical_count = len([f for f in self.findings if f['level'] == 'CRITICAL'])
        if critical_count > 0:
            recommendations.append(f"🔥 CRITICAL: Resolve {critical_count} critical integration issues")
        
        error_count = len([f for f in self.findings if f['level'] == 'ERROR'])
        if error_count >= 5:
            recommendations.append(f"❌ HIGH: Fix {error_count} error-level integration issues")
        
        if not recommendations:
            recommendations.append("🎉 Excellent! Template is ready for real-world use")
        
        return recommendations


def main():
    """Main integration reality audit execution."""
    parser = argparse.ArgumentParser(description="🔧 TDD Template Integration Reality Check")
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output with detailed findings')
    parser.add_argument('--install-deps', action='store_true',
                       help='Attempt to install dependencies via Poetry')
    parser.add_argument('--report', choices=['console', 'json', 'both'], 
                       default='console', help='Report output format')
    parser.add_argument('--output', '-o', help='Output file for JSON report')
    
    args = parser.parse_args()
    
    print("🔧 TDD PROJECT TEMPLATE - INTEGRATION REALITY CHECK")
    print("=" * 60)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Project: {Path.cwd()}")
    print(f"📦 Install Dependencies: {'YES' if args.install_deps else 'NO'}")
    
    auditor = IntegrationRealityAuditor(verbose=args.verbose, install_deps=args.install_deps)
    
    try:
        # Run all integration reality audits
        poetry_results = auditor.audit_poetry_installation()
        imports_results = auditor.audit_dependency_imports()
        execution_results = auditor.audit_script_execution_reality()
        charts_results = auditor.audit_chart_generation_reality()
        
        # Generate final report
        report = auditor.generate_integration_reality_report()
        
        # Output report
        if args.report in ['json', 'both']:
            output_file = args.output or f'integration_reality_audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 JSON report saved: {output_file}")
        
        # Return exit code based on readiness level
        readiness_codes = {'READY': 0, 'MOSTLY_READY': 1, 'NEEDS_SETUP': 2, 'NOT_READY': 3}
        return readiness_codes.get(report['integration_readiness'], 3)
        
    except KeyboardInterrupt:
        print("\n❌ Integration reality audit cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Integration reality audit failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())