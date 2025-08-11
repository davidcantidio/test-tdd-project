#!/usr/bin/env python3
"""
👥 TDD Project Template - User Experience & Usability Audit
==========================================================

Auditoria rigorosa da experiência do usuário, documentação,
onboarding e usabilidade geral do template.

Uso:
    python scripts/audit_user_experience.py
    python scripts/audit_user_experience.py --verbose --comprehensive
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


class UserExperienceAuditor:
    """Auditor rigoroso da experiência do usuário do template."""
    
    def __init__(self, verbose: bool = False, comprehensive: bool = False):
        self.verbose = verbose
        self.comprehensive = comprehensive
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
    
    def audit_documentation_quality(self) -> Dict[str, Any]:
        """Audit documentation for clarity, completeness, and user-friendliness."""
        print("\n📚 AUDITING DOCUMENTATION QUALITY")
        print("=" * 50)
        
        doc_metrics = {
            'readme_analysis': {},
            'documentation_coverage': {},
            'examples_quality': {},
            'user_guidance': {}
        }
        
        # Analyze README.md
        readme_path = self.project_root / 'README.md'
        if readme_path.exists():
            content = readme_path.read_text()
            
            # Basic metrics
            word_count = len(content.split())
            section_count = len(re.findall(r'^#+\s', content, re.MULTILINE))
            code_block_count = len(re.findall(r'```', content))
            link_count = len(re.findall(r'\[.*?\]\(.*?\)', content))
            
            # User-focused content analysis
            has_quick_start = bool(re.search(r'quick\s*start|getting\s*started', content, re.IGNORECASE))
            has_examples = bool(re.search(r'example', content, re.IGNORECASE))
            has_installation = bool(re.search(r'install|setup', content, re.IGNORECASE))
            has_troubleshooting = bool(re.search(r'troubleshoot|problem|issue', content, re.IGNORECASE))
            has_contributing = bool(re.search(r'contribut', content, re.IGNORECASE))
            
            # Visual appeal
            has_badges = bool(re.search(r'!\[.*?\]\(.*?badge.*?\)', content))
            has_images = bool(re.search(r'!\[.*?\]\(.*?\.(png|jpg|gif|svg)', content))
            has_emojis = bool(re.search(r'[🎯📊🚀✨🧪📈🤖🏗️📋🔧]', content))
            
            doc_metrics['readme_analysis'] = {
                'word_count': word_count,
                'section_count': section_count,
                'code_blocks': code_block_count,
                'links': link_count,
                'has_quick_start': has_quick_start,
                'has_examples': has_examples,
                'has_installation': has_installation,
                'has_troubleshooting': has_troubleshooting,
                'has_contributing': has_contributing,
                'has_badges': has_badges,
                'has_images': has_images,
                'has_emojis': has_emojis
            }
            
            # Score README quality
            readme_score = 0
            if word_count >= 1000:
                readme_score += 20
                self.log_finding('SUCCESS', 'DOCS', f"README has good length ({word_count} words)")
            elif word_count >= 500:
                readme_score += 10
                self.log_finding('WARNING', 'DOCS', f"README could be more detailed ({word_count} words)")
            else:
                self.log_finding('ERROR', 'DOCS', f"README too short ({word_count} words)")
            
            if section_count >= 8:
                readme_score += 15
                self.log_finding('SUCCESS', 'DOCS', f"Good README structure ({section_count} sections)")
            elif section_count >= 5:
                readme_score += 10
            
            if has_quick_start and has_installation:
                readme_score += 20
                self.log_finding('SUCCESS', 'DOCS', "README has user onboarding sections")
            else:
                self.log_finding('WARNING', 'DOCS', "README missing quick start or installation guide")
            
            if code_block_count >= 5:
                readme_score += 15
                self.log_finding('SUCCESS', 'DOCS', f"Good code examples ({code_block_count} blocks)")
            
            if has_badges and has_emojis:
                readme_score += 10
                self.log_finding('SUCCESS', 'DOCS', "README has visual appeal (badges + emojis)")
            
            if has_troubleshooting or has_contributing:
                readme_score += 10
                self.log_finding('SUCCESS', 'DOCS', "README includes user support sections")
            
            if link_count >= 10:
                readme_score += 10
                self.log_finding('SUCCESS', 'DOCS', f"Good navigation ({link_count} links)")
            
            self.metrics['readme_score'] = readme_score
            
        else:
            self.log_finding('CRITICAL', 'DOCS', "README.md missing")
            self.metrics['readme_score'] = 0
        
        # Check additional documentation files
        doc_files = {
            'SETUP_GUIDE.md': 'Setup instructions',
            'CUSTOMIZATION.md': 'Customization guide', 
            'TROUBLESHOOTING.md': 'Troubleshooting help',
            'docs/TDD_COMMIT_PATTERNS.md': 'TDD workflow guide',
            'docs/github_pages_setup_guide.md': 'GitHub Pages setup'
        }
        
        doc_coverage_score = 0
        found_docs = 0
        
        for doc_file, description in doc_files.items():
            doc_path = self.project_root / doc_file
            if doc_path.exists():
                found_docs += 1
                content = doc_path.read_text()
                if len(content) > 500:
                    doc_coverage_score += 20
                    self.log_finding('SUCCESS', 'DOCS', f"Good documentation: {doc_file}")
                else:
                    doc_coverage_score += 10
                    self.log_finding('WARNING', 'DOCS', f"Minimal documentation: {doc_file}")
            else:
                self.log_finding('WARNING', 'DOCS', f"Missing documentation: {doc_file}")
        
        doc_metrics['documentation_coverage'] = {
            'total_expected': len(doc_files),
            'found_docs': found_docs,
            'coverage_percentage': (found_docs / len(doc_files)) * 100
        }
        
        self.metrics['documentation_coverage_score'] = doc_coverage_score
        
        return {
            'readme_score': self.metrics.get('readme_score', 0),
            'coverage_score': doc_coverage_score,
            'metrics': doc_metrics
        }
    
    def audit_onboarding_experience(self) -> Dict[str, Any]:
        """Audit the new user onboarding experience."""
        print("\n🚀 AUDITING ONBOARDING EXPERIENCE")
        print("=" * 50)
        
        onboarding_metrics = {
            'setup_clarity': {},
            'example_quality': {},
            'error_handling': {}
        }
        
        # Check setup scripts and guides
        setup_files = [
            'scripts/init_project.py',
            'scripts/test_setup.py', 
            'scripts/commit_helper.py'
        ]
        
        setup_score = 0
        working_setup_tools = 0
        
        for setup_file in setup_files:
            setup_path = self.project_root / setup_file
            if setup_path.exists():
                try:
                    # Test if script has help functionality
                    result = subprocess.run([
                        sys.executable, str(setup_path), '--help'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        working_setup_tools += 1
                        setup_score += 25
                        
                        # Check help quality
                        help_text = result.stdout
                        has_description = len(help_text.split('\n')[0]) > 20
                        has_examples = 'example' in help_text.lower()
                        has_options = '--' in help_text
                        
                        if has_description and has_options:
                            setup_score += 10
                            self.log_finding('SUCCESS', 'ONBOARDING', 
                                           f"Good help system: {setup_file}")
                        
                        if has_examples:
                            setup_score += 5
                        
                    else:
                        self.log_finding('WARNING', 'ONBOARDING',
                                       f"Setup tool help issues: {setup_file}")
                        
                except subprocess.TimeoutExpired:
                    self.log_finding('ERROR', 'ONBOARDING',
                                   f"Setup tool timeout: {setup_file}")
                except Exception as e:
                    self.log_finding('ERROR', 'ONBOARDING',
                                   f"Setup tool error: {setup_file} - {str(e)}")
            else:
                self.log_finding('WARNING', 'ONBOARDING',
                               f"Missing setup tool: {setup_file}")
        
        onboarding_metrics['setup_clarity'] = {
            'total_setup_tools': len(setup_files),
            'working_tools': working_setup_tools,
            'setup_score': setup_score
        }
        
        # Check example quality
        epic_examples = list((self.project_root / 'epics').glob('*.json')) if (self.project_root / 'epics').exists() else []
        example_score = 0
        
        if epic_examples:
            for epic_file in epic_examples:
                try:
                    with open(epic_file, 'r') as f:
                        epic_data = json.load(f)
                    
                    # Check if it's a good example (not just template)
                    has_realistic_data = epic_data.get('title', '') != 'Epic Title Here'
                    has_tasks = len(epic_data.get('tasks', [])) > 0
                    has_tdd_phases = any(task.get('phase') in ['analysis', 'red', 'green', 'refactor'] 
                                       for task in epic_data.get('tasks', []))
                    
                    if has_realistic_data and has_tasks and has_tdd_phases:
                        example_score += 30
                        self.log_finding('SUCCESS', 'ONBOARDING',
                                       f"Good example epic: {epic_file.name}")
                    elif has_tasks:
                        example_score += 15
                        self.log_finding('WARNING', 'ONBOARDING',
                                       f"Basic example: {epic_file.name}")
                    else:
                        self.log_finding('WARNING', 'ONBOARDING',
                                       f"Template-only file: {epic_file.name}")
                        
                except Exception as e:
                    self.log_finding('ERROR', 'ONBOARDING',
                                   f"Invalid example epic: {epic_file.name} - {str(e)}")
            
            if len(epic_examples) >= 2:
                example_score += 20
                self.log_finding('SUCCESS', 'ONBOARDING', "Multiple epic examples available")
        else:
            self.log_finding('WARNING', 'ONBOARDING', "No epic examples found")
        
        onboarding_metrics['example_quality'] = {
            'epic_examples': len(epic_examples),
            'example_score': example_score
        }
        
        overall_onboarding_score = min(100, (setup_score + example_score) / 2)
        self.metrics['onboarding_score'] = overall_onboarding_score
        
        return {
            'score': overall_onboarding_score,
            'metrics': onboarding_metrics
        }
    
    def audit_workflow_usability(self) -> Dict[str, Any]:
        """Audit TDD workflow usability and user guidance."""
        print("\n🔄 AUDITING TDD WORKFLOW USABILITY")
        print("=" * 50)
        
        workflow_metrics = {
            'commit_helper_usability': {},
            'workflow_documentation': {},
            'automation_quality': {}
        }
        
        # Test commit helper usability
        commit_helper_path = self.project_root / 'scripts' / 'commit_helper.py'
        commit_score = 0
        
        if commit_helper_path.exists():
            try:
                # Test interactive guide
                result = subprocess.run([
                    sys.executable, str(commit_helper_path), '--guide'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    guide_content = result.stdout
                    
                    # Check guide quality
                    has_tdd_explanation = 'red' in guide_content.lower() and 'green' in guide_content.lower()
                    has_examples = '[EPIC-' in guide_content
                    has_phase_explanation = 'analysis' in guide_content.lower()
                    has_visual_elements = any(char in guide_content for char in ['🔴', '🟢', '🔄', '📝'])
                    
                    if has_tdd_explanation:
                        commit_score += 25
                        self.log_finding('SUCCESS', 'WORKFLOW', "Commit helper explains TDD phases")
                    
                    if has_examples:
                        commit_score += 25
                        self.log_finding('SUCCESS', 'WORKFLOW', "Commit helper provides examples")
                    
                    if has_phase_explanation:
                        commit_score += 20
                        self.log_finding('SUCCESS', 'WORKFLOW', "Good phase documentation")
                    
                    if has_visual_elements:
                        commit_score += 10
                        self.log_finding('SUCCESS', 'WORKFLOW', "Visual workflow guidance")
                    
                # Test validation functionality
                test_message = "[EPIC-1] red: test: add user validation [Task 1.1 | 30min]"
                result = subprocess.run([
                    sys.executable, str(commit_helper_path), '--validate', test_message
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and 'Valid' in result.stdout:
                    commit_score += 20
                    self.log_finding('SUCCESS', 'WORKFLOW', "Commit validation works correctly")
                else:
                    self.log_finding('WARNING', 'WORKFLOW', "Commit validation issues")
                    
            except Exception as e:
                self.log_finding('ERROR', 'WORKFLOW', f"Commit helper test failed: {str(e)}")
        else:
            self.log_finding('ERROR', 'WORKFLOW', "Commit helper script missing")
        
        workflow_metrics['commit_helper_usability'] = {
            'score': commit_score,
            'exists': commit_helper_path.exists()
        }
        
        # Check TDD workflow documentation
        tdd_doc_path = self.project_root / 'docs' / 'TDD_COMMIT_PATTERNS.md'
        doc_score = 0
        
        if tdd_doc_path.exists():
            content = tdd_doc_path.read_text()
            
            # Check documentation completeness
            has_pattern_explanation = '[EPIC-' in content
            has_phase_details = all(phase in content.lower() for phase in ['analysis', 'red', 'green', 'refactor'])
            has_examples = content.count('[EPIC-') >= 3
            has_troubleshooting = 'troubleshoot' in content.lower() or 'problem' in content.lower()
            
            if has_pattern_explanation:
                doc_score += 25
            if has_phase_details:
                doc_score += 25
            if has_examples:
                doc_score += 25
            if has_troubleshooting:
                doc_score += 25
                
            if doc_score >= 75:
                self.log_finding('SUCCESS', 'WORKFLOW', "Excellent TDD documentation")
            elif doc_score >= 50:
                self.log_finding('WARNING', 'WORKFLOW', "Good but incomplete TDD documentation")
            else:
                self.log_finding('ERROR', 'WORKFLOW', "Poor TDD documentation")
        else:
            self.log_finding('WARNING', 'WORKFLOW', "TDD workflow documentation missing")
        
        workflow_metrics['workflow_documentation'] = {
            'score': doc_score,
            'exists': tdd_doc_path.exists()
        }
        
        # Check GitHub Actions automation
        workflow_path = self.project_root / '.github' / 'workflows' / 'update-tdd-gantt.yml'
        automation_score = 0
        
        if workflow_path.exists():
            try:
                import yaml
                with open(workflow_path, 'r') as f:
                    workflow_config = yaml.safe_load(f)
                
                # Check automation quality
                has_automatic_triggers = 'push' in workflow_config.get('on', {})
                has_manual_trigger = 'workflow_dispatch' in workflow_config.get('on', {})
                has_dependency_caching = 'cache' in str(workflow_config).lower()
                has_error_handling = 'continue-on-error' in str(workflow_config)
                
                if has_automatic_triggers:
                    automation_score += 30
                    self.log_finding('SUCCESS', 'WORKFLOW', "Automatic chart updates on commits")
                
                if has_manual_trigger:
                    automation_score += 20
                    self.log_finding('SUCCESS', 'WORKFLOW', "Manual workflow trigger available")
                
                if has_dependency_caching:
                    automation_score += 25
                    self.log_finding('SUCCESS', 'WORKFLOW', "Dependency caching configured")
                
                if has_error_handling:
                    automation_score += 25
                    self.log_finding('SUCCESS', 'WORKFLOW', "Error handling in automation")
                    
            except Exception as e:
                self.log_finding('ERROR', 'WORKFLOW', f"Failed to analyze workflow: {str(e)}")
        else:
            self.log_finding('WARNING', 'WORKFLOW', "GitHub Actions workflow missing")
        
        workflow_metrics['automation_quality'] = {
            'score': automation_score,
            'exists': workflow_path.exists()
        }
        
        overall_workflow_score = (commit_score + doc_score + automation_score) / 3
        self.metrics['workflow_usability_score'] = overall_workflow_score
        
        return {
            'score': overall_workflow_score,
            'metrics': workflow_metrics
        }
    
    def audit_error_handling_ux(self) -> Dict[str, Any]:
        """Audit error handling and user feedback quality."""
        print("\n🚨 AUDITING ERROR HANDLING & USER FEEDBACK")
        print("=" * 50)
        
        error_handling_metrics = {
            'helpful_error_messages': 0,
            'graceful_degradation': 0,
            'user_guidance_on_errors': 0
        }
        
        # Test error scenarios
        test_scenarios = [
            {
                'name': 'Invalid commit pattern',
                'script': 'scripts/commit_helper.py',
                'args': ['--validate', 'invalid commit message'],
                'expect_helpful_error': True
            },
            {
                'name': 'Missing dependencies',
                'script': 'scripts/visualization/tdd_gantt_tracker.py',
                'args': ['--help'],
                'expect_graceful_degradation': True
            }
        ]
        
        error_score = 0
        
        for scenario in test_scenarios:
            script_path = self.project_root / scenario['script']
            if script_path.exists():
                try:
                    result = subprocess.run([
                        sys.executable, str(script_path)] + scenario['args'],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    error_output = result.stderr + result.stdout
                    
                    # Check for helpful error messages
                    if scenario.get('expect_helpful_error') and result.returncode != 0:
                        has_explanation = len(error_output) > 50
                        has_guidance = any(word in error_output.lower() 
                                         for word in ['try', 'should', 'example', 'format'])
                        has_context = any(word in error_output.lower()
                                        for word in ['invalid', 'missing', 'expected'])
                        
                        if has_explanation and has_guidance:
                            error_score += 25
                            error_handling_metrics['helpful_error_messages'] += 1
                            self.log_finding('SUCCESS', 'ERROR_HANDLING',
                                           f"Helpful error in {scenario['name']}")
                        elif has_context:
                            error_score += 15
                            self.log_finding('WARNING', 'ERROR_HANDLING',
                                           f"Basic error message in {scenario['name']}")
                        else:
                            self.log_finding('ERROR', 'ERROR_HANDLING',
                                           f"Poor error message in {scenario['name']}")
                    
                    # Check for graceful degradation
                    if scenario.get('expect_graceful_degradation'):
                        if 'ModuleNotFoundError' in error_output:
                            # Should suggest fallback or installation
                            has_suggestion = any(word in error_output.lower()
                                               for word in ['install', 'pip', 'poetry', 'try'])
                            if has_suggestion:
                                error_score += 25
                                error_handling_metrics['graceful_degradation'] += 1
                                self.log_finding('SUCCESS', 'ERROR_HANDLING',
                                               f"Graceful degradation in {scenario['name']}")
                            else:
                                self.log_finding('WARNING', 'ERROR_HANDLING',
                                               f"Missing degradation guidance in {scenario['name']}")
                        else:
                            # No missing dependencies, which is good
                            error_score += 15
                            
                except subprocess.TimeoutExpired:
                    self.log_finding('WARNING', 'ERROR_HANDLING',
                                   f"Timeout testing {scenario['name']}")
                except Exception as e:
                    self.log_finding('ERROR', 'ERROR_HANDLING',
                                   f"Failed to test {scenario['name']}: {str(e)}")
        
        # Check for user guidance files
        guidance_files = [
            'TROUBLESHOOTING.md',
            'docs/github_pages_setup_guide.md'
        ]
        
        for guidance_file in guidance_files:
            guidance_path = self.project_root / guidance_file
            if guidance_path.exists():
                content = guidance_path.read_text()
                if len(content) > 500:  # Substantial content
                    error_score += 15
                    error_handling_metrics['user_guidance_on_errors'] += 1
                    self.log_finding('SUCCESS', 'ERROR_HANDLING',
                                   f"Good troubleshooting guide: {guidance_file}")
                else:
                    self.log_finding('WARNING', 'ERROR_HANDLING',
                                   f"Minimal troubleshooting guide: {guidance_file}")
            else:
                self.log_finding('WARNING', 'ERROR_HANDLING',
                               f"Missing troubleshooting guide: {guidance_file}")
        
        self.metrics['error_handling_score'] = min(100, error_score)
        
        return {
            'score': min(100, error_score),
            'metrics': error_handling_metrics
        }
    
    def audit_visual_appeal(self) -> Dict[str, Any]:
        """Audit visual appeal and professional presentation."""
        print("\n🎨 AUDITING VISUAL APPEAL & PRESENTATION")
        print("=" * 50)
        
        visual_metrics = {
            'readme_visual_elements': {},
            'dashboard_quality': {},
            'consistent_branding': {}
        }
        
        visual_score = 0
        
        # Check README visual elements
        readme_path = self.project_root / 'README.md'
        if readme_path.exists():
            content = readme_path.read_text()
            
            # Count visual elements
            badge_count = len(re.findall(r'!\[.*?\]\(.*?badge', content))
            emoji_count = len(re.findall(r'[🎯📊🚀✨🧪📈🤖🏗️📋🔧⚙️🔍📚👥🔄🚨🎨]', content))
            diagram_count = len(re.findall(r'```mermaid', content))
            image_count = len(re.findall(r'!\[.*?\]\(.*?\.(png|jpg|gif|svg)', content))
            
            visual_metrics['readme_visual_elements'] = {
                'badges': badge_count,
                'emojis': emoji_count,
                'diagrams': diagram_count,
                'images': image_count
            }
            
            if badge_count >= 3:
                visual_score += 20
                self.log_finding('SUCCESS', 'VISUAL', f"Good badge usage ({badge_count} badges)")
            elif badge_count > 0:
                visual_score += 10
            
            if emoji_count >= 10:
                visual_score += 20
                self.log_finding('SUCCESS', 'VISUAL', f"Good emoji usage ({emoji_count} emojis)")
            elif emoji_count >= 5:
                visual_score += 15
            
            if diagram_count > 0:
                visual_score += 20
                self.log_finding('SUCCESS', 'VISUAL', f"Includes diagrams ({diagram_count})")
            
            # Check for consistent structure
            has_toc = 'Table of Contents' in content or '## Contents' in content
            has_sections = len(re.findall(r'^#{1,3}\s', content, re.MULTILINE)) >= 8
            
            if has_toc:
                visual_score += 10
            if has_sections:
                visual_score += 10
        
        # Check dashboard quality
        dashboard_path = self.project_root / 'docs' / 'dashboard.html'
        if dashboard_path.exists():
            content = dashboard_path.read_text()
            
            # Check for professional styling
            has_css_styling = '<style' in content or 'stylesheet' in content
            has_interactive_elements = 'plotly' in content.lower()
            has_responsive_design = 'responsive' in content or 'mobile' in content
            has_color_scheme = 'gradient' in content or 'color:' in content
            
            dashboard_score = 0
            if has_css_styling:
                dashboard_score += 25
            if has_interactive_elements:
                dashboard_score += 25
            if has_responsive_design:
                dashboard_score += 25
            if has_color_scheme:
                dashboard_score += 25
                
            visual_metrics['dashboard_quality'] = {
                'has_styling': has_css_styling,
                'has_interactivity': has_interactive_elements,
                'has_responsive': has_responsive_design,
                'has_colors': has_color_scheme,
                'score': dashboard_score
            }
            
            visual_score += dashboard_score * 0.5  # Weight dashboard as 50% of visual score
            
            if dashboard_score >= 75:
                self.log_finding('SUCCESS', 'VISUAL', "Professional dashboard design")
            elif dashboard_score >= 50:
                self.log_finding('WARNING', 'VISUAL', "Basic dashboard design")
            else:
                self.log_finding('ERROR', 'VISUAL', "Poor dashboard design")
        else:
            self.log_finding('WARNING', 'VISUAL', "Dashboard HTML missing")
        
        # Check for consistent branding/theming
        branding_elements = []
        files_to_check = ['README.md', 'docs/index.md', 'docs/dashboard.html']
        
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            if full_path.exists():
                content = full_path.read_text()
                if 'TDD' in content:
                    branding_elements.append(file_path)
        
        if len(branding_elements) >= 2:
            visual_score += 10
            self.log_finding('SUCCESS', 'VISUAL', "Consistent TDD branding across files")
        
        visual_metrics['consistent_branding'] = {
            'files_with_branding': len(branding_elements),
            'total_checked': len(files_to_check)
        }
        
        self.metrics['visual_appeal_score'] = min(100, visual_score)
        
        return {
            'score': min(100, visual_score),
            'metrics': visual_metrics
        }
    
    def generate_ux_report(self) -> Dict[str, Any]:
        """Generate comprehensive user experience report."""
        print("\n📊 GENERATING USER EXPERIENCE REPORT")
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
            'user_experience_level': self._calculate_ux_level(overall_score),
            'metrics': self.metrics,
            'summary': {
                'total_findings': len(self.findings),
                'critical_issues': len(critical_issues),
                'errors': len(errors),
                'warnings': len(warnings),
                'successes': len(successes)
            },
            'findings': self.findings,
            'recommendations': self._generate_ux_recommendations()
        }
        
        # Console summary
        grade_colors = {
            'A+': '🟢', 'A': '🟢', 'B+': '🔵', 'B': '🔵', 
            'C+': '🟡', 'C': '🟡', 'D': '🟠', 'F': '🔴'
        }
        ux_colors = {'EXCELLENT': '🟢', 'GOOD': '🔵', 'FAIR': '🟡', 'POOR': '🔴'}
        
        grade_color = grade_colors.get(report['grade'], '⚪')
        ux_color = ux_colors.get(report['user_experience_level'], '⚪')
        
        print(f"\n{grade_color} OVERALL UX GRADE: {report['grade']} ({overall_score:.1f}%)")
        print(f"{ux_color} USER EXPERIENCE LEVEL: {report['user_experience_level']}")
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
    
    def _calculate_ux_level(self, score: float) -> str:
        """Calculate UX maturity level."""
        if score >= 85: return 'EXCELLENT'
        elif score >= 70: return 'GOOD'
        elif score >= 55: return 'FAIR'
        else: return 'POOR'
    
    def _generate_ux_recommendations(self) -> List[str]:
        """Generate actionable UX recommendations."""
        recommendations = []
        
        if self.metrics.get('readme_score', 0) < 70:
            recommendations.append("📚 HIGH: Improve README with more examples, clearer setup instructions")
        
        if self.metrics.get('onboarding_score', 0) < 60:
            recommendations.append("🚀 HIGH: Enhance onboarding experience with better examples and guides")
        
        if self.metrics.get('workflow_usability_score', 0) < 70:
            recommendations.append("🔄 HIGH: Improve TDD workflow documentation and tooling")
        
        if self.metrics.get('error_handling_score', 0) < 60:
            recommendations.append("🚨 MEDIUM: Add better error messages and troubleshooting guides")
        
        if self.metrics.get('visual_appeal_score', 0) < 70:
            recommendations.append("🎨 MEDIUM: Enhance visual presentation with more diagrams and styling")
        
        if self.metrics.get('documentation_coverage_score', 0) < 60:
            recommendations.append("📖 MEDIUM: Complete missing documentation files")
        
        critical_count = len([f for f in self.findings if f['level'] == 'CRITICAL'])
        if critical_count > 0:
            recommendations.append(f"🔥 CRITICAL: Fix {critical_count} critical UX issues immediately")
        
        if not recommendations:
            recommendations.append("🎉 Excellent! User experience is well designed and comprehensive")
        
        return recommendations


def main():
    """Main UX audit execution."""
    parser = argparse.ArgumentParser(description="👥 TDD Template User Experience Audit")
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output with detailed findings')
    parser.add_argument('--comprehensive', action='store_true',
                       help='Run comprehensive UX tests (slower but thorough)')
    parser.add_argument('--report', choices=['console', 'json', 'both'], 
                       default='console', help='Report output format')
    parser.add_argument('--output', '-o', help='Output file for JSON report')
    
    args = parser.parse_args()
    
    print("👥 TDD PROJECT TEMPLATE - USER EXPERIENCE AUDIT")
    print("=" * 60)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Project: {Path.cwd()}")
    print(f"🔍 Comprehensive: {'YES' if args.comprehensive else 'NO'}")
    
    auditor = UserExperienceAuditor(verbose=args.verbose, comprehensive=args.comprehensive)
    
    try:
        # Run all UX audits
        doc_results = auditor.audit_documentation_quality()
        onboarding_results = auditor.audit_onboarding_experience()
        workflow_results = auditor.audit_workflow_usability()
        error_results = auditor.audit_error_handling_ux()
        visual_results = auditor.audit_visual_appeal()
        
        # Generate final report
        report = auditor.generate_ux_report()
        
        # Output report
        if args.report in ['json', 'both']:
            output_file = args.output or f'ux_audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 JSON report saved: {output_file}")
        
        # Return exit code based on grade
        grade_scores = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C+': 1, 'C': 1, 'D': 2, 'F': 3}
        return grade_scores.get(report['grade'], 3)
        
    except KeyboardInterrupt:
        print("\n❌ UX audit cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ UX audit failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())