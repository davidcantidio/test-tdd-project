#!/usr/bin/env python3
"""
🏗️ TDD Project Template - Architecture Audit
=============================================

Auditoria rigorosa da arquitetura e estrutura do projeto.
Valida aderência a padrões profissionais e best practices.

Uso:
    python scripts/audit_architecture.py
    python scripts/audit_architecture.py --verbose
    python scripts/audit_architecture.py --report=json
"""

import argparse
import json
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import re
import subprocess
from datetime import datetime


class ArchitectureAuditor:
    """Auditor completo da arquitetura do template TDD."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = Path.cwd()
        self.findings = []
        self.metrics = {}
        
    def log_finding(self, level: str, category: str, message: str, details: Optional[Dict] = None):
        """Log audit finding with structured data."""
        finding = {
            'timestamp': datetime.now().isoformat(),
            'level': level,  # SUCCESS, WARNING, ERROR, CRITICAL
            'category': category,
            'message': message,
            'details': details or {}
        }
        self.findings.append(finding)
        
        # Console output
        icons = {'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌', 'CRITICAL': '🔥'}
        icon = icons.get(level, 'ℹ️')
        print(f"{icon} [{category}] {message}")
        if self.verbose and details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def audit_directory_structure(self) -> Dict[str, Any]:
        """Audit project directory structure against best practices."""
        print("\n🏗️ AUDITING DIRECTORY STRUCTURE")
        print("=" * 50)
        
        expected_structure = {
            # Core directories
            '.github/workflows': {'required': True, 'description': 'GitHub Actions workflows'},
            'docs': {'required': True, 'description': 'Jekyll documentation'},
            'scripts': {'required': True, 'description': 'Automation scripts'},
            'scripts/visualization': {'required': True, 'description': 'Analytics scripts'},
            'epics': {'required': True, 'description': 'Epic JSON definitions'},
            
            # Optional but recommended
            'tests': {'required': False, 'description': 'Unit tests'},
            'config': {'required': False, 'description': 'Configuration files'},
            'config/docker': {'required': False, 'description': 'Docker setup'},
            'config/environment': {'required': False, 'description': 'Environment configs'},
            'config/vscode': {'required': False, 'description': 'VS Code settings'},
            'tdah_tools': {'required': False, 'description': 'TDAH optimization tools'},
        }
        
        structure_score = 0
        total_dirs = len(expected_structure)
        
        for dir_path, config in expected_structure.items():
            full_path = self.project_root / dir_path
            if full_path.exists() and full_path.is_dir():
                structure_score += 1
                self.log_finding('SUCCESS', 'STRUCTURE', 
                               f"Directory exists: {dir_path}", 
                               {'description': config['description']})
            else:
                level = 'ERROR' if config['required'] else 'WARNING'
                self.log_finding(level, 'STRUCTURE',
                               f"Missing directory: {dir_path}",
                               {'required': config['required'], 'description': config['description']})
        
        # Check for unexpected directories that might indicate poor organization
        unexpected_dirs = []
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in [d.split('/')[0] for d in expected_structure]:
                unexpected_dirs.append(item.name)
        
        if unexpected_dirs:
            self.log_finding('WARNING', 'STRUCTURE',
                           f"Unexpected root directories: {', '.join(unexpected_dirs)}",
                           {'directories': unexpected_dirs})
        
        structure_percentage = (structure_score / total_dirs) * 100
        self.metrics['directory_structure_score'] = structure_percentage
        
        return {
            'score': structure_percentage,
            'directories_found': structure_score,
            'total_expected': total_dirs,
            'unexpected_directories': unexpected_dirs
        }
    
    def audit_core_files(self) -> Dict[str, Any]:
        """Audit critical project files."""
        print("\n📁 AUDITING CORE FILES")
        print("=" * 50)
        
        critical_files = {
            'pyproject.toml': {'required': True, 'validator': self._validate_pyproject},
            'README.md': {'required': True, 'validator': self._validate_readme},
            'requirements.txt': {'required': True, 'validator': self._validate_requirements},
            '.gitignore': {'required': False, 'validator': self._validate_gitignore},
            'LICENSE': {'required': False, 'validator': None},
        }
        
        scripts_files = {
            'scripts/commit_helper.py': {'required': True, 'validator': self._validate_python_script},
            'scripts/visualization/tdd_gantt_tracker.py': {'required': True, 'validator': self._validate_python_script},
            'scripts/test_setup.py': {'required': True, 'validator': self._validate_python_script},
        }
        
        docs_files = {
            'docs/index.md': {'required': True, 'validator': self._validate_markdown},
            'docs/_config.yml': {'required': True, 'validator': self._validate_jekyll_config},
            'docs/Gemfile': {'required': True, 'validator': self._validate_gemfile},
            'docs/dashboard.html': {'required': True, 'validator': self._validate_html},
            'docs/TDD_COMMIT_PATTERNS.md': {'required': True, 'validator': self._validate_markdown},
        }
        
        workflow_files = {
            '.github/workflows/update-tdd-gantt.yml': {'required': True, 'validator': self._validate_github_workflow},
        }
        
        all_files = {**critical_files, **scripts_files, **docs_files, **workflow_files}
        
        files_score = 0
        total_files = len(all_files)
        validation_results = {}
        
        for file_path, config in all_files.items():
            full_path = self.project_root / file_path
            if full_path.exists() and full_path.is_file():
                files_score += 1
                
                # Run validator if available
                if config.get('validator'):
                    try:
                        validation_result = config['validator'](full_path)
                        validation_results[file_path] = validation_result
                        
                        if validation_result.get('valid', True):
                            self.log_finding('SUCCESS', 'FILES', 
                                           f"File valid: {file_path}",
                                           validation_result)
                        else:
                            self.log_finding('WARNING', 'FILES',
                                           f"File has issues: {file_path}",
                                           validation_result)
                    except Exception as e:
                        self.log_finding('ERROR', 'FILES',
                                       f"Failed to validate {file_path}: {str(e)}")
                else:
                    self.log_finding('SUCCESS', 'FILES', f"File exists: {file_path}")
                    
            else:
                level = 'ERROR' if config['required'] else 'WARNING'
                self.log_finding(level, 'FILES', 
                               f"Missing file: {file_path}",
                               {'required': config['required']})
        
        files_percentage = (files_score / total_files) * 100
        self.metrics['core_files_score'] = files_percentage
        
        return {
            'score': files_percentage,
            'files_found': files_score,
            'total_expected': total_files,
            'validation_results': validation_results
        }
    
    def audit_naming_conventions(self) -> Dict[str, Any]:
        """Audit naming conventions across the project."""
        print("\n📝 AUDITING NAMING CONVENTIONS")
        print("=" * 50)
        
        naming_issues = []
        
        # Python files should follow snake_case
        for py_file in self.project_root.rglob("*.py"):
            if not re.match(r'^[a-z_][a-z0-9_]*\.py$', py_file.name):
                naming_issues.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'issue': 'Python file should use snake_case naming',
                    'current': py_file.name
                })
        
        # YAML/YML files consistency
        yml_files = list(self.project_root.rglob("*.yml")) + list(self.project_root.rglob("*.yaml"))
        if len(yml_files) > 0:
            extensions = set(f.suffix for f in yml_files)
            if len(extensions) > 1:
                naming_issues.append({
                    'issue': 'Inconsistent YAML file extensions',
                    'extensions': list(extensions)
                })
        
        # Markdown files should be meaningful
        for md_file in self.project_root.rglob("*.md"):
            if re.match(r'^[A-Z_]+\.md$', md_file.name):  # ALL CAPS is good
                continue
            if not re.match(r'^[a-z0-9_-]+\.md$', md_file.name):
                naming_issues.append({
                    'file': str(md_file.relative_to(self.project_root)),
                    'issue': 'Markdown file should use lowercase with dashes/underscores',
                    'current': md_file.name
                })
        
        if naming_issues:
            for issue in naming_issues:
                self.log_finding('WARNING', 'NAMING', 
                               issue.get('issue', 'Naming convention issue'),
                               issue)
        else:
            self.log_finding('SUCCESS', 'NAMING', "All files follow naming conventions")
        
        naming_score = max(0, 100 - (len(naming_issues) * 10))  # -10 points per issue
        self.metrics['naming_conventions_score'] = naming_score
        
        return {
            'score': naming_score,
            'issues': naming_issues,
            'total_issues': len(naming_issues)
        }
    
    def audit_documentation_quality(self) -> Dict[str, Any]:
        """Audit documentation completeness and quality."""
        print("\n📚 AUDITING DOCUMENTATION QUALITY")
        print("=" * 50)
        
        doc_metrics = {}
        
        # Check README.md quality
        readme_path = self.project_root / 'README.md'
        if readme_path.exists():
            content = readme_path.read_text()
            doc_metrics['readme'] = {
                'length': len(content),
                'sections': len(re.findall(r'^#+\s', content, re.MULTILINE)),
                'code_blocks': len(re.findall(r'```', content)),
                'links': len(re.findall(r'\[.*?\]\(.*?\)', content)),
                'has_badges': bool(re.search(r'!\[.*?\]\(.*?\)', content)),
                'has_toc': 'Table of Contents' in content or '## Contents' in content
            }
            
            # Quality scoring
            readme_score = 0
            if doc_metrics['readme']['length'] > 1000:
                readme_score += 20
                self.log_finding('SUCCESS', 'DOCS', "README has good length")
            else:
                self.log_finding('WARNING', 'DOCS', "README might be too short")
            
            if doc_metrics['readme']['sections'] >= 8:
                readme_score += 20
                self.log_finding('SUCCESS', 'DOCS', "README has good section structure")
            
            if doc_metrics['readme']['code_blocks'] >= 5:
                readme_score += 20
                self.log_finding('SUCCESS', 'DOCS', "README has adequate code examples")
            
            if doc_metrics['readme']['has_badges']:
                readme_score += 20
                self.log_finding('SUCCESS', 'DOCS', "README has status badges")
            
            if doc_metrics['readme']['links'] >= 10:
                readme_score += 20
                self.log_finding('SUCCESS', 'DOCS', "README has good link coverage")
            
        else:
            readme_score = 0
            self.log_finding('ERROR', 'DOCS', "README.md missing")
        
        # Check for additional documentation
        doc_files = list(self.project_root.glob('docs/*.md')) + list(self.project_root.glob('*.md'))
        doc_count = len([f for f in doc_files if f.name != 'README.md'])
        
        if doc_count >= 3:
            self.log_finding('SUCCESS', 'DOCS', f"Good documentation coverage: {doc_count} files")
            doc_coverage_score = 100
        elif doc_count >= 1:
            self.log_finding('WARNING', 'DOCS', f"Limited documentation: {doc_count} files")
            doc_coverage_score = 60
        else:
            self.log_finding('ERROR', 'DOCS', "No additional documentation found")
            doc_coverage_score = 0
        
        overall_doc_score = (readme_score + doc_coverage_score) / 2
        self.metrics['documentation_score'] = overall_doc_score
        
        return {
            'score': overall_doc_score,
            'readme_score': readme_score,
            'doc_coverage_score': doc_coverage_score,
            'metrics': doc_metrics,
            'documentation_files': doc_count
        }
    
    def audit_dependency_management(self) -> Dict[str, Any]:
        """Audit dependency management setup."""
        print("\n📦 AUDITING DEPENDENCY MANAGEMENT")
        print("=" * 50)
        
        dep_findings = {}
        
        # Check Poetry setup
        pyproject_path = self.project_root / 'pyproject.toml'
        if pyproject_path.exists():
            try:
                import toml
                config = toml.load(pyproject_path)
                
                # Validate Poetry configuration
                poetry_config = config.get('tool', {}).get('poetry', {})
                if poetry_config:
                    dep_findings['poetry'] = {
                        'configured': True,
                        'name': poetry_config.get('name'),
                        'version': poetry_config.get('version'),
                        'dependencies_count': len(poetry_config.get('dependencies', {})),
                        'dev_dependencies_count': len(config.get('tool', {}).get('poetry', {}).get('group', {}).get('dev', {}).get('dependencies', {}))
                    }
                    self.log_finding('SUCCESS', 'DEPS', "Poetry properly configured")
                else:
                    self.log_finding('ERROR', 'DEPS', "pyproject.toml missing Poetry configuration")
                    
            except ImportError:
                self.log_finding('WARNING', 'DEPS', "toml module not available for validation")
            except Exception as e:
                self.log_finding('ERROR', 'DEPS', f"Error parsing pyproject.toml: {e}")
        
        # Check requirements.txt fallback
        req_path = self.project_root / 'requirements.txt'
        if req_path.exists():
            requirements = req_path.read_text().strip().split('\n')
            req_count = len([r for r in requirements if r and not r.startswith('#')])
            dep_findings['requirements_txt'] = {
                'exists': True,
                'dependencies_count': req_count
            }
            self.log_finding('SUCCESS', 'DEPS', f"requirements.txt fallback available ({req_count} deps)")
        else:
            self.log_finding('WARNING', 'DEPS', "No requirements.txt fallback")
        
        # Check for lock files
        if (self.project_root / 'poetry.lock').exists():
            self.log_finding('SUCCESS', 'DEPS', "Poetry lock file present")
            dep_findings['has_lock_file'] = True
        else:
            self.log_finding('WARNING', 'DEPS', "No Poetry lock file (run poetry install)")
            dep_findings['has_lock_file'] = False
        
        # Score dependency management
        dep_score = 0
        if dep_findings.get('poetry', {}).get('configured'):
            dep_score += 50
        if dep_findings.get('requirements_txt', {}).get('exists'):
            dep_score += 30
        if dep_findings.get('has_lock_file'):
            dep_score += 20
        
        self.metrics['dependency_management_score'] = dep_score
        
        return {
            'score': dep_score,
            'findings': dep_findings
        }
    
    def _validate_pyproject(self, file_path: Path) -> Dict[str, Any]:
        """Validate pyproject.toml file."""
        try:
            import toml
            config = toml.load(file_path)
            
            # Check required sections
            required_sections = ['tool.poetry', 'tool.poetry.dependencies', 'build-system']
            missing_sections = []
            
            for section in required_sections:
                keys = section.split('.')
                current = config
                for key in keys:
                    if key not in current:
                        missing_sections.append(section)
                        break
                    current = current[key]
            
            return {
                'valid': len(missing_sections) == 0,
                'missing_sections': missing_sections,
                'has_poetry': 'tool' in config and 'poetry' in config['tool'],
                'dependency_count': len(config.get('tool', {}).get('poetry', {}).get('dependencies', {}))
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _validate_readme(self, file_path: Path) -> Dict[str, Any]:
        """Validate README.md file."""
        content = file_path.read_text()
        return {
            'valid': len(content) > 500,
            'length': len(content),
            'has_title': content.startswith('#'),
            'sections': len(re.findall(r'^#+\s', content, re.MULTILINE)),
            'code_blocks': len(re.findall(r'```', content))
        }
    
    def _validate_requirements(self, file_path: Path) -> Dict[str, Any]:
        """Validate requirements.txt file."""
        content = file_path.read_text().strip()
        lines = [line for line in content.split('\n') if line and not line.startswith('#')]
        return {
            'valid': len(lines) > 0,
            'dependency_count': len(lines),
            'has_versions': any('>=' in line or '==' in line for line in lines)
        }
    
    def _validate_python_script(self, file_path: Path) -> Dict[str, Any]:
        """Validate Python script."""
        try:
            content = file_path.read_text()
            
            # Check for shebang
            has_shebang = content.startswith('#!')
            
            # Check for docstring
            has_docstring = '"""' in content and content.count('"""') >= 2
            
            # Basic syntax check
            try:
                compile(content, str(file_path), 'exec')
                syntax_valid = True
            except SyntaxError:
                syntax_valid = False
            
            return {
                'valid': syntax_valid,
                'has_shebang': has_shebang,
                'has_docstring': has_docstring,
                'length': len(content),
                'lines': len(content.split('\n'))
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _validate_markdown(self, file_path: Path) -> Dict[str, Any]:
        """Validate Markdown file."""
        content = file_path.read_text()
        return {
            'valid': len(content) > 100,
            'length': len(content),
            'has_headers': bool(re.search(r'^#+\s', content, re.MULTILINE)),
            'has_code': '```' in content
        }
    
    def _validate_html(self, file_path: Path) -> Dict[str, Any]:
        """Validate HTML file."""
        content = file_path.read_text()
        return {
            'valid': '<html' in content.lower() and '</html>' in content.lower(),
            'length': len(content),
            'has_doctype': content.lower().startswith('<!doctype'),
            'has_css': '<style' in content or 'href=' in content,
            'has_js': '<script' in content
        }
    
    def _validate_jekyll_config(self, file_path: Path) -> Dict[str, Any]:
        """Validate Jekyll _config.yml file."""
        try:
            content = file_path.read_text()
            config = yaml.safe_load(content)
            
            required_keys = ['title', 'description']
            has_required = all(key in config for key in required_keys)
            
            return {
                'valid': has_required,
                'has_title': 'title' in config,
                'has_description': 'description' in config,
                'key_count': len(config)
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _validate_gemfile(self, file_path: Path) -> Dict[str, Any]:
        """Validate Jekyll Gemfile."""
        content = file_path.read_text()
        return {
            'valid': 'gem ' in content,
            'has_github_pages': 'github-pages' in content,
            'has_jekyll': 'jekyll' in content,
            'gem_count': len(re.findall(r'gem\s+["\']', content))
        }
    
    def _validate_github_workflow(self, file_path: Path) -> Dict[str, Any]:
        """Validate GitHub Actions workflow."""
        try:
            content = file_path.read_text()
            config = yaml.safe_load(content)
            
            has_name = 'name' in config
            has_on = 'on' in config
            has_jobs = 'jobs' in config
            
            return {
                'valid': has_name and has_on and has_jobs,
                'has_name': has_name,
                'has_triggers': has_on,
                'has_jobs': has_jobs,
                'job_count': len(config.get('jobs', {}))
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _validate_gitignore(self, file_path: Path) -> Dict[str, Any]:
        """Validate .gitignore file."""
        content = file_path.read_text()
        patterns = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        
        important_patterns = [
            '__pycache__', '.pyc', 'node_modules', '.env', '*.log', '.DS_Store'
        ]
        has_important = sum(1 for pattern in important_patterns 
                           if any(pattern in p for p in patterns))
        
        return {
            'valid': len(patterns) > 5,
            'pattern_count': len(patterns),
            'important_patterns_covered': has_important,
            'coverage_score': (has_important / len(important_patterns)) * 100
        }
    
    def generate_architecture_report(self) -> Dict[str, Any]:
        """Generate comprehensive architecture audit report."""
        print("\n📊 GENERATING ARCHITECTURE REPORT")
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
            'recommendations': self._generate_recommendations()
        }
        
        # Console summary
        grade_colors = {
            'A+': '🟢', 'A': '🟢', 'B+': '🔵', 'B': '🔵', 
            'C+': '🟡', 'C': '🟡', 'D': '🟠', 'F': '🔴'
        }
        grade_color = grade_colors.get(report['grade'], '⚪')
        
        print(f"\n{grade_color} OVERALL ARCHITECTURE GRADE: {report['grade']} ({overall_score:.1f}%)")
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
        warnings = [f for f in self.findings if f['level'] == 'WARNING']
        
        if errors:
            recommendations.append("🔥 CRITICAL: Fix all ERROR level issues before production use")
        
        if len(warnings) > 5:
            recommendations.append("⚠️ HIGH: Address WARNING level issues to improve quality")
        
        if self.metrics.get('documentation_score', 0) < 80:
            recommendations.append("📚 MEDIUM: Improve documentation coverage and quality")
        
        if self.metrics.get('dependency_management_score', 0) < 90:
            recommendations.append("📦 MEDIUM: Complete dependency management setup")
        
        if not recommendations:
            recommendations.append("🎉 Excellent! Architecture follows best practices")
        
        return recommendations


def main():
    """Main audit execution."""
    parser = argparse.ArgumentParser(description="🏗️ TDD Template Architecture Audit")
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output with detailed findings')
    parser.add_argument('--report', choices=['console', 'json', 'both'], 
                       default='console', help='Report output format')
    parser.add_argument('--output', '-o', help='Output file for JSON report')
    
    args = parser.parse_args()
    
    print("🏗️ TDD PROJECT TEMPLATE - ARCHITECTURE AUDIT")
    print("=" * 60)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Project: {Path.cwd()}")
    
    auditor = ArchitectureAuditor(verbose=args.verbose)
    
    try:
        # Run all audits
        structure_results = auditor.audit_directory_structure()
        files_results = auditor.audit_core_files()
        naming_results = auditor.audit_naming_conventions()
        docs_results = auditor.audit_documentation_quality()
        deps_results = auditor.audit_dependency_management()
        
        # Generate final report
        report = auditor.generate_architecture_report()
        
        # Output report
        if args.report in ['json', 'both']:
            output_file = args.output or f'architecture_audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 JSON report saved: {output_file}")
        
        # Return exit code based on grade
        grade_scores = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C+': 1, 'C': 1, 'D': 2, 'F': 3}
        return grade_scores.get(report['grade'], 3)
        
    except KeyboardInterrupt:
        print("\n❌ Audit cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Audit failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())