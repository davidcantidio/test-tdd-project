#!/usr/bin/env python3
"""
🔒 TDD Project Template - Code Quality & Security Audit
=====================================================

Auditoria rigorosa de qualidade de código, segurança e best practices.
Analisa vulnerabilidades, padrões de código, e compliance com standards.

Uso:
    python scripts/audit_code_quality.py
    python scripts/audit_code_quality.py --verbose --security-focused
"""

import argparse
import json
import os
import sys
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set
from datetime import datetime
import hashlib
import base64


class CodeQualityAuditor:
    """Auditor rigoroso de qualidade de código e segurança."""
    
    def __init__(self, verbose: bool = False, security_focused: bool = False):
        self.verbose = verbose
        self.security_focused = security_focused
        self.project_root = Path.cwd()
        self.findings = []
        self.metrics = {}
        self.security_issues = []
        
        # Security patterns to detect
        self.security_patterns = {
            'hardcoded_secrets': [
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'password\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
                r'key\s*=\s*["\'][A-Za-z0-9+/]{32,}={0,2}["\']',  # base64-ish
                r'["\'][A-Za-z0-9]{32,}["\']',  # long hex strings
            ],
            'sql_injection_risk': [
                r'execute\s*\(\s*["\'].+\+.+["\']',
                r'query\s*\(\s*["\'].+\+.+["\']',
                r'SELECT\s+.+\+',
                r'INSERT\s+.+\+',
                r'UPDATE\s+.+\+',
                r'DELETE\s+.+\+',
            ],
            'command_injection_risk': [
                r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True',
                r'os\.(system|popen)\s*\(',
                r'eval\s*\(',
                r'exec\s*\(',
            ],
            'path_traversal_risk': [
                r'\.\./',
                r'open\s*\([^)]*\+',  # file path concatenation
                r'Path\s*\([^)]*\+',
            ],
            'unsafe_deserialization': [
                r'pickle\.loads?\s*\(',
                r'yaml\.load\s*\(',  # should use safe_load
                r'json\.loads?\s*\([^)]*user',
            ]
        }
        
    def log_finding(self, level: str, category: str, message: str, 
                   details: Optional[Dict] = None, security_risk: bool = False):
        """Log audit finding with structured data."""
        finding = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'category': category,
            'message': message,
            'details': details or {},
            'security_risk': security_risk
        }
        self.findings.append(finding)
        
        if security_risk:
            self.security_issues.append(finding)
        
        icons = {
            'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌', 
            'CRITICAL': '🔥', 'INFO': 'ℹ️', 'SECURITY': '🔒'
        }
        icon = icons.get(level, 'ℹ️')
        if security_risk:
            icon = '🔒'
            
        print(f"{icon} [{category}] {message}")
        if self.verbose and details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def audit_code_style_consistency(self) -> Dict[str, Any]:
        """Audit code style consistency across Python files."""
        print("\n🎨 AUDITING CODE STYLE CONSISTENCY")
        print("=" * 50)
        
        python_files = list(self.project_root.rglob("*.py"))
        style_metrics = {
            'total_files': len(python_files),
            'inconsistent_indentation': 0,
            'missing_docstrings': 0,
            'long_lines': 0,
            'inconsistent_imports': 0,
            'style_violations': []
        }
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                file_path = str(py_file.relative_to(self.project_root))
                file_issues = []
                
                # Check indentation consistency
                indentation_types = set()
                for line in lines:
                    if line.strip() and line.startswith((' ', '\t')):
                        if line.startswith('    '):
                            indentation_types.add('spaces')
                        elif line.startswith('\t'):
                            indentation_types.add('tabs')
                
                if len(indentation_types) > 1:
                    style_metrics['inconsistent_indentation'] += 1
                    file_issues.append('mixed_indentation')
                
                # Check for missing docstrings in functions/classes
                has_class_or_func = bool(re.search(r'^(class|def)\s+', content, re.MULTILINE))
                has_docstring = '"""' in content or "'''" in content
                
                if has_class_or_func and not has_docstring:
                    style_metrics['missing_docstrings'] += 1
                    file_issues.append('missing_docstrings')
                
                # Check line length (PEP 8 recommends 79-88 chars)
                long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 100]
                if long_lines:
                    style_metrics['long_lines'] += len(long_lines)
                    file_issues.append(f'long_lines: {len(long_lines)}')
                
                # Check import organization
                import_lines = [line for line in lines if re.match(r'^(import|from)\s+', line)]
                if len(import_lines) > 3:
                    # Check if imports are grouped (stdlib, 3rd party, local)
                    import_blocks = []
                    current_block = []
                    for line in lines:
                        if re.match(r'^(import|from)\s+', line):
                            current_block.append(line)
                        elif current_block and line.strip() == '':
                            import_blocks.append(current_block)
                            current_block = []
                        elif current_block and line.strip():
                            break  # imports should be at top
                    
                    if current_block:
                        import_blocks.append(current_block)
                    
                    if len(import_blocks) == 1 and len(import_lines) > 5:
                        style_metrics['inconsistent_imports'] += 1
                        file_issues.append('ungrouped_imports')
                
                if file_issues:
                    style_metrics['style_violations'].append({
                        'file': file_path,
                        'issues': file_issues
                    })
                    self.log_finding('WARNING', 'STYLE', 
                                   f"Style issues in {py_file.name}",
                                   {'issues': file_issues})
                else:
                    self.log_finding('SUCCESS', 'STYLE',
                                   f"Good style: {py_file.name}")
                    
            except Exception as e:
                self.log_finding('ERROR', 'STYLE',
                               f"Failed to analyze {py_file.name}: {str(e)}")
        
        # Calculate style score
        total_issues = (style_metrics['inconsistent_indentation'] + 
                       style_metrics['missing_docstrings'] + 
                       min(style_metrics['long_lines'], 10) +  # cap long lines impact
                       style_metrics['inconsistent_imports'])
        
        style_score = max(0, 100 - (total_issues * 5))  # -5 points per issue
        self.metrics['code_style_score'] = style_score
        
        return {
            'score': style_score,
            'metrics': style_metrics
        }
    
    def audit_security_vulnerabilities(self) -> Dict[str, Any]:
        """Audit for security vulnerabilities and unsafe patterns."""
        print("\n🔒 AUDITING SECURITY VULNERABILITIES")
        print("=" * 50)
        
        security_findings = {
            'critical_vulnerabilities': [],
            'potential_risks': [],
            'safe_patterns': [],
            'total_files_scanned': 0
        }
        
        # Scan Python files for security issues
        python_files = list(self.project_root.rglob("*.py"))
        config_files = (list(self.project_root.rglob("*.yml")) + 
                       list(self.project_root.rglob("*.yaml")) +
                       list(self.project_root.rglob("*.json")) +
                       list(self.project_root.rglob("*.env*")))
        
        all_files = python_files + config_files
        security_findings['total_files_scanned'] = len(all_files)
        
        for file_path in all_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                file_rel = str(file_path.relative_to(self.project_root))
                
                # Check for hardcoded secrets
                for pattern in self.security_patterns['hardcoded_secrets']:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Skip obvious examples or templates
                        if any(x in match.lower() for x in ['example', 'placeholder', 'your-', 'template']):
                            continue
                            
                        security_findings['critical_vulnerabilities'].append({
                            'type': 'hardcoded_secret',
                            'file': file_rel,
                            'pattern': pattern,
                            'risk_level': 'HIGH'
                        })
                        self.log_finding('CRITICAL', 'SECURITY',
                                       f"Potential hardcoded secret in {file_path.name}",
                                       {'pattern': pattern}, security_risk=True)
                
                # Check for SQL injection risks (only in Python files)
                if file_path.suffix == '.py':
                    for pattern in self.security_patterns['sql_injection_risk']:
                        if re.search(pattern, content, re.IGNORECASE):
                            security_findings['potential_risks'].append({
                                'type': 'sql_injection_risk',
                                'file': file_rel,
                                'pattern': pattern,
                                'risk_level': 'MEDIUM'
                            })
                            self.log_finding('WARNING', 'SECURITY',
                                           f"Potential SQL injection risk in {file_path.name}",
                                           {'pattern': pattern}, security_risk=True)
                    
                    # Check for command injection risks
                    for pattern in self.security_patterns['command_injection_risk']:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            security_findings['critical_vulnerabilities'].append({
                                'type': 'command_injection_risk',
                                'file': file_rel,
                                'match': match,
                                'risk_level': 'HIGH'
                            })
                            self.log_finding('CRITICAL', 'SECURITY',
                                           f"Command injection risk in {file_path.name}",
                                           {'match': match}, security_risk=True)
                    
                    # Check for unsafe YAML loading
                    if 'yaml.load(' in content and 'safe_load' not in content:
                        security_findings['potential_risks'].append({
                            'type': 'unsafe_yaml_load',
                            'file': file_rel,
                            'risk_level': 'HIGH'
                        })
                        self.log_finding('WARNING', 'SECURITY',
                                       f"Unsafe YAML loading in {file_path.name}",
                                       security_risk=True)
                
                # Check for safe patterns (positive indicators)
                safe_indicators = [
                    'safe_load',
                    'os.environ.get',
                    'getpass.getpass',
                    'secrets.token',
                    'hashlib.sha256',
                    'ssl.create_default_context'
                ]
                
                safe_count = sum(1 for indicator in safe_indicators if indicator in content)
                if safe_count > 0:
                    security_findings['safe_patterns'].append({
                        'file': file_rel,
                        'safe_patterns_count': safe_count
                    })
                    self.log_finding('SUCCESS', 'SECURITY',
                                   f"Good security practices in {file_path.name}",
                                   {'safe_patterns': safe_count})
                    
            except Exception as e:
                self.log_finding('ERROR', 'SECURITY',
                               f"Failed to scan {file_path.name}: {str(e)}")
        
        # Calculate security score
        critical_count = len(security_findings['critical_vulnerabilities'])
        risk_count = len(security_findings['potential_risks'])
        safe_count = len(security_findings['safe_patterns'])
        
        security_score = max(0, 100 - (critical_count * 25) - (risk_count * 10) + (safe_count * 5))
        self.metrics['security_score'] = security_score
        
        return {
            'score': security_score,
            'findings': security_findings
        }
    
    def audit_configuration_security(self) -> Dict[str, Any]:
        """Audit configuration files for security issues."""
        print("\n⚙️ AUDITING CONFIGURATION SECURITY")
        print("=" * 50)
        
        config_security = {
            'exposed_secrets': [],
            'insecure_permissions': [],
            'good_practices': []
        }
        
        # Check environment files
        env_files = list(self.project_root.rglob("*.env*"))
        for env_file in env_files:
            if env_file.is_file():
                try:
                    content = env_file.read_text()
                    file_rel = str(env_file.relative_to(self.project_root))
                    
                    # Check for exposed secrets in .env files
                    lines = content.split('\n')
                    for line_no, line in enumerate(lines, 1):
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            value = value.strip('"\'')
                            
                            # Skip if it's obviously a template/example
                            if any(x in value.lower() for x in ['example', 'your-', 'placeholder', 'template']):
                                config_security['good_practices'].append({
                                    'file': file_rel,
                                    'practice': 'uses_template_values'
                                })
                                continue
                            
                            # Check for potentially real secrets
                            if len(value) > 20 and not value.isdigit():
                                if any(x in key.lower() for x in ['key', 'secret', 'token', 'password']):
                                    config_security['exposed_secrets'].append({
                                        'file': file_rel,
                                        'line': line_no,
                                        'key': key,
                                        'risk_level': 'HIGH'
                                    })
                                    self.log_finding('CRITICAL', 'CONFIG_SECURITY',
                                                   f"Potential exposed secret in {env_file.name}",
                                                   {'key': key, 'line': line_no}, security_risk=True)
                    
                    # Check if .env files are in .gitignore
                    gitignore_path = self.project_root / '.gitignore'
                    if gitignore_path.exists():
                        gitignore_content = gitignore_path.read_text()
                        if '.env' in gitignore_content:
                            config_security['good_practices'].append({
                                'file': file_rel,
                                'practice': 'properly_gitignored'
                            })
                            self.log_finding('SUCCESS', 'CONFIG_SECURITY',
                                           f"Environment file properly ignored: {env_file.name}")
                        else:
                            self.log_finding('WARNING', 'CONFIG_SECURITY',
                                           f"Environment file not in .gitignore: {env_file.name}",
                                           security_risk=True)
                            
                except Exception as e:
                    self.log_finding('ERROR', 'CONFIG_SECURITY',
                                   f"Failed to audit {env_file.name}: {str(e)}")
        
        # Check GitHub workflows for secrets handling
        workflow_files = list((self.project_root / '.github' / 'workflows').glob('*.yml'))
        for workflow_file in workflow_files:
            if workflow_file.is_file():
                try:
                    content = workflow_file.read_text()
                    file_rel = str(workflow_file.relative_to(self.project_root))
                    
                    # Check for proper secrets usage
                    if 'secrets.' in content:
                        config_security['good_practices'].append({
                            'file': file_rel,
                            'practice': 'uses_github_secrets'
                        })
                        self.log_finding('SUCCESS', 'CONFIG_SECURITY',
                                       f"Proper secrets usage in {workflow_file.name}")
                    
                    # Check for hardcoded tokens in workflow
                    token_patterns = [r'[a-f0-9]{40}', r'gh[ps]_[A-Za-z0-9_]{36}']
                    for pattern in token_patterns:
                        if re.search(pattern, content):
                            config_security['exposed_secrets'].append({
                                'file': file_rel,
                                'type': 'github_token',
                                'risk_level': 'CRITICAL'
                            })
                            self.log_finding('CRITICAL', 'CONFIG_SECURITY',
                                           f"Potential hardcoded token in {workflow_file.name}",
                                           security_risk=True)
                            
                except Exception as e:
                    self.log_finding('ERROR', 'CONFIG_SECURITY',
                                   f"Failed to audit {workflow_file.name}: {str(e)}")
        
        # Calculate configuration security score
        critical_issues = len(config_security['exposed_secrets'])
        good_practices = len(config_security['good_practices'])
        
        config_score = max(0, 100 - (critical_issues * 30) + (good_practices * 10))
        self.metrics['config_security_score'] = config_score
        
        return {
            'score': config_score,
            'findings': config_security
        }
    
    def audit_input_validation(self) -> Dict[str, Any]:
        """Audit input validation and error handling patterns."""
        print("\n🛡️ AUDITING INPUT VALIDATION & ERROR HANDLING")
        print("=" * 50)
        
        validation_metrics = {
            'functions_with_validation': 0,
            'functions_without_validation': 0,
            'error_handling_patterns': [],
            'validation_patterns': [],
            'total_functions': 0
        }
        
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            try:
                content = py_file.read_text()
                file_rel = str(py_file.relative_to(self.project_root))
                
                # Find function definitions
                function_matches = re.finditer(r'^def\s+(\w+)\s*\([^)]*\):', content, re.MULTILINE)
                
                for func_match in function_matches:
                    validation_metrics['total_functions'] += 1
                    func_name = func_match.group(1)
                    
                    # Get function body (simplified - until next def or class)
                    start_pos = func_match.start()
                    rest_content = content[start_pos:]
                    
                    # Find end of function (next def/class at same indent level)
                    lines = rest_content.split('\n')
                    func_lines = [lines[0]]  # function definition
                    indent_level = None
                    
                    for line in lines[1:]:
                        if line.strip() == '':
                            func_lines.append(line)
                            continue
                            
                        current_indent = len(line) - len(line.lstrip())
                        if indent_level is None and line.strip():
                            indent_level = current_indent
                        
                        if line.strip() and current_indent <= indent_level and re.match(r'^(def|class)\s+', line.lstrip()):
                            break
                            
                        func_lines.append(line)
                    
                    func_body = '\n'.join(func_lines)
                    
                    # Check for validation patterns
                    validation_patterns = [
                        'isinstance(',
                        'if not ',
                        'raise ValueError',
                        'raise TypeError',
                        'assert ',
                        '.strip()',
                        'len(',
                        'if.*is None'
                    ]
                    
                    has_validation = any(pattern in func_body for pattern in validation_patterns)
                    
                    # Check for error handling
                    error_handling_patterns = [
                        'try:',
                        'except',
                        'raise',
                        'logging.',
                        'print('  # basic error reporting
                    ]
                    
                    has_error_handling = any(pattern in func_body for pattern in error_handling_patterns)
                    
                    if has_validation:
                        validation_metrics['functions_with_validation'] += 1
                        validation_metrics['validation_patterns'].append({
                            'file': file_rel,
                            'function': func_name,
                            'patterns': [p for p in validation_patterns if p in func_body]
                        })
                    else:
                        validation_metrics['functions_without_validation'] += 1
                    
                    if has_error_handling:
                        validation_metrics['error_handling_patterns'].append({
                            'file': file_rel,
                            'function': func_name,
                            'patterns': [p for p in error_handling_patterns if p in func_body]
                        })
                
            except Exception as e:
                self.log_finding('ERROR', 'VALIDATION',
                               f"Failed to analyze {py_file.name}: {str(e)}")
        
        # Calculate validation score
        if validation_metrics['total_functions'] > 0:
            validation_ratio = validation_metrics['functions_with_validation'] / validation_metrics['total_functions']
            validation_score = validation_ratio * 100
        else:
            validation_score = 100  # No functions to validate
            
        self.metrics['input_validation_score'] = validation_score
        
        if validation_score >= 70:
            self.log_finding('SUCCESS', 'VALIDATION',
                           f"Good input validation coverage: {validation_score:.1f}%")
        elif validation_score >= 40:
            self.log_finding('WARNING', 'VALIDATION',
                           f"Moderate input validation: {validation_score:.1f}%")
        else:
            self.log_finding('ERROR', 'VALIDATION',
                           f"Poor input validation: {validation_score:.1f}%")
        
        return {
            'score': validation_score,
            'metrics': validation_metrics
        }
    
    def audit_dependency_security(self) -> Dict[str, Any]:
        """Audit dependency security and supply chain risks."""
        print("\n📦 AUDITING DEPENDENCY SECURITY")
        print("=" * 50)
        
        dep_security = {
            'package_managers': [],
            'dependency_count': 0,
            'security_findings': []
        }
        
        # Check Poetry dependencies
        pyproject_path = self.project_root / 'pyproject.toml'
        if pyproject_path.exists():
            try:
                import toml
                config = toml.load(pyproject_path)
                poetry_deps = config.get('tool', {}).get('poetry', {}).get('dependencies', {})
                dev_deps = config.get('tool', {}).get('poetry', {}).get('group', {}).get('dev', {}).get('dependencies', {})
                
                dep_security['package_managers'].append('poetry')
                dep_security['dependency_count'] = len(poetry_deps) + len(dev_deps)
                
                # Check for version pinning
                unpinned_deps = []
                for dep_name, dep_spec in {**poetry_deps, **dev_deps}.items():
                    if isinstance(dep_spec, str):
                        if dep_spec.startswith('^') or dep_spec.startswith('~'):
                            continue  # acceptable version ranges
                        elif '*' in dep_spec or not any(c in dep_spec for c in ['>', '<', '=']):
                            unpinned_deps.append(dep_name)
                
                if unpinned_deps:
                    dep_security['security_findings'].append({
                        'type': 'unpinned_dependencies',
                        'dependencies': unpinned_deps,
                        'risk_level': 'MEDIUM'
                    })
                    self.log_finding('WARNING', 'DEPENDENCY_SECURITY',
                                   f"Unpinned dependencies: {', '.join(unpinned_deps[:3])}")
                else:
                    self.log_finding('SUCCESS', 'DEPENDENCY_SECURITY',
                                   "All dependencies properly pinned")
                
            except ImportError:
                self.log_finding('WARNING', 'DEPENDENCY_SECURITY',
                               "toml module not available for Poetry audit")
            except Exception as e:
                self.log_finding('ERROR', 'DEPENDENCY_SECURITY',
                               f"Failed to audit Poetry dependencies: {str(e)}")
        
        # Check requirements.txt
        req_path = self.project_root / 'requirements.txt'
        if req_path.exists():
            try:
                requirements = req_path.read_text().strip().split('\n')
                req_deps = [r for r in requirements if r and not r.startswith('#')]
                
                dep_security['package_managers'].append('pip')
                if 'dependency_count' not in dep_security or dep_security['dependency_count'] == 0:
                    dep_security['dependency_count'] = len(req_deps)
                
                # Check for version pinning in requirements.txt
                unpinned_reqs = []
                for req in req_deps:
                    if not any(op in req for op in ['==', '>=', '<=', '>', '<', '~=']):
                        unpinned_reqs.append(req)
                
                if unpinned_reqs:
                    dep_security['security_findings'].append({
                        'type': 'unpinned_requirements',
                        'requirements': unpinned_reqs,
                        'risk_level': 'MEDIUM'
                    })
                    self.log_finding('WARNING', 'DEPENDENCY_SECURITY',
                                   f"Unpinned requirements: {', '.join(unpinned_reqs[:3])}")
                else:
                    self.log_finding('SUCCESS', 'DEPENDENCY_SECURITY',
                                   "All requirements properly pinned")
                    
            except Exception as e:
                self.log_finding('ERROR', 'DEPENDENCY_SECURITY',
                               f"Failed to audit requirements.txt: {str(e)}")
        
        # Check for known vulnerable packages (simplified check)
        known_vulnerable = ['pillow<8.3.2', 'flask<2.0.0', 'requests<2.25.0', 'urllib3<1.26.5']
        
        # Calculate dependency security score
        unpinned_count = len([f for f in dep_security['security_findings'] 
                             if f['type'] in ['unpinned_dependencies', 'unpinned_requirements']])
        
        dep_score = max(0, 100 - (unpinned_count * 20))
        self.metrics['dependency_security_score'] = dep_score
        
        return {
            'score': dep_score,
            'findings': dep_security
        }
    
    def generate_code_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive code quality and security report."""
        print("\n📊 GENERATING CODE QUALITY REPORT")
        print("=" * 50)
        
        # Calculate overall score
        scores = [v for k, v in self.metrics.items() if k.endswith('_score')]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Categorize findings
        critical_issues = [f for f in self.findings if f['level'] == 'CRITICAL']
        errors = [f for f in self.findings if f['level'] == 'ERROR']
        warnings = [f for f in self.findings if f['level'] == 'WARNING']
        successes = [f for f in self.findings if f['level'] == 'SUCCESS']
        security_issues = len(self.security_issues)
        
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'overall_score': round(overall_score, 2),
            'grade': self._calculate_grade(overall_score),
            'security_risk_level': self._calculate_security_risk(),
            'metrics': self.metrics,
            'summary': {
                'total_findings': len(self.findings),
                'critical_issues': len(critical_issues),
                'errors': len(errors),
                'warnings': len(warnings),
                'successes': len(successes),
                'security_issues': security_issues
            },
            'findings': self.findings,
            'security_issues': self.security_issues,
            'recommendations': self._generate_quality_recommendations()
        }
        
        # Console summary
        grade_colors = {
            'A+': '🟢', 'A': '🟢', 'B+': '🔵', 'B': '🔵', 
            'C+': '🟡', 'C': '🟡', 'D': '🟠', 'F': '🔴'
        }
        risk_colors = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🔴', 'CRITICAL': '🔥'}
        
        grade_color = grade_colors.get(report['grade'], '⚪')
        risk_color = risk_colors.get(report['security_risk_level'], '⚪')
        
        print(f"\n{grade_color} OVERALL CODE QUALITY GRADE: {report['grade']} ({overall_score:.1f}%)")
        print(f"{risk_color} SECURITY RISK LEVEL: {report['security_risk_level']}")
        print(f"📊 Total Findings: {len(self.findings)}")
        print(f"🔥 Critical: {len(critical_issues)}")
        print(f"❌ Errors: {len(errors)}")
        print(f"⚠️ Warnings: {len(warnings)}")
        print(f"✅ Successes: {len(successes)}")
        print(f"🔒 Security Issues: {security_issues}")
        
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
    
    def _calculate_security_risk(self) -> str:
        """Calculate security risk level."""
        critical_security = len([f for f in self.security_issues if f['level'] == 'CRITICAL'])
        total_security = len(self.security_issues)
        
        if critical_security > 0:
            return 'CRITICAL'
        elif total_security >= 5:
            return 'HIGH'
        elif total_security >= 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_quality_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on findings."""
        recommendations = []
        
        security_issues = len(self.security_issues)
        if security_issues > 0:
            recommendations.append(f"🔒 CRITICAL: Fix {security_issues} security vulnerabilities immediately")
        
        if self.metrics.get('security_score', 100) < 70:
            recommendations.append("🔥 HIGH: Address security vulnerabilities before production")
        
        if self.metrics.get('code_style_score', 100) < 80:
            recommendations.append("🎨 MEDIUM: Improve code style consistency (consider using ruff/black)")
        
        if self.metrics.get('input_validation_score', 100) < 60:
            recommendations.append("🛡️ HIGH: Add input validation to functions handling external data")
        
        if self.metrics.get('dependency_security_score', 100) < 80:
            recommendations.append("📦 MEDIUM: Pin dependency versions and audit for vulnerabilities")
        
        critical_count = len([f for f in self.findings if f['level'] == 'CRITICAL'])
        if critical_count > 0:
            recommendations.append(f"🔥 CRITICAL: Resolve {critical_count} critical issues before deployment")
        
        if not recommendations:
            recommendations.append("🎉 Excellent! Code quality and security standards are well maintained")
        
        return recommendations


def main():
    """Main code quality audit execution."""
    parser = argparse.ArgumentParser(description="🔒 TDD Template Code Quality & Security Audit")
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output with detailed findings')
    parser.add_argument('--security-focused', action='store_true',
                       help='Focus on security vulnerabilities and risks')
    parser.add_argument('--report', choices=['console', 'json', 'both'], 
                       default='console', help='Report output format')
    parser.add_argument('--output', '-o', help='Output file for JSON report')
    
    args = parser.parse_args()
    
    print("🔒 TDD PROJECT TEMPLATE - CODE QUALITY & SECURITY AUDIT")
    print("=" * 60)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Project: {Path.cwd()}")
    print(f"🔍 Security Focused: {'YES' if args.security_focused else 'NO'}")
    
    auditor = CodeQualityAuditor(verbose=args.verbose, security_focused=args.security_focused)
    
    try:
        # Run all quality audits
        style_results = auditor.audit_code_style_consistency()
        security_results = auditor.audit_security_vulnerabilities()
        config_results = auditor.audit_configuration_security()
        validation_results = auditor.audit_input_validation()
        dependency_results = auditor.audit_dependency_security()
        
        # Generate final report
        report = auditor.generate_code_quality_report()
        
        # Output report
        if args.report in ['json', 'both']:
            output_file = args.output or f'code_quality_audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 JSON report saved: {output_file}")
        
        # Return exit code based on security risk
        risk_codes = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2, 'CRITICAL': 3}
        return risk_codes.get(report['security_risk_level'], 3)
        
    except KeyboardInterrupt:
        print("\n❌ Code quality audit cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Code quality audit failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())