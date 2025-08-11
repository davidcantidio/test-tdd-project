#!/usr/bin/env python3
"""
🔍 TDD Project Template - ETL Debrito Feature Parity Comparison
============================================================

Auditoria comparativa detalhada entre o template TDD e o projeto ETL Debrito,
verificando feature parity, padrões implementados e qualidade da adaptação.

Uso:
    python scripts/audit_etl_comparison.py
    python scripts/audit_etl_comparison.py --verbose --deep-analysis
"""

import argparse
import json
import os
import sys
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime


class ETLComparisonAuditor:
    """Auditor de comparação detalhada com ETL Debrito."""
    
    def __init__(self, verbose: bool = False, deep_analysis: bool = False):
        self.verbose = verbose
        self.deep_analysis = deep_analysis
        self.project_root = Path.cwd()
        self.etl_root = Path.cwd().parent.parent  # Assume ETL Debrito is in parent
        self.findings = []
        self.metrics = {}
        
        # ETL Debrito reference features
        self.etl_features = {
            'analytics_engine': {
                'gantt_tracker': 'Plotly-based Gantt chart generation',
                'commit_parsing': 'Parse [EPIC-X] commit patterns',
                'progress_tracking': 'Real-time progress analytics',
                'time_accuracy': 'Estimated vs actual time tracking',
                'performance_grading': 'A/B/C grading system'
            },
            'github_integration': {
                'pages_deployment': 'Jekyll + GitHub Pages automation',
                'workflow_automation': 'Auto-update charts on commits',
                'issue_linking': 'Epic to GitHub issue integration',
                'milestone_tracking': 'Visual milestone representation'
            },
            'documentation_system': {
                'professional_styling': 'Gradient-based visual design',
                'interactive_dashboards': 'HTML dashboards with Plotly',
                'comprehensive_readme': 'Detailed setup and usage guides',
                'troubleshooting_docs': '404 resolution and error handling'
            },
            'dependency_management': {
                'poetry_integration': 'pyproject.toml with Poetry',
                'graceful_fallbacks': 'requirements.txt backup',
                'dependency_caching': 'GitHub Actions caching',
                'version_pinning': 'Locked dependency versions'
            },
            'architecture_patterns': {
                'modular_structure': 'Clean separation of concerns',
                'configuration_management': 'Environment-based config',
                'error_handling': 'Comprehensive error management',
                'logging_system': 'Structured logging implementation'
            }
        }
        
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
    
    def compare_analytics_engine(self) -> Dict[str, Any]:
        """Compare analytics and visualization capabilities."""
        print("\n📊 COMPARING ANALYTICS ENGINE")
        print("=" * 50)
        
        analytics_comparison = {
            'gantt_implementation': {},
            'commit_parsing': {},
            'visualization_quality': {},
            'data_processing': {}
        }
        
        parity_score = 0
        
        # Check Gantt tracker implementation
        tdd_gantt_path = self.project_root / 'scripts' / 'visualization' / 'tdd_gantt_tracker.py'
        etl_gantt_path = self.etl_root / 'gantt_tracker.py'
        
        if tdd_gantt_path.exists() and etl_gantt_path.exists():
            try:
                # Read both implementations
                tdd_content = tdd_gantt_path.read_text()
                etl_content = etl_gantt_path.read_text()
                
                # Compare key features
                tdd_features = {
                    'plotly_usage': 'plotly.graph_objects' in tdd_content,
                    'dual_bar_charts': 'add_trace' in tdd_content and 'name=' in tdd_content,
                    'interactive_html': 'to_html' in tdd_content,
                    'commit_parsing': 'CommitTracker' in tdd_content or 'parse' in tdd_content,
                    'time_tracking': 'estimated' in tdd_content and 'actual' in tdd_content
                }
                
                etl_features = {
                    'plotly_usage': 'plotly.graph_objects' in etl_content,
                    'dual_bar_charts': 'add_trace' in etl_content and 'name=' in etl_content,
                    'interactive_html': 'to_html' in etl_content,
                    'commit_parsing': 'CommitTracker' in etl_content or 'parse' in etl_content,
                    'time_tracking': 'estimated' in etl_content and 'actual' in etl_content
                }
                
                # Calculate feature parity
                matching_features = sum(1 for feature in tdd_features 
                                      if tdd_features[feature] == etl_features[feature] and tdd_features[feature])
                total_features = len(tdd_features)
                feature_parity = (matching_features / total_features) * 100
                
                if feature_parity >= 80:
                    parity_score += 30
                    self.log_finding('SUCCESS', 'ANALYTICS', 
                                   f"Excellent Gantt implementation parity ({feature_parity:.1f}%)")
                elif feature_parity >= 60:
                    parity_score += 20
                    self.log_finding('WARNING', 'ANALYTICS',
                                   f"Good Gantt implementation parity ({feature_parity:.1f}%)")
                else:
                    self.log_finding('ERROR', 'ANALYTICS',
                                   f"Poor Gantt implementation parity ({feature_parity:.1f}%)")
                
                analytics_comparison['gantt_implementation'] = {
                    'tdd_features': tdd_features,
                    'etl_features': etl_features,
                    'parity_percentage': feature_parity
                }
                
                # Compare code complexity and quality
                tdd_lines = len(tdd_content.split('\n'))
                etl_lines = len(etl_content.split('\n'))
                
                if abs(tdd_lines - etl_lines) / max(tdd_lines, etl_lines) < 0.2:
                    parity_score += 10
                    self.log_finding('SUCCESS', 'ANALYTICS', "Similar implementation complexity")
                
            except Exception as e:
                self.log_finding('ERROR', 'ANALYTICS', f"Failed to compare Gantt implementations: {str(e)}")
                
        elif tdd_gantt_path.exists():
            parity_score += 15
            self.log_finding('WARNING', 'ANALYTICS', "TDD Gantt exists but ETL reference not found")
        else:
            self.log_finding('ERROR', 'ANALYTICS', "TDD Gantt implementation missing")
        
        # Check commit parsing capabilities
        tdd_commit_helper = self.project_root / 'scripts' / 'commit_helper.py'
        
        if tdd_commit_helper.exists():
            content = tdd_commit_helper.read_text()
            
            # Check for TDD-specific adaptations
            tdd_adaptations = {
                'tdd_phases': all(phase in content.lower() for phase in ['red', 'green', 'refactor', 'analysis']),
                'epic_pattern': '[EPIC-' in content,
                'task_pattern': 'Task' in content,
                'time_pattern': 'min]' in content,
                'validation': 'validate' in content.lower()
            }
            
            adaptation_score = sum(1 for feature in tdd_adaptations.values() if feature)
            if adaptation_score >= 4:
                parity_score += 25
                self.log_finding('SUCCESS', 'ANALYTICS', "Excellent TDD pattern adaptation")
            elif adaptation_score >= 3:
                parity_score += 15
                self.log_finding('WARNING', 'ANALYTICS', "Good TDD pattern adaptation")
            else:
                self.log_finding('ERROR', 'ANALYTICS', "Poor TDD pattern adaptation")
                
            analytics_comparison['commit_parsing'] = {
                'tdd_adaptations': tdd_adaptations,
                'adaptation_score': adaptation_score
            }
        else:
            self.log_finding('ERROR', 'ANALYTICS', "Commit helper missing")
        
        # Check visualization quality
        dashboard_path = self.project_root / 'docs' / 'dashboard.html'
        if dashboard_path.exists():
            content = dashboard_path.read_text()
            
            visual_features = {
                'plotly_integration': 'plotly' in content.lower(),
                'professional_styling': 'gradient' in content.lower() or 'style' in content,
                'responsive_design': 'responsive' in content or 'mobile' in content,
                'interactive_elements': 'onclick' in content or 'addEventListener' in content,
                'tdd_branding': 'tdd' in content.lower()
            }
            
            visual_score = sum(1 for feature in visual_features.values() if feature)
            if visual_score >= 4:
                parity_score += 20
                self.log_finding('SUCCESS', 'ANALYTICS', "Excellent dashboard quality")
            elif visual_score >= 2:
                parity_score += 10
                self.log_finding('WARNING', 'ANALYTICS', "Basic dashboard quality")
            
            analytics_comparison['visualization_quality'] = {
                'visual_features': visual_features,
                'visual_score': visual_score
            }
        else:
            self.log_finding('WARNING', 'ANALYTICS', "Dashboard HTML missing")
        
        self.metrics['analytics_parity_score'] = parity_score
        
        return {
            'score': parity_score,
            'comparison': analytics_comparison
        }
    
    def compare_github_integration(self) -> Dict[str, Any]:
        """Compare GitHub integration and automation."""
        print("\n🤖 COMPARING GITHUB INTEGRATION")
        print("=" * 50)
        
        github_comparison = {
            'workflow_quality': {},
            'pages_setup': {},
            'automation_features': {}
        }
        
        integration_score = 0
        
        # Compare GitHub Actions workflows
        tdd_workflow = self.project_root / '.github' / 'workflows' / 'update-tdd-gantt.yml'
        etl_workflow = self.etl_root / '.github' / 'workflows' / 'update-gantt.yml'
        
        if tdd_workflow.exists():
            try:
                import yaml
                with open(tdd_workflow, 'r') as f:
                    tdd_config = yaml.safe_load(f)
                
                # Check workflow features
                workflow_features = {
                    'automatic_triggers': 'push' in tdd_config.get('on', {}),
                    'manual_dispatch': 'workflow_dispatch' in tdd_config.get('on', {}),
                    'dependency_caching': 'cache' in str(tdd_config).lower(),
                    'poetry_support': 'poetry' in str(tdd_config).lower(),
                    'pages_deployment': 'pages' in str(tdd_config).lower(),
                    'artifact_upload': 'upload' in str(tdd_config).lower()
                }
                
                feature_count = sum(1 for feature in workflow_features.values() if feature)
                if feature_count >= 5:
                    integration_score += 30
                    self.log_finding('SUCCESS', 'GITHUB', f"Comprehensive workflow ({feature_count}/6 features)")
                elif feature_count >= 3:
                    integration_score += 20
                    self.log_finding('WARNING', 'GITHUB', f"Basic workflow ({feature_count}/6 features)")
                else:
                    self.log_finding('ERROR', 'GITHUB', f"Limited workflow ({feature_count}/6 features)")
                
                github_comparison['workflow_quality'] = {
                    'features': workflow_features,
                    'feature_count': feature_count
                }
                
                # Compare with ETL workflow if available
                if etl_workflow.exists():
                    try:
                        with open(etl_workflow, 'r') as f:
                            etl_config = yaml.safe_load(f)
                        
                        # Compare job structures
                        tdd_jobs = len(tdd_config.get('jobs', {}))
                        etl_jobs = len(etl_config.get('jobs', {}))
                        
                        if tdd_jobs == etl_jobs:
                            integration_score += 10
                            self.log_finding('SUCCESS', 'GITHUB', "Workflow structure matches ETL pattern")
                        
                    except Exception:
                        pass
                        
            except Exception as e:
                self.log_finding('ERROR', 'GITHUB', f"Failed to analyze workflow: {str(e)}")
        else:
            self.log_finding('ERROR', 'GITHUB', "GitHub Actions workflow missing")
        
        # Check Jekyll and Pages setup
        jekyll_files = {
            'docs/_config.yml': 'Jekyll configuration',
            'docs/Gemfile': 'Ruby dependencies',
            'docs/index.md': 'Main page content'
        }
        
        jekyll_score = 0
        for jekyll_file, description in jekyll_files.items():
            file_path = self.project_root / jekyll_file
            if file_path.exists():
                jekyll_score += 1
                
                if jekyll_file.endswith('_config.yml'):
                    # Check Jekyll configuration quality
                    try:
                        import yaml
                        with open(file_path, 'r') as f:
                            config = yaml.safe_load(f)
                        
                        config_features = {
                            'has_title': 'title' in config,
                            'has_description': 'description' in config,
                            'has_theme': 'theme' in config or 'remote_theme' in config,
                            'has_plugins': 'plugins' in config,
                            'tdd_specific': 'tdd' in str(config).lower()
                        }
                        
                        config_quality = sum(1 for feature in config_features.values() if feature)
                        if config_quality >= 4:
                            integration_score += 15
                            self.log_finding('SUCCESS', 'GITHUB', "Excellent Jekyll configuration")
                        elif config_quality >= 2:
                            integration_score += 10
                            
                    except Exception:
                        pass
                        
        if jekyll_score >= 3:
            integration_score += 20
            self.log_finding('SUCCESS', 'GITHUB', f"Complete Jekyll setup ({jekyll_score}/3 files)")
        elif jekyll_score >= 2:
            integration_score += 15
            self.log_finding('WARNING', 'GITHUB', f"Partial Jekyll setup ({jekyll_score}/3 files)")
        else:
            self.log_finding('ERROR', 'GITHUB', f"Incomplete Jekyll setup ({jekyll_score}/3 files)")
        
        github_comparison['pages_setup'] = {
            'jekyll_files_found': jekyll_score,
            'total_expected': len(jekyll_files)
        }
        
        # Check automation sophistication
        automation_features = []
        
        # Check for commit pattern automation
        if tdd_workflow.exists():
            workflow_content = tdd_workflow.read_text()
            if 'EPIC-' in workflow_content:
                automation_features.append('commit_pattern_detection')
                self.log_finding('SUCCESS', 'GITHUB', "Commit pattern automation detected")
        
        # Check for automated chart generation
        if (self.project_root / 'scripts' / 'visualization').exists():
            automation_features.append('chart_generation')
            
        # Check for deployment automation
        if 'deploy' in str(tdd_config).lower() if tdd_workflow.exists() else False:
            automation_features.append('deployment_automation')
        
        automation_score = len(automation_features) * 10
        integration_score += automation_score
        
        github_comparison['automation_features'] = {
            'features': automation_features,
            'count': len(automation_features)
        }
        
        self.metrics['github_integration_score'] = min(100, integration_score)
        
        return {
            'score': min(100, integration_score),
            'comparison': github_comparison
        }
    
    def compare_documentation_system(self) -> Dict[str, Any]:
        """Compare documentation quality and completeness."""
        print("\n📚 COMPARING DOCUMENTATION SYSTEM")  
        print("=" * 50)
        
        docs_comparison = {
            'readme_quality': {},
            'comprehensive_docs': {},
            'visual_presentation': {}
        }
        
        docs_score = 0
        
        # Compare README quality with ETL Debrito patterns
        readme_path = self.project_root / 'README.md'
        etl_readme_path = self.etl_root / 'CLAUDE.md'  # ETL Debrito uses CLAUDE.md as main doc
        
        if readme_path.exists():
            content = readme_path.read_text()
            
            # Check for ETL Debrito documentation patterns
            etl_patterns = {
                'structured_headers': len(re.findall(r'^#{1,3}\s', content, re.MULTILINE)) >= 10,
                'emoji_usage': len(re.findall(r'[🎯📊🚀✨🧪📈🤖🏗️📋]', content)) >= 10,
                'code_examples': content.count('```') >= 10,
                'badges': content.count('![') >= 3,
                'feature_lists': '- **' in content or '* **' in content,
                'quick_start': 'quick start' in content.lower() or 'getting started' in content.lower(),
                'detailed_sections': len(content.split()) >= 1000,
                'link_navigation': len(re.findall(r'\[.*?\]\(.*?\)', content)) >= 10
            }
            
            pattern_score = sum(1 for pattern in etl_patterns.values() if pattern)
            if pattern_score >= 7:
                docs_score += 30
                self.log_finding('SUCCESS', 'DOCS', f"Excellent README following ETL patterns ({pattern_score}/8)")
            elif pattern_score >= 5:
                docs_score += 20
                self.log_finding('WARNING', 'DOCS', f"Good README following ETL patterns ({pattern_score}/8)")
            else:
                self.log_finding('ERROR', 'DOCS', f"Poor README adaptation ({pattern_score}/8)")
            
            docs_comparison['readme_quality'] = {
                'etl_patterns': etl_patterns,
                'pattern_score': pattern_score
            }
            
            # Check for TDD-specific adaptations
            tdd_adaptations = {
                'tdd_methodology': 'tdd' in content.lower() and 'test-driven' in content.lower(),
                'red_green_refactor': all(phase in content.lower() for phase in ['red', 'green', 'refactor']),
                'commit_patterns': '[EPIC-' in content,
                'analytics_mention': 'gantt' in content.lower() or 'analytics' in content.lower(),
                'github_pages': 'github pages' in content.lower() or 'pages' in content
            }
            
            adaptation_score = sum(1 for adaptation in tdd_adaptations.values() if adaptation)
            if adaptation_score >= 4:
                docs_score += 25
                self.log_finding('SUCCESS', 'DOCS', f"Excellent TDD adaptation ({adaptation_score}/5)")
            elif adaptation_score >= 2:
                docs_score += 15
                self.log_finding('WARNING', 'DOCS', f"Basic TDD adaptation ({adaptation_score}/5)")
            
        else:
            self.log_finding('CRITICAL', 'DOCS', "README.md missing")
        
        # Check comprehensive documentation coverage
        expected_docs = [
            'SETUP_GUIDE.md',
            'CUSTOMIZATION.md', 
            'TROUBLESHOOTING.md',
            'docs/TDD_COMMIT_PATTERNS.md',
            'docs/github_pages_setup_guide.md'
        ]
        
        found_docs = 0
        for doc_file in expected_docs:
            if (self.project_root / doc_file).exists():
                found_docs += 1
                
                # Check document quality
                content = (self.project_root / doc_file).read_text()
                if len(content) > 1000:  # Substantial content
                    docs_score += 5
                    self.log_finding('SUCCESS', 'DOCS', f"Comprehensive documentation: {doc_file}")
                elif len(content) > 200:
                    docs_score += 3
                    self.log_finding('WARNING', 'DOCS', f"Basic documentation: {doc_file}")
            else:
                self.log_finding('WARNING', 'DOCS', f"Missing documentation: {doc_file}")
        
        doc_coverage = (found_docs / len(expected_docs)) * 100
        if doc_coverage >= 80:
            docs_score += 20
            self.log_finding('SUCCESS', 'DOCS', f"Excellent doc coverage ({doc_coverage:.1f}%)")
        elif doc_coverage >= 60:
            docs_score += 15
            self.log_finding('WARNING', 'DOCS', f"Good doc coverage ({doc_coverage:.1f}%)")
        elif doc_coverage >= 40:
            docs_score += 10
            self.log_finding('WARNING', 'DOCS', f"Basic doc coverage ({doc_coverage:.1f}%)")
        else:
            self.log_finding('ERROR', 'DOCS', f"Poor doc coverage ({doc_coverage:.1f}%)")
        
        docs_comparison['comprehensive_docs'] = {
            'found_docs': found_docs,
            'total_expected': len(expected_docs),
            'coverage_percentage': doc_coverage
        }
        
        # Check visual presentation quality
        visual_elements = []
        
        # Check dashboard
        if (self.project_root / 'docs' / 'dashboard.html').exists():
            dashboard_content = (self.project_root / 'docs' / 'dashboard.html').read_text()
            
            if 'gradient' in dashboard_content.lower():
                visual_elements.append('gradient_styling')
            if 'plotly' in dashboard_content.lower():
                visual_elements.append('interactive_charts')
            if len(dashboard_content) > 5000:  # Substantial dashboard
                visual_elements.append('comprehensive_dashboard')
                
        # Check Jekyll styling
        if (self.project_root / 'docs' / '_sass').exists():
            visual_elements.append('custom_sass_styling')
            
        visual_score = len(visual_elements) * 10
        docs_score += visual_score
        
        if visual_score >= 30:
            self.log_finding('SUCCESS', 'DOCS', f"Excellent visual presentation ({len(visual_elements)} elements)")
        elif visual_score >= 20:
            self.log_finding('WARNING', 'DOCS', f"Good visual presentation ({len(visual_elements)} elements)")
        elif visual_score >= 10:
            self.log_finding('WARNING', 'DOCS', f"Basic visual presentation ({len(visual_elements)} elements)")
        else:
            self.log_finding('ERROR', 'DOCS', "Poor visual presentation")
        
        docs_comparison['visual_presentation'] = {
            'elements': visual_elements,
            'count': len(visual_elements)
        }
        
        self.metrics['documentation_parity_score'] = min(100, docs_score)
        
        return {
            'score': min(100, docs_score),
            'comparison': docs_comparison
        }
    
    def compare_dependency_architecture(self) -> Dict[str, Any]:
        """Compare dependency management and architecture."""
        print("\n📦 COMPARING DEPENDENCY & ARCHITECTURE")
        print("=" * 50)
        
        architecture_comparison = {
            'dependency_management': {},
            'project_structure': {},
            'configuration_patterns': {}
        }
        
        arch_score = 0
        
        # Compare dependency management
        tdd_pyproject = self.project_root / 'pyproject.toml'
        etl_pyproject = self.etl_root / 'pyproject.toml'
        
        if tdd_pyproject.exists():
            try:
                import toml
                tdd_config = toml.load(tdd_pyproject)
                
                # Check Poetry configuration similarity to ETL
                poetry_features = {
                    'has_poetry_config': 'tool' in tdd_config and 'poetry' in tdd_config['tool'],
                    'has_main_deps': bool(tdd_config.get('tool', {}).get('poetry', {}).get('dependencies')),
                    'has_dev_deps': bool(tdd_config.get('tool', {}).get('poetry', {}).get('group', {}).get('dev')),
                    'has_build_system': 'build-system' in tdd_config,
                    'has_tool_configs': len(tdd_config.get('tool', {})) >= 3  # poetry + other tools
                }
                
                # Check for ETL-inspired dependencies
                deps = tdd_config.get('tool', {}).get('poetry', {}).get('dependencies', {})
                etl_inspired_deps = {
                    'plotly': 'plotly' in deps,
                    'pandas': 'pandas' in deps,
                    'pyyaml': 'pyyaml' in deps or 'PyYAML' in deps,
                    'toml': 'toml' in deps
                }
                
                config_score = sum(1 for feature in poetry_features.values() if feature)
                deps_score = sum(1 for dep in etl_inspired_deps.values() if dep)
                
                if config_score >= 4:
                    arch_score += 25
                    self.log_finding('SUCCESS', 'ARCHITECTURE', f"Excellent Poetry configuration ({config_score}/5)")
                elif config_score >= 3:
                    arch_score += 15
                    
                if deps_score >= 3:
                    arch_score += 15
                    self.log_finding('SUCCESS', 'ARCHITECTURE', f"Good ETL-inspired dependencies ({deps_score}/4)")
                elif deps_score >= 2:
                    arch_score += 10
                
                architecture_comparison['dependency_management'] = {
                    'poetry_features': poetry_features,
                    'etl_inspired_deps': etl_inspired_deps,
                    'config_score': config_score,
                    'deps_score': deps_score
                }
                
            except Exception as e:
                self.log_finding('ERROR', 'ARCHITECTURE', f"Failed to analyze pyproject.toml: {str(e)}")
        else:
            self.log_finding('ERROR', 'ARCHITECTURE', "pyproject.toml missing")
        
        # Compare project structure patterns
        expected_structure = {
            'scripts/': 'Automation scripts',
            'scripts/visualization/': 'Analytics scripts',
            'docs/': 'Documentation',
            'epics/': 'Epic definitions',
            '.github/workflows/': 'CI/CD automation',
            'config/': 'Configuration files'
        }
        
        structure_score = 0
        found_dirs = 0
        
        for dir_path, description in expected_structure.items():
            full_path = self.project_root / dir_path.rstrip('/')
            if full_path.exists() and full_path.is_dir():
                found_dirs += 1
                structure_score += 15
                self.log_finding('SUCCESS', 'ARCHITECTURE', f"Directory exists: {dir_path}")
            else:
                self.log_finding('WARNING', 'ARCHITECTURE', f"Missing directory: {dir_path}")
        
        structure_coverage = (found_dirs / len(expected_structure)) * 100
        if structure_coverage >= 80:
            arch_score += 20
            self.log_finding('SUCCESS', 'ARCHITECTURE', f"Excellent structure coverage ({structure_coverage:.1f}%)")
        elif structure_coverage >= 60:
            arch_score += 15
            
        architecture_comparison['project_structure'] = {
            'found_dirs': found_dirs,
            'total_expected': len(expected_structure),
            'coverage_percentage': structure_coverage
        }
        
        # Compare configuration patterns
        config_patterns = {
            'env_examples': ['.env.example', 'config/environment/.env.example'],
            'yaml_configs': list(self.project_root.rglob('*.yml')) + list(self.project_root.rglob('*.yaml')),
            'json_configs': list(self.project_root.rglob('*.json')),
            'gitignore': '.gitignore'
        }
        
        config_score = 0
        
        # Check environment configuration
        env_found = any((self.project_root / env_file).exists() for env_file in config_patterns['env_examples'])
        if env_found:
            config_score += 20
            self.log_finding('SUCCESS', 'ARCHITECTURE', "Environment configuration template exists")
        
        # Check YAML configuration files
        if len(config_patterns['yaml_configs']) >= 2:
            config_score += 15
            self.log_finding('SUCCESS', 'ARCHITECTURE', f"Multiple YAML configs ({len(config_patterns['yaml_configs'])})")
        elif len(config_patterns['yaml_configs']) >= 1:
            config_score += 10
            
        # Check JSON configuration
        if len(config_patterns['json_configs']) >= 2:
            config_score += 10
            self.log_finding('SUCCESS', 'ARCHITECTURE', f"JSON configuration files ({len(config_patterns['json_configs'])})")
        
        # Check .gitignore
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            if '.env' in gitignore_content and '__pycache__' in gitignore_content:
                config_score += 15
                self.log_finding('SUCCESS', 'ARCHITECTURE', "Comprehensive .gitignore")
        
        arch_score += config_score
        
        architecture_comparison['configuration_patterns'] = {
            'has_env_examples': env_found,
            'yaml_config_count': len(config_patterns['yaml_configs']),
            'json_config_count': len(config_patterns['json_configs']),
            'has_gitignore': gitignore_path.exists()
        }
        
        self.metrics['architecture_parity_score'] = min(100, arch_score)
        
        return {
            'score': min(100, arch_score),
            'comparison': architecture_comparison
        }
    
    def generate_etl_comparison_report(self) -> Dict[str, Any]:
        """Generate comprehensive ETL Debrito comparison report."""
        print("\n📊 GENERATING ETL COMPARISON REPORT")
        print("=" * 50)
        
        # Calculate overall parity score
        parity_weights = {
            'analytics_parity_score': 0.35,      # Most important - core functionality
            'github_integration_score': 0.25,    # Important - automation
            'documentation_parity_score': 0.25,  # Important - user experience  
            'architecture_parity_score': 0.15    # Supporting - structure
        }
        
        overall_parity = 0
        for metric, weight in parity_weights.items():
            score = self.metrics.get(metric, 0)
            overall_parity += score * weight
        
        # Categorize findings
        critical_issues = [f for f in self.findings if f['level'] == 'CRITICAL']
        errors = [f for f in self.findings if f['level'] == 'ERROR']
        warnings = [f for f in self.findings if f['level'] == 'WARNING']
        successes = [f for f in self.findings if f['level'] == 'SUCCESS']
        
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'overall_parity_score': round(overall_parity, 2),
            'parity_grade': self._calculate_grade(overall_parity),
            'feature_parity_level': self._calculate_parity_level(overall_parity),
            'weighted_scores': {k: round(self.metrics.get(k, 0), 2) for k in parity_weights.keys()},
            'weights_used': parity_weights,
            'metrics': self.metrics,
            'summary': {
                'total_findings': len(self.findings),
                'critical_issues': len(critical_issues),
                'errors': len(errors),
                'warnings': len(warnings),
                'successes': len(successes)
            },
            'findings': self.findings,
            'etl_features_reference': self.etl_features,
            'recommendations': self._generate_parity_recommendations()
        }
        
        # Console summary
        grade_colors = {
            'A+': '🟢', 'A': '🟢', 'B+': '🔵', 'B': '🔵', 
            'C+': '🟡', 'C': '🟡', 'D': '🟠', 'F': '🔴'
        }
        parity_colors = {'EXCELLENT': '🟢', 'GOOD': '🔵', 'FAIR': '🟡', 'POOR': '🔴'}
        
        grade_color = grade_colors.get(report['parity_grade'], '⚪')
        parity_color = parity_colors.get(report['feature_parity_level'], '⚪')
        
        print(f"\n{grade_color} OVERALL PARITY GRADE: {report['parity_grade']} ({overall_parity:.1f}%)")
        print(f"{parity_color} FEATURE PARITY LEVEL: {report['feature_parity_level']}")
        print(f"📊 Component Parity Scores:")
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
    
    def _calculate_parity_level(self, score: float) -> str:
        """Calculate feature parity level."""
        if score >= 85: return 'EXCELLENT'
        elif score >= 70: return 'GOOD'
        elif score >= 55: return 'FAIR'
        else: return 'POOR'
    
    def _generate_parity_recommendations(self) -> List[str]:
        """Generate actionable parity improvement recommendations."""
        recommendations = []
        
        if self.metrics.get('analytics_parity_score', 0) < 70:
            recommendations.append("📊 HIGH: Improve Gantt chart implementation to match ETL Debrito patterns")
        
        if self.metrics.get('github_integration_score', 0) < 70:
            recommendations.append("🤖 HIGH: Complete GitHub Actions workflow and Pages automation")
        
        if self.metrics.get('documentation_parity_score', 0) < 70:
            recommendations.append("📚 MEDIUM: Enhance documentation coverage and visual presentation")
        
        if self.metrics.get('architecture_parity_score', 0) < 70:
            recommendations.append("🏗️ MEDIUM: Improve project structure and dependency management")
        
        critical_count = len([f for f in self.findings if f['level'] == 'CRITICAL'])
        if critical_count > 0:
            recommendations.append(f"🔥 CRITICAL: Fix {critical_count} critical parity gaps")
        
        error_count = len([f for f in self.findings if f['level'] == 'ERROR'])
        if error_count >= 5:
            recommendations.append(f"❌ HIGH: Address {error_count} error-level implementation gaps")
        
        # Overall parity assessment
        overall_parity = sum(self.metrics.get(k, 0) * w for k, w in {
            'analytics_parity_score': 0.35,
            'github_integration_score': 0.25,
            'documentation_parity_score': 0.25,
            'architecture_parity_score': 0.15
        }.items())
        
        if overall_parity < 50:
            recommendations.append("🚨 CRITICAL: Major rework needed to achieve ETL Debrito feature parity")
        elif overall_parity < 70:
            recommendations.append("⚠️ HIGH: Significant improvements needed for good feature parity")
        
        if not recommendations:
            recommendations.append("🎉 Excellent! Template achieves strong feature parity with ETL Debrito")
        
        return recommendations


def main():
    """Main ETL comparison audit execution."""
    parser = argparse.ArgumentParser(description="🔍 TDD Template ETL Debrito Comparison Audit")
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output with detailed findings')
    parser.add_argument('--deep-analysis', action='store_true',
                       help='Perform deep code analysis and comparison')
    parser.add_argument('--report', choices=['console', 'json', 'both'], 
                       default='console', help='Report output format')
    parser.add_argument('--output', '-o', help='Output file for JSON report')
    
    args = parser.parse_args()
    
    print("🔍 TDD PROJECT TEMPLATE - ETL DEBRITO FEATURE PARITY AUDIT")
    print("=" * 65)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 TDD Project: {Path.cwd()}")
    print(f"🔍 Deep Analysis: {'YES' if args.deep_analysis else 'NO'}")
    
    auditor = ETLComparisonAuditor(verbose=args.verbose, deep_analysis=args.deep_analysis)
    
    try:
        # Run all comparison audits
        analytics_results = auditor.compare_analytics_engine()
        github_results = auditor.compare_github_integration()
        docs_results = auditor.compare_documentation_system()
        arch_results = auditor.compare_dependency_architecture()
        
        # Generate final report
        report = auditor.generate_etl_comparison_report()
        
        # Output report
        if args.report in ['json', 'both']:
            output_file = args.output or f'etl_comparison_audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 JSON report saved: {output_file}")
        
        # Return exit code based on parity level
        parity_codes = {'EXCELLENT': 0, 'GOOD': 1, 'FAIR': 2, 'POOR': 3}
        return parity_codes.get(report['feature_parity_level'], 3)
        
    except KeyboardInterrupt:
        print("\n❌ ETL comparison audit cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ ETL comparison audit failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())