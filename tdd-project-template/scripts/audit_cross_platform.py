#!/usr/bin/env python3
"""
🌐 TDD Project Template - Cross-Platform Compatibility Audit
============================================================

Auditoria de compatibilidade multi-ambiente testando funcionalidade
em diferentes sistemas operacionais, versões Python e configurações.

Uso:
    python scripts/audit_cross_platform.py
    python scripts/audit_cross_platform.py --verbose --test-python-versions
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
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import importlib.util


class CrossPlatformAuditor:
    """Auditor de compatibilidade multi-ambiente do template TDD."""
    
    def __init__(self, verbose: bool = False, test_python_versions: bool = False):
        self.verbose = verbose
        self.test_python_versions = test_python_versions
        self.project_root = Path.cwd()
        self.findings = []
        self.metrics = {}
        self.platform_info = self._gather_platform_info()
        
    def _gather_platform_info(self) -> Dict[str, Any]:
        """Gather comprehensive platform information."""
        import platform as plt
        return {
            'system': plt.system(),
            'release': plt.release(),
            'version': plt.version(),
            'architecture': plt.architecture(),
            'machine': plt.machine(),
            'processor': plt.processor(),
            'python_version': plt.python_version(),
            'python_implementation': plt.python_implementation(),
            'python_compiler': plt.python_compiler(),
            'python_build': plt.python_build(),
            'platform_full': plt.platform(),
            'node': plt.node(),
            'uname': plt.uname()._asdict()
        }
        
    def log_finding(self, level: str, category: str, message: str, details: Optional[Dict] = None):
        """Log audit finding with structured data."""
        finding = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'category': category,
            'message': message,
            'details': details or {},
            'platform': self.platform_info['system']
        }
        self.findings.append(finding)
        
        icons = {'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌', 'CRITICAL': '🔥', 'INFO': 'ℹ️'}
        icon = icons.get(level, 'ℹ️')
        print(f"{icon} [{category}] {message}")
        if self.verbose and details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def audit_platform_compatibility(self) -> Dict[str, Any]:
        """Audit platform-specific compatibility issues."""
        print("\n🌐 AUDITING PLATFORM COMPATIBILITY")
        print("=" * 50)
        
        platform_metrics = {
            'platform_support': {},
            'path_handling': {},
            'line_endings': {},
            'permissions': {}
        }
        
        compatibility_score = 0
        
        # Test platform identification
        current_platform = self.platform_info['system']
        supported_platforms = ['Linux', 'Darwin', 'Windows']
        
        if current_platform in supported_platforms:
            platform_metrics['platform_support'][current_platform] = True
            compatibility_score += 25
            self.log_finding('SUCCESS', 'PLATFORM', f"Running on supported platform: {current_platform}")
        else:
            platform_metrics['platform_support'][current_platform] = False
            self.log_finding('WARNING', 'PLATFORM', f"Running on untested platform: {current_platform}")
        
        # Test path handling
        try:
            # Test cross-platform path operations
            test_paths = [
                'scripts/commit_helper.py',
                'epics/epic_1.json',
                'docs/dashboard.html',
                '.github/workflows/update-gantt.yml'
            ]
            
            path_issues = 0
            for test_path in test_paths:
                full_path = self.project_root / test_path
                if full_path.exists():
                    # Test path normalization
                    normalized = Path(test_path)
                    if str(normalized) == test_path.replace('\\', '/'):
                        platform_metrics['path_handling'][test_path] = True
                    else:
                        platform_metrics['path_handling'][test_path] = False
                        path_issues += 1
                else:
                    path_issues += 1
            
            if path_issues == 0:
                compatibility_score += 20
                self.log_finding('SUCCESS', 'PLATFORM', "All paths handle correctly cross-platform")
            else:
                self.log_finding('WARNING', 'PLATFORM', f"{path_issues} path handling issues found")
        
        except Exception as e:
            self.log_finding('ERROR', 'PLATFORM', f"Path handling test failed: {str(e)}")
        
        # Test line ending handling
        try:
            test_files = [
                'scripts/commit_helper.py',
                'README.md',
                '.github/workflows/update-gantt.yml'
            ]
            
            line_ending_issues = 0
            for test_file in test_files:
                file_path = self.project_root / test_file
                if file_path.exists():
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # Check for consistent line endings
                    crlf_count = content.count(b'\r\n')
                    lf_count = content.count(b'\n') - crlf_count
                    cr_count = content.count(b'\r') - crlf_count
                    
                    if crlf_count > 0 and lf_count > 0:
                        line_ending_issues += 1
                        platform_metrics['line_endings'][test_file] = 'mixed'
                    elif crlf_count > 0:
                        platform_metrics['line_endings'][test_file] = 'crlf'
                    elif lf_count > 0:
                        platform_metrics['line_endings'][test_file] = 'lf'
                    else:
                        platform_metrics['line_endings'][test_file] = 'unknown'
            
            if line_ending_issues == 0:
                compatibility_score += 15
                self.log_finding('SUCCESS', 'PLATFORM', "Line endings consistent")
            else:
                self.log_finding('WARNING', 'PLATFORM', f"{line_ending_issues} mixed line ending files")
        
        except Exception as e:
            self.log_finding('ERROR', 'PLATFORM', f"Line ending test failed: {str(e)}")
        
        # Test file permissions (Unix-like systems)
        if current_platform in ['Linux', 'Darwin']:
            try:
                script_files = [
                    'scripts/commit_helper.py',
                    'scripts/test_setup.py'
                ]
                
                permission_issues = 0
                for script_file in script_files:
                    file_path = self.project_root / script_file
                    if file_path.exists():
                        # Check if file is executable or at least readable
                        if os.access(file_path, os.R_OK):
                            platform_metrics['permissions'][script_file] = 'readable'
                            if os.access(file_path, os.X_OK):
                                platform_metrics['permissions'][script_file] = 'executable'
                        else:
                            platform_metrics['permissions'][script_file] = 'no_access'
                            permission_issues += 1
                
                if permission_issues == 0:
                    compatibility_score += 10
                    self.log_finding('SUCCESS', 'PLATFORM', "File permissions correct")
                else:
                    self.log_finding('WARNING', 'PLATFORM', f"{permission_issues} permission issues")
                    
            except Exception as e:
                self.log_finding('ERROR', 'PLATFORM', f"Permission test failed: {str(e)}")
        
        # Test shell command compatibility
        try:
            # Test basic shell commands that scripts might use
            if current_platform == 'Windows':
                test_commands = [
                    ['cmd', '/c', 'echo test'],
                    ['where', 'python'],
                ]
            else:
                test_commands = [
                    ['echo', 'test'],
                    ['which', 'python3'],
                ]
            
            command_successes = 0
            for cmd in test_commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, timeout=5)
                    if result.returncode == 0:
                        command_successes += 1
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            command_success_rate = (command_successes / len(test_commands)) * 100
            if command_success_rate >= 80:
                compatibility_score += 15
                self.log_finding('SUCCESS', 'PLATFORM', f"Shell compatibility: {command_success_rate:.1f}%")
            else:
                self.log_finding('WARNING', 'PLATFORM', f"Shell compatibility issues: {command_success_rate:.1f}%")
                
        except Exception as e:
            self.log_finding('ERROR', 'PLATFORM', f"Shell compatibility test failed: {str(e)}")
        
        # Platform-specific bonus points
        if current_platform == 'Linux':
            compatibility_score += 15  # Primary development platform
            self.log_finding('SUCCESS', 'PLATFORM', "Optimal platform for TDD development")
        elif current_platform == 'Darwin':
            compatibility_score += 10  # Good development platform
            self.log_finding('SUCCESS', 'PLATFORM', "Good platform for TDD development")
        elif current_platform == 'Windows':
            compatibility_score += 5   # Supported but may need more testing
            self.log_finding('INFO', 'PLATFORM', "Windows support available with potential considerations")
        
        self.metrics['platform_compatibility_score'] = compatibility_score
        
        return {
            'score': compatibility_score,
            'metrics': platform_metrics
        }
    
    def audit_python_version_compatibility(self) -> Dict[str, Any]:
        """Audit Python version compatibility."""
        print("\n🐍 AUDITING PYTHON VERSION COMPATIBILITY")
        print("=" * 50)
        
        python_metrics = {
            'current_version': self.platform_info['python_version'],
            'implementation': self.platform_info['python_implementation'],
            'version_support': {},
            'feature_compatibility': {}
        }
        
        python_score = 0
        current_version = tuple(map(int, self.platform_info['python_version'].split('.')))
        
        # Check minimum Python version (3.8+)
        if current_version >= (3, 8):
            python_metrics['version_support']['minimum'] = True
            python_score += 30
            self.log_finding('SUCCESS', 'PYTHON', f"Python {self.platform_info['python_version']} meets minimum requirements (3.8+)")
        else:
            python_metrics['version_support']['minimum'] = False
            self.log_finding('ERROR', 'PYTHON', f"Python {self.platform_info['python_version']} below minimum (3.8)")
        
        # Check recommended Python version (3.9+)
        if current_version >= (3, 9):
            python_metrics['version_support']['recommended'] = True
            python_score += 20
            self.log_finding('SUCCESS', 'PYTHON', "Python version meets recommended requirements (3.9+)")
        else:
            python_metrics['version_support']['recommended'] = False
            self.log_finding('WARNING', 'PYTHON', "Python version below recommended (3.9+)")
        
        # Test Python features required by template
        feature_tests = [
            {
                'name': 'pathlib',
                'test': 'from pathlib import Path; Path("/tmp").exists()',
                'required': True
            },
            {
                'name': 'f_strings',
                'test': 'name = "test"; result = f"Hello {name}"',
                'required': True
            },
            {
                'name': 'type_hints',
                'test': 'from typing import Dict, List, Optional',
                'required': True
            },
            {
                'name': 'dataclasses',
                'test': 'from dataclasses import dataclass',
                'required': False
            },
            {
                'name': 'json',
                'test': 'import json; json.dumps({"test": "value"})',
                'required': True
            },
            {
                'name': 'subprocess',
                'test': 'import subprocess; subprocess.run(["echo", "test"], capture_output=True)',
                'required': True
            },
            {
                'name': 'datetime',
                'test': 'from datetime import datetime; datetime.now().isoformat()',
                'required': True
            }
        ]
        
        feature_successes = 0
        required_successes = 0
        required_total = sum(1 for test in feature_tests if test['required'])
        
        for test in feature_tests:
            try:
                exec(test['test'])
                python_metrics['feature_compatibility'][test['name']] = True
                feature_successes += 1
                if test['required']:
                    required_successes += 1
                self.log_finding('SUCCESS', 'PYTHON', f"Feature available: {test['name']}")
            except Exception as e:
                python_metrics['feature_compatibility'][test['name']] = False
                level = 'ERROR' if test['required'] else 'WARNING'
                self.log_finding(level, 'PYTHON', f"Feature unavailable: {test['name']} - {str(e)}")
        
        # Score based on required features
        if required_successes == required_total:
            python_score += 40
            self.log_finding('SUCCESS', 'PYTHON', "All required Python features available")
        else:
            missing_required = required_total - required_successes
            python_score += max(0, 40 - (missing_required * 10))
            self.log_finding('ERROR', 'PYTHON', f"{missing_required} required Python features missing")
        
        # Bonus for optional features
        optional_successes = feature_successes - required_successes
        optional_total = len(feature_tests) - required_total
        if optional_total > 0:
            optional_score = (optional_successes / optional_total) * 10
            python_score += optional_score
        
        # Test specific Python versions if requested
        if self.test_python_versions:
            self._test_multiple_python_versions(python_metrics)
        
        self.metrics['python_compatibility_score'] = python_score
        
        return {
            'score': python_score,
            'metrics': python_metrics
        }
    
    def _test_multiple_python_versions(self, python_metrics: Dict):
        """Test compatibility with multiple Python versions."""
        test_versions = ['python3.8', 'python3.9', 'python3.10', 'python3.11', 'python3.12']
        version_results = {}
        
        for version_cmd in test_versions:
            try:
                # Test if version is available
                result = subprocess.run([version_cmd, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    # Test basic script execution
                    test_script = '''
import sys
from pathlib import Path
from typing import Dict
import json
print(f"Python {sys.version_info.major}.{sys.version_info.minor} working")
'''
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                        f.write(test_script)
                        f.flush()
                        
                        try:
                            exec_result = subprocess.run([version_cmd, f.name],
                                                       capture_output=True, text=True, timeout=10)
                            
                            version_results[version_cmd] = {
                                'available': True,
                                'working': exec_result.returncode == 0,
                                'output': exec_result.stdout.strip()
                            }
                            
                            if exec_result.returncode == 0:
                                self.log_finding('SUCCESS', 'PYTHON', f"{version_cmd} compatibility confirmed")
                            else:
                                self.log_finding('WARNING', 'PYTHON', f"{version_cmd} execution issues")
                                
                        finally:
                            os.unlink(f.name)
                else:
                    version_results[version_cmd] = {'available': False}
                    
            except (FileNotFoundError, subprocess.TimeoutExpired):
                version_results[version_cmd] = {'available': False}
        
        python_metrics['version_testing'] = version_results
    
    def audit_dependency_compatibility(self) -> Dict[str, Any]:
        """Audit dependency compatibility across environments."""
        print("\n📦 AUDITING DEPENDENCY COMPATIBILITY")
        print("=" * 50)
        
        dependency_metrics = {
            'poetry_compatibility': {},
            'pip_fallback': {},
            'import_simulation': {}
        }
        
        dependency_score = 0
        
        # Test Poetry configuration compatibility
        pyproject_path = self.project_root / 'pyproject.toml'
        if pyproject_path.exists():
            try:
                import toml
                config = toml.load(pyproject_path)
                
                # Check Python version constraints
                python_requires = config.get('tool', {}).get('poetry', {}).get('dependencies', {}).get('python')
                if python_requires:
                    dependency_metrics['poetry_compatibility']['python_constraint'] = python_requires
                    dependency_score += 15
                    self.log_finding('SUCCESS', 'DEPS', f"Python constraint defined: {python_requires}")
                else:
                    self.log_finding('WARNING', 'DEPS', "No Python version constraint in Poetry config")
                
                # Check for platform-specific dependencies
                deps = config.get('tool', {}).get('poetry', {}).get('dependencies', {})
                platform_specific = [dep for dep in deps.values() 
                                   if isinstance(dep, dict) and ('markers' in dep or 'platform' in dep)]
                
                if platform_specific:
                    dependency_metrics['poetry_compatibility']['platform_specific'] = len(platform_specific)
                    dependency_score += 10
                    self.log_finding('SUCCESS', 'DEPS', f"{len(platform_specific)} platform-specific dependencies configured")
                
                dependency_score += 20  # Poetry config exists and valid
                
            except ImportError:
                self.log_finding('WARNING', 'DEPS', "toml module not available for Poetry validation")
            except Exception as e:
                self.log_finding('ERROR', 'DEPS', f"Failed to validate Poetry config: {str(e)}")
        
        # Test pip fallback compatibility
        requirements_path = self.project_root / 'requirements.txt'
        if requirements_path.exists():
            try:
                with open(requirements_path, 'r') as f:
                    requirements = f.read().strip().split('\n')
                
                valid_requirements = [req for req in requirements 
                                    if req.strip() and not req.strip().startswith('#')]
                
                dependency_metrics['pip_fallback']['total_requirements'] = len(valid_requirements)
                dependency_score += 15
                self.log_finding('SUCCESS', 'DEPS', f"{len(valid_requirements)} pip fallback dependencies available")
                
                # Check for problematic dependencies
                problematic_patterns = ['==dev', 'file://', 'git+']
                problematic = [req for req in valid_requirements 
                             if any(pattern in req for pattern in problematic_patterns)]
                
                if problematic:
                    dependency_metrics['pip_fallback']['problematic'] = problematic
                    self.log_finding('WARNING', 'DEPS', f"{len(problematic)} potentially problematic pip requirements")
                else:
                    dependency_score += 10
                    
            except Exception as e:
                self.log_finding('ERROR', 'DEPS', f"Failed to validate requirements.txt: {str(e)}")
        
        # Simulate import testing without actually installing
        critical_imports = [
            'json', 'datetime', 'pathlib', 'subprocess', 'argparse',
            'os', 'sys', 're', 'time', 'tempfile', 'shutil'
        ]
        
        import_successes = 0
        for import_name in critical_imports:
            try:
                exec(f'import {import_name}')
                dependency_metrics['import_simulation'][import_name] = True
                import_successes += 1
            except ImportError:
                dependency_metrics['import_simulation'][import_name] = False
        
        import_success_rate = (import_successes / len(critical_imports)) * 100
        if import_success_rate == 100:
            dependency_score += 25
            self.log_finding('SUCCESS', 'DEPS', "All critical imports available")
        elif import_success_rate >= 90:
            dependency_score += 20
            self.log_finding('SUCCESS', 'DEPS', f"Most critical imports available: {import_success_rate:.1f}%")
        else:
            dependency_score += 10
            self.log_finding('WARNING', 'DEPS', f"Some critical imports missing: {import_success_rate:.1f}%")
        
        # Test package manager availability
        package_managers = ['pip', 'pip3']
        if self.platform_info['system'] != 'Windows':
            package_managers.extend(['poetry'])
        
        manager_available = 0
        for manager in package_managers:
            try:
                result = subprocess.run([manager, '--version'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    manager_available += 1
                    self.log_finding('SUCCESS', 'DEPS', f"Package manager available: {manager}")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self.log_finding('WARNING', 'DEPS', f"Package manager not available: {manager}")
        
        if manager_available > 0:
            dependency_score += 15
        
        self.metrics['dependency_compatibility_score'] = dependency_score
        
        return {
            'score': dependency_score,
            'metrics': dependency_metrics
        }
    
    def audit_script_cross_platform_execution(self) -> Dict[str, Any]:
        """Audit script execution across different environments."""
        print("\n⚡ AUDITING CROSS-PLATFORM SCRIPT EXECUTION")
        print("=" * 50)
        
        execution_metrics = {
            'script_compatibility': {},
            'path_resolution': {},
            'encoding_handling': {}
        }
        
        execution_score = 0
        
        # Test scripts with different execution methods
        test_scripts = [
            'scripts/commit_helper.py',
            'scripts/test_setup.py'
        ]
        
        execution_methods = []
        
        # Determine available execution methods based on platform
        if self.platform_info['system'] == 'Windows':
            execution_methods = [
                ['python'],
                ['py', '-3'],
                [sys.executable]
            ]
        else:
            execution_methods = [
                ['python3'],
                ['python'],
                [sys.executable]
            ]
        
        for script_path in test_scripts:
            full_script_path = self.project_root / script_path
            if not full_script_path.exists():
                continue
            
            script_results = {
                'path_exists': True,
                'execution_methods': {}
            }
            
            for method in execution_methods:
                try:
                    # Test help command to avoid side effects
                    result = subprocess.run(
                        method + [str(full_script_path), '--help'],
                        capture_output=True, text=True, timeout=15,
                        cwd=self.project_root
                    )
                    
                    script_results['execution_methods'][str(method)] = {
                        'success': result.returncode == 0,
                        'has_output': len(result.stdout) > 0,
                        'encoding_ok': 'TDD' in result.stdout or 'help' in result.stdout.lower()
                    }
                    
                    if result.returncode == 0:
                        execution_score += 10
                        self.log_finding('SUCCESS', 'EXECUTION', 
                                       f"{script_path} works with {' '.join(method)}")
                    else:
                        self.log_finding('WARNING', 'EXECUTION',
                                       f"{script_path} fails with {' '.join(method)}")
                        
                except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                    script_results['execution_methods'][str(method)] = {
                        'success': False,
                        'error': str(e)
                    }
                    self.log_finding('WARNING', 'EXECUTION',
                                   f"{script_path} unavailable with {' '.join(method)}")
                except Exception as e:
                    script_results['execution_methods'][str(method)] = {
                        'success': False,
                        'error': str(e)
                    }
            
            execution_metrics['script_compatibility'][script_path] = script_results
        
        # Test path resolution in scripts
        try:
            # Check if scripts use proper cross-platform path handling
            path_issues = 0
            for script_path in test_scripts:
                full_script_path = self.project_root / script_path
                if full_script_path.exists():
                    with open(full_script_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Look for potential path issues
                    problematic_patterns = [
                        r'[\'\"]/[^\'"]*[\'"]',  # Hardcoded absolute Unix paths
                        r'[\'\"]\w:\\[^\'"]*[\'"]',  # Hardcoded absolute Windows paths
                        r'\.split\([\'\"]/[\'"]\)',  # Unix-specific splits
                        r'\.split\([\'\"]\\\[\'"]\)'  # Windows-specific splits
                    ]
                    
                    found_issues = []
                    for pattern in problematic_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            found_issues.extend(matches)
                            path_issues += len(matches)
                    
                    execution_metrics['path_resolution'][script_path] = {
                        'issues_found': len(found_issues),
                        'issues': found_issues[:5]  # Limit to first 5
                    }
            
            if path_issues == 0:
                execution_score += 20
                self.log_finding('SUCCESS', 'EXECUTION', "No obvious cross-platform path issues")
            else:
                self.log_finding('WARNING', 'EXECUTION', f"{path_issues} potential path compatibility issues")
                
        except Exception as e:
            self.log_finding('ERROR', 'EXECUTION', f"Path analysis failed: {str(e)}")
        
        # Test file encoding handling
        try:
            encoding_test_files = [
                'README.md',
                'scripts/commit_helper.py',
                'epics/epic_1.json'
            ]
            
            encoding_issues = 0
            for test_file in encoding_test_files:
                file_path = self.project_root / test_file
                if file_path.exists():
                    try:
                        # Test multiple encodings
                        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
                        successful_encodings = []
                        
                        for encoding in encodings:
                            try:
                                with open(file_path, 'r', encoding=encoding) as f:
                                    content = f.read()
                                    if content:  # Successfully read non-empty content
                                        successful_encodings.append(encoding)
                            except UnicodeDecodeError:
                                continue
                        
                        execution_metrics['encoding_handling'][test_file] = {
                            'successful_encodings': successful_encodings,
                            'utf8_compatible': 'utf-8' in successful_encodings
                        }
                        
                        if 'utf-8' in successful_encodings:
                            execution_score += 5
                        else:
                            encoding_issues += 1
                            
                    except Exception as file_e:
                        execution_metrics['encoding_handling'][test_file] = {
                            'error': str(file_e)
                        }
                        encoding_issues += 1
            
            if encoding_issues == 0:
                execution_score += 15
                self.log_finding('SUCCESS', 'EXECUTION', "All files UTF-8 compatible")
            else:
                self.log_finding('WARNING', 'EXECUTION', f"{encoding_issues} encoding compatibility issues")
                
        except Exception as e:
            self.log_finding('ERROR', 'EXECUTION', f"Encoding test failed: {str(e)}")
        
        self.metrics['script_execution_score'] = execution_score
        
        return {
            'score': execution_score,
            'metrics': execution_metrics
        }
    
    def audit_environment_robustness(self) -> Dict[str, Any]:
        """Audit template robustness in different environments."""
        print("\n🛡️ AUDITING ENVIRONMENT ROBUSTNESS")
        print("=" * 50)
        
        robustness_metrics = {
            'environment_variables': {},
            'working_directory': {},
            'permission_scenarios': {},
            'resource_constraints': {}
        }
        
        robustness_score = 0
        
        # Test environment variable handling
        try:
            # Test with missing environment variables
            original_path = os.environ.get('PATH', '')
            test_vars = ['HOME', 'USER', 'TEMP', 'TMP']
            
            missing_vars = []
            for var in test_vars:
                if var not in os.environ:
                    missing_vars.append(var)
            
            robustness_metrics['environment_variables']['missing_standard'] = missing_vars
            
            if len(missing_vars) <= 1:
                robustness_score += 20
                self.log_finding('SUCCESS', 'ROBUSTNESS', f"Standard environment variables available")
            else:
                self.log_finding('WARNING', 'ROBUSTNESS', f"{len(missing_vars)} standard env vars missing")
            
            # Test PATH variable robustness
            if 'PATH' in os.environ and len(os.environ['PATH']) > 0:
                robustness_score += 15
                self.log_finding('SUCCESS', 'ROBUSTNESS', "PATH environment variable configured")
            else:
                self.log_finding('ERROR', 'ROBUSTNESS', "PATH environment variable missing/empty")
                
        except Exception as e:
            self.log_finding('ERROR', 'ROBUSTNESS', f"Environment variable test failed: {str(e)}")
        
        # Test working directory robustness
        try:
            original_cwd = os.getcwd()
            
            # Test if scripts work from different working directories
            test_directories = [
                self.project_root,
                self.project_root / 'scripts',
                Path.home() if Path.home().exists() else self.project_root
            ]
            
            directory_successes = 0
            for test_dir in test_directories:
                if test_dir.exists():
                    try:
                        os.chdir(test_dir)
                        # Try to run a simple validation
                        script_path = self.project_root / 'scripts' / 'commit_helper.py'
                        if script_path.exists():
                            result = subprocess.run([
                                sys.executable, str(script_path), '--help'
                            ], capture_output=True, timeout=10)
                            
                            if result.returncode == 0:
                                directory_successes += 1
                            
                    except Exception:
                        pass
                    finally:
                        os.chdir(original_cwd)
            
            robustness_metrics['working_directory']['test_directories'] = len(test_directories)
            robustness_metrics['working_directory']['successful'] = directory_successes
            
            if directory_successes >= 2:
                robustness_score += 20
                self.log_finding('SUCCESS', 'ROBUSTNESS', "Works from multiple working directories")
            else:
                self.log_finding('WARNING', 'ROBUSTNESS', "Limited working directory robustness")
                
        except Exception as e:
            self.log_finding('ERROR', 'ROBUSTNESS', f"Working directory test failed: {str(e)}")
        
        # Test permission scenarios (Unix-like systems only)
        if self.platform_info['system'] in ['Linux', 'Darwin']:
            try:
                # Test read-only directory scenario
                temp_dir = Path(tempfile.mkdtemp())
                test_file = temp_dir / 'test_readonly.py'
                
                # Create a simple test script
                with open(test_file, 'w') as f:
                    f.write('print("Hello from readonly test")')
                
                # Make directory read-only
                os.chmod(temp_dir, 0o555)
                
                # Try to execute script in read-only directory
                try:
                    os.chdir(temp_dir)
                    result = subprocess.run([sys.executable, 'test_readonly.py'], 
                                          capture_output=True, timeout=5)
                    
                    if result.returncode == 0:
                        robustness_score += 15
                        self.log_finding('SUCCESS', 'ROBUSTNESS', "Scripts work in read-only directories")
                    else:
                        self.log_finding('WARNING', 'ROBUSTNESS', "Issues with read-only directories")
                        
                except Exception:
                    self.log_finding('WARNING', 'ROBUSTNESS', "Read-only directory test inconclusive")
                
                finally:
                    os.chdir(original_cwd)
                    # Restore permissions and cleanup
                    os.chmod(temp_dir, 0o755)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
            except Exception as e:
                self.log_finding('WARNING', 'ROBUSTNESS', f"Permission test failed: {str(e)}")
        
        # Test resource constraint scenarios
        try:
            # Test with limited memory/CPU (simulated)
            # This is a basic simulation - real constraint testing would require more complex setup
            import resource
            
            # Get current resource limits
            try:
                mem_limit = resource.getrlimit(resource.RLIMIT_AS)
                robustness_metrics['resource_constraints']['memory_limit'] = mem_limit
                robustness_score += 10
                self.log_finding('SUCCESS', 'ROBUSTNESS', "Resource limits accessible")
            except (AttributeError, OSError):
                # Not available on this platform
                pass
            
            # Test large file handling capability
            try:
                large_content = "# Large comment\n" * 10000
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(large_content)
                    f.flush()
                    
                    try:
                        # Try to read large file
                        with open(f.name, 'r') as read_f:
                            content = read_f.read()
                            if len(content) == len(large_content):
                                robustness_score += 10
                                self.log_finding('SUCCESS', 'ROBUSTNESS', "Large file handling works")
                    finally:
                        os.unlink(f.name)
                        
            except Exception:
                self.log_finding('WARNING', 'ROBUSTNESS', "Large file handling issues")
                
        except Exception as e:
            self.log_finding('WARNING', 'ROBUSTNESS', f"Resource constraint test failed: {str(e)}")
        
        self.metrics['environment_robustness_score'] = robustness_score
        
        return {
            'score': robustness_score,
            'metrics': robustness_metrics
        }
    
    def generate_cross_platform_report(self) -> Dict[str, Any]:
        """Generate comprehensive cross-platform compatibility report."""
        print("\n📊 GENERATING CROSS-PLATFORM REPORT")
        print("=" * 50)
        
        # Calculate overall cross-platform score
        cross_platform_weights = {
            'platform_compatibility_score': 0.25,
            'python_compatibility_score': 0.25,
            'dependency_compatibility_score': 0.20,
            'script_execution_score': 0.20,
            'environment_robustness_score': 0.10
        }
        
        overall_score = 0
        for metric, weight in cross_platform_weights.items():
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
            'compatibility_level': self._calculate_compatibility_level(overall_score),
            'platform_info': self.platform_info,
            'weighted_scores': {k: round(self.metrics.get(k, 0), 2) for k in cross_platform_weights.keys()},
            'weights_used': cross_platform_weights,
            'metrics': self.metrics,
            'summary': {
                'total_findings': len(self.findings),
                'critical_issues': len(critical_issues),
                'errors': len(errors),
                'warnings': len(warnings),
                'successes': len(successes)
            },
            'findings': self.findings,
            'recommendations': self._generate_compatibility_recommendations()
        }
        
        # Console summary
        grade_colors = {
            'A+': '🟢', 'A': '🟢', 'B+': '🔵', 'B': '🔵', 
            'C+': '🟡', 'C': '🟡', 'D': '🟠', 'F': '🔴'
        }
        compat_colors = {
            'EXCELLENT': '🟢', 'GOOD': '🔵', 'FAIR': '🟡', 
            'POOR': '🟠', 'INCOMPATIBLE': '🔴'
        }
        
        grade_color = grade_colors.get(report['grade'], '⚪')
        compat_color = compat_colors.get(report['compatibility_level'], '⚪')
        
        print(f"\n{grade_color} OVERALL CROSS-PLATFORM GRADE: {report['grade']} ({overall_score:.1f}%)")
        print(f"{compat_color} COMPATIBILITY LEVEL: {report['compatibility_level']}")
        print(f"🌐 Current Platform: {self.platform_info['system']} {self.platform_info['release']}")
        print(f"🐍 Python Version: {self.platform_info['python_version']} ({self.platform_info['python_implementation']})")
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
    
    def _calculate_compatibility_level(self, score: float) -> str:
        """Calculate compatibility level based on score."""
        if score >= 90: return 'EXCELLENT'
        elif score >= 75: return 'GOOD'
        elif score >= 60: return 'FAIR'
        elif score >= 40: return 'POOR'
        else: return 'INCOMPATIBLE'
    
    def _generate_compatibility_recommendations(self) -> List[str]:
        """Generate actionable compatibility recommendations."""
        recommendations = []
        
        if self.metrics.get('platform_compatibility_score', 0) < 70:
            recommendations.append("🌐 HIGH: Fix platform-specific path and line ending issues")
        
        if self.metrics.get('python_compatibility_score', 0) < 70:
            recommendations.append("🐍 CRITICAL: Update Python version to 3.8+ or fix version compatibility")
        
        if self.metrics.get('dependency_compatibility_score', 0) < 70:
            recommendations.append("📦 HIGH: Improve dependency management and fallback options")
        
        if self.metrics.get('script_execution_score', 0) < 70:
            recommendations.append("⚡ HIGH: Fix script execution issues across different environments")
        
        if self.metrics.get('environment_robustness_score', 0) < 60:
            recommendations.append("🛡️ MEDIUM: Improve robustness for different environment conditions")
        
        # Platform-specific recommendations
        current_platform = self.platform_info['system']
        if current_platform == 'Windows':
            recommendations.append("🪟 MEDIUM: Add Windows-specific testing and documentation")
        elif current_platform == 'Darwin':
            recommendations.append("🍎 LOW: Consider macOS-specific optimizations")
        
        critical_count = len([f for f in self.findings if f['level'] == 'CRITICAL'])
        if critical_count > 0:
            recommendations.append(f"🔥 CRITICAL: Resolve {critical_count} critical compatibility issues")
        
        error_count = len([f for f in self.findings if f['level'] == 'ERROR'])
        if error_count >= 3:
            recommendations.append(f"❌ HIGH: Fix {error_count} error-level compatibility issues")
        
        if not recommendations:
            recommendations.append("🎉 Excellent! Template shows strong cross-platform compatibility")
        
        return recommendations


def main():
    """Main cross-platform audit execution."""
    parser = argparse.ArgumentParser(description="🌐 TDD Template Cross-Platform Compatibility Audit")
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output with detailed findings')
    parser.add_argument('--test-python-versions', action='store_true',
                       help='Test compatibility with multiple Python versions')
    parser.add_argument('--report', choices=['console', 'json', 'both'], 
                       default='console', help='Report output format')
    parser.add_argument('--output', '-o', help='Output file for JSON report')
    
    args = parser.parse_args()
    
    print("🌐 TDD PROJECT TEMPLATE - CROSS-PLATFORM COMPATIBILITY AUDIT")
    print("=" * 70)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Project: {Path.cwd()}")
    print(f"🐍 Python Version Testing: {'YES' if args.test_python_versions else 'NO'}")
    
    auditor = CrossPlatformAuditor(verbose=args.verbose, test_python_versions=args.test_python_versions)
    
    try:
        # Run all cross-platform compatibility audits
        platform_results = auditor.audit_platform_compatibility()
        python_results = auditor.audit_python_version_compatibility()
        dependency_results = auditor.audit_dependency_compatibility()
        execution_results = auditor.audit_script_cross_platform_execution()
        robustness_results = auditor.audit_environment_robustness()
        
        # Generate final report
        report = auditor.generate_cross_platform_report()
        
        # Output report
        if args.report in ['json', 'both']:
            output_file = args.output or f'cross_platform_audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 JSON report saved: {output_file}")
        
        # Return exit code based on compatibility level
        compat_codes = {'EXCELLENT': 0, 'GOOD': 0, 'FAIR': 1, 'POOR': 2, 'INCOMPATIBLE': 3}
        return compat_codes.get(report['compatibility_level'], 3)
        
    except KeyboardInterrupt:
        print("\n❌ Cross-platform audit cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Cross-platform audit failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())