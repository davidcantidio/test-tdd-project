#!/usr/bin/env python3
"""
🌐 TDD Project Template - Live Deployment & URL Validation Audit
==============================================================

Auditoria que testa URLs reais do GitHub Pages, detecta erros 404,
valida dashboards funcionando e verifica deployment completo.

Uso:
    python scripts/audit_live_deployment.py
    python scripts/audit_live_deployment.py --verbose --check-all-urls
"""

import argparse
import json
import os
import sys
import re
import subprocess
import requests
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import yaml


class LiveDeploymentAuditor:
    """Auditor de deployment real e URLs do GitHub Pages."""
    
    def __init__(self, verbose: bool = False, check_all_urls: bool = False):
        self.verbose = verbose
        self.check_all_urls = check_all_urls
        self.project_root = Path.cwd()
        self.findings = []
        self.metrics = {}
        
        # GitHub Pages URL configuration
        self.github_config = self._detect_github_config()
        
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
    
    def _detect_github_config(self) -> Dict[str, Any]:
        """Detect GitHub repository configuration."""
        config = {
            'repository_name': None,
            'username': None,
            'base_url': None,
            'detected_from': None
        }
        
        # Try to detect from git remote
        try:
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                                  capture_output=True, text=True, timeout=10,
                                  cwd=self.project_root)
            
            if result.returncode == 0:
                remote_url = result.stdout.strip()
                
                # Parse GitHub URL patterns
                github_patterns = [
                    r'https://github\.com/([^/]+)/([^/]+)\.git',
                    r'git@github\.com:([^/]+)/([^/]+)\.git',
                    r'https://github\.com/([^/]+)/([^/]+)'
                ]
                
                for pattern in github_patterns:
                    match = re.search(pattern, remote_url)
                    if match:
                        config['username'] = match.group(1)
                        config['repository_name'] = match.group(2)
                        config['base_url'] = f"https://{config['username']}.github.io/{config['repository_name']}"
                        config['detected_from'] = 'git_remote'
                        break
                        
        except Exception:
            pass
        
        # Fallback: try to detect from Jekyll config
        if not config['base_url']:
            jekyll_config_path = self.project_root / 'docs' / '_config.yml'
            if jekyll_config_path.exists():
                try:
                    with open(jekyll_config_path, 'r') as f:
                        jekyll_config = yaml.safe_load(f)
                    
                    if 'url' in jekyll_config:
                        config['base_url'] = jekyll_config['url']
                        config['detected_from'] = 'jekyll_config'
                    elif 'github' in jekyll_config and 'repository_name' in jekyll_config['github']:
                        repo_name = jekyll_config['github']['repository_name']
                        if 'github' in jekyll_config and 'owner_name' in jekyll_config['github']:
                            owner_name = jekyll_config['github']['owner_name']
                            config['username'] = owner_name
                            config['repository_name'] = repo_name
                            config['base_url'] = f"https://{owner_name}.github.io/{repo_name}"
                            config['detected_from'] = 'jekyll_github_config'
                            
                except Exception:
                    pass
        
        # Manual fallback for known template
        if not config['base_url']:
            config['username'] = 'davidcantidio'  # Known from context
            config['repository_name'] = 'tdd-project-template'
            config['base_url'] = f"https://{config['username']}.github.io/{config['repository_name']}"
            config['detected_from'] = 'manual_fallback'
        
        return config
    
    def audit_github_pages_availability(self) -> Dict[str, Any]:
        """Audit GitHub Pages availability and configuration."""
        print("\n🌐 AUDITING GITHUB PAGES AVAILABILITY")
        print("=" * 50)
        
        pages_metrics = {
            'github_config': self.github_config,
            'pages_enabled': False,
            'base_url_accessible': False,
            'response_time_ms': None,
            'status_code': None,
            'content_length': 0
        }
        
        pages_score = 0
        
        # Log detected configuration
        if self.github_config['base_url']:
            self.log_finding('INFO', 'PAGES', 
                           f"Detected GitHub Pages URL: {self.github_config['base_url']}")
            self.log_finding('INFO', 'PAGES', 
                           f"Configuration source: {self.github_config['detected_from']}")
        else:
            self.log_finding('ERROR', 'PAGES', "Could not detect GitHub Pages URL")
            return {'score': 0, 'metrics': pages_metrics}
        
        # Test base URL accessibility
        try:
            start_time = time.time()
            response = requests.get(self.github_config['base_url'], 
                                  timeout=30,
                                  headers={'User-Agent': 'TDD-Template-Auditor/1.0'})
            response_time = (time.time() - start_time) * 1000
            
            pages_metrics['status_code'] = response.status_code
            pages_metrics['response_time_ms'] = round(response_time, 2)
            pages_metrics['content_length'] = len(response.content)
            
            if response.status_code == 200:
                pages_metrics['base_url_accessible'] = True
                pages_metrics['pages_enabled'] = True
                pages_score += 40
                
                self.log_finding('SUCCESS', 'PAGES', 
                               f"GitHub Pages accessible ({response_time:.0f}ms)")
                
                # Check for Jekyll/TDD content
                content = response.text
                tdd_indicators = ['TDD', 'Test-Driven', 'Epic', 'Gantt', 'commit']
                found_indicators = [indicator for indicator in tdd_indicators 
                                  if indicator.lower() in content.lower()]
                
                if len(found_indicators) >= 3:
                    pages_score += 20
                    self.log_finding('SUCCESS', 'PAGES', 
                                   f"TDD-specific content detected: {', '.join(found_indicators)}")
                elif len(found_indicators) >= 1:
                    pages_score += 10
                    self.log_finding('WARNING', 'PAGES', 
                                   f"Limited TDD content: {', '.join(found_indicators)}")
                else:
                    self.log_finding('WARNING', 'PAGES', "No TDD-specific content found")
                
                # Check for Jekyll indicators
                jekyll_indicators = ['Jekyll', 'liquid', '_includes', '_layouts']
                found_jekyll = [indicator for indicator in jekyll_indicators 
                              if indicator in content]
                
                if found_jekyll:
                    pages_score += 10
                    self.log_finding('SUCCESS', 'PAGES', "Jekyll processing detected")
                
                # Performance bonus
                if response_time < 2000:  # < 2 seconds
                    pages_score += 15
                    self.log_finding('SUCCESS', 'PAGES', f"Excellent response time: {response_time:.0f}ms")
                elif response_time < 5000:  # < 5 seconds
                    pages_score += 10
                    self.log_finding('SUCCESS', 'PAGES', f"Good response time: {response_time:.0f}ms")
                else:
                    self.log_finding('WARNING', 'PAGES', f"Slow response time: {response_time:.0f}ms")
                
            elif response.status_code == 404:
                self.log_finding('ERROR', 'PAGES', 
                               f"GitHub Pages not found (404) - may not be enabled")
            elif response.status_code in [403, 401]:
                self.log_finding('ERROR', 'PAGES', 
                               f"GitHub Pages access denied ({response.status_code}) - check permissions")
            else:
                self.log_finding('WARNING', 'PAGES', 
                               f"Unexpected response code: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_finding('ERROR', 'PAGES', "GitHub Pages request timeout (>30s)")
        except requests.exceptions.ConnectionError:
            self.log_finding('ERROR', 'PAGES', "GitHub Pages connection error - check URL")
        except requests.exceptions.RequestException as e:
            self.log_finding('ERROR', 'PAGES', f"GitHub Pages request failed: {str(e)}")
        except Exception as e:
            self.log_finding('ERROR', 'PAGES', f"GitHub Pages check failed: {str(e)}")
        
        self.metrics['github_pages_score'] = pages_score
        
        return {
            'score': pages_score,
            'metrics': pages_metrics
        }
    
    def audit_specific_urls_404_detection(self) -> Dict[str, Any]:
        """Audit specific URLs for 404 errors and content validation."""
        print("\n🔍 AUDITING SPECIFIC URLS & 404 DETECTION")
        print("=" * 50)
        
        url_metrics = {
            'tested_urls': [],
            'successful_urls': [],
            'failed_urls': [],
            'redirect_urls': [],
            '404_urls': []
        }
        
        url_score = 0
        
        if not self.github_config['base_url']:
            self.log_finding('ERROR', 'URLS', "No base URL available for testing")
            return {'score': 0, 'metrics': url_metrics}
        
        # Define critical URLs to test
        test_urls = [
            {
                'path': '/',
                'name': 'Main Page',
                'critical': True,
                'expected_content': ['TDD', 'template']
            },
            {
                'path': '/dashboard.html',
                'name': 'Interactive Dashboard',
                'critical': True,
                'expected_content': ['plotly', 'TDD', 'dashboard']
            },
            {
                'path': '/tdd_gantt_progress.html',
                'name': 'Gantt Chart Page',
                'critical': False,
                'expected_content': ['Gantt', 'chart']
            },
            {
                'path': '/index.html',
                'name': 'Index Page',
                'critical': False,
                'expected_content': ['TDD']
            }
        ]
        
        # Add Jekyll-specific URLs
        if self.check_all_urls:
            test_urls.extend([
                {
                    'path': '/assets/css/style.css',
                    'name': 'Stylesheet',
                    'critical': False,
                    'expected_content': []
                },
                {
                    'path': '/404.html',
                    'name': '404 Error Page',
                    'critical': False,
                    'expected_content': ['404', 'not found']
                }
            ])
        
        # Test each URL
        for url_config in test_urls:
            full_url = urljoin(self.github_config['base_url'], url_config['path'])
            url_metrics['tested_urls'].append(full_url)
            
            try:
                start_time = time.time()
                response = requests.get(full_url, 
                                      timeout=20,
                                      headers={'User-Agent': 'TDD-Template-Auditor/1.0'},
                                      allow_redirects=True)
                response_time = (time.time() - start_time) * 1000
                
                url_result = {
                    'url': full_url,
                    'name': url_config['name'],
                    'status_code': response.status_code,
                    'response_time_ms': round(response_time, 2),
                    'content_length': len(response.content),
                    'redirected': response.url != full_url,
                    'final_url': response.url if response.url != full_url else None
                }
                
                if response.status_code == 200:
                    url_metrics['successful_urls'].append(url_result)
                    
                    # Score based on criticality
                    if url_config['critical']:
                        url_score += 25
                        self.log_finding('SUCCESS', 'URLS', 
                                       f"Critical URL accessible: {url_config['name']}")
                    else:
                        url_score += 10
                        self.log_finding('SUCCESS', 'URLS', 
                                       f"URL accessible: {url_config['name']}")
                    
                    # Check expected content
                    if url_config['expected_content']:
                        content = response.text.lower()
                        found_content = [item for item in url_config['expected_content'] 
                                       if item.lower() in content]
                        
                        if len(found_content) >= len(url_config['expected_content']) * 0.7:
                            url_score += 5
                            self.log_finding('SUCCESS', 'URLS', 
                                           f"Expected content found in {url_config['name']}")
                        else:
                            self.log_finding('WARNING', 'URLS',
                                           f"Missing expected content in {url_config['name']}: {url_config['expected_content']}")
                    
                    # Performance bonus
                    if response_time < 1000:
                        url_score += 5
                        
                elif response.status_code == 404:
                    url_metrics['404_urls'].append(url_result)
                    if url_config['critical']:
                        self.log_finding('CRITICAL', 'URLS',
                                       f"CRITICAL 404: {url_config['name']} not found")
                    else:
                        self.log_finding('WARNING', 'URLS',
                                       f"404: {url_config['name']} not found")
                        
                elif response.status_code in [301, 302, 303, 307, 308]:
                    url_metrics['redirect_urls'].append(url_result)
                    self.log_finding('INFO', 'URLS',
                                   f"Redirect: {url_config['name']} -> {response.url}")
                    url_score += 5  # Partial credit for redirects
                    
                else:
                    url_metrics['failed_urls'].append(url_result)
                    self.log_finding('ERROR', 'URLS',
                                   f"Error {response.status_code}: {url_config['name']}")
                    
            except requests.exceptions.Timeout:
                url_result = {'url': full_url, 'name': url_config['name'], 'error': 'timeout'}
                url_metrics['failed_urls'].append(url_result)
                self.log_finding('ERROR', 'URLS', f"Timeout: {url_config['name']}")
                
            except requests.exceptions.RequestException as e:
                url_result = {'url': full_url, 'name': url_config['name'], 'error': str(e)}
                url_metrics['failed_urls'].append(url_result)
                self.log_finding('ERROR', 'URLS', f"Request failed: {url_config['name']} - {str(e)}")
                
            except Exception as e:
                url_result = {'url': full_url, 'name': url_config['name'], 'error': str(e)}
                url_metrics['failed_urls'].append(url_result)
                self.log_finding('ERROR', 'URLS', f"Unexpected error: {url_config['name']} - {str(e)}")
        
        # Calculate success rate
        total_urls = len(test_urls)
        successful_urls = len(url_metrics['successful_urls'])
        critical_urls = [url for url in test_urls if url['critical']]
        critical_successes = len([url for url in url_metrics['successful_urls'] 
                                if any(crit['name'] == url['name'] for crit in critical_urls)])
        
        success_rate = (successful_urls / total_urls) * 100 if total_urls > 0 else 0
        critical_success_rate = (critical_successes / len(critical_urls)) * 100 if critical_urls else 100
        
        # Bonus for high success rates
        if critical_success_rate == 100:
            url_score += 20
            self.log_finding('SUCCESS', 'URLS', f"All critical URLs accessible ({critical_success_rate}%)")
        elif critical_success_rate >= 75:
            url_score += 10
            self.log_finding('WARNING', 'URLS', f"Most critical URLs accessible ({critical_success_rate}%)")
        else:
            self.log_finding('ERROR', 'URLS', f"Critical URL failures ({critical_success_rate}%)")
        
        self.log_finding('INFO', 'URLS', f"Overall URL success rate: {success_rate:.1f}%")
        
        self.metrics['url_validation_score'] = url_score
        
        return {
            'score': url_score,
            'success_rate': success_rate,
            'critical_success_rate': critical_success_rate,
            'metrics': url_metrics
        }
    
    def audit_dashboard_functionality(self) -> Dict[str, Any]:
        """Audit dashboard functionality and interactive features."""
        print("\n📊 AUDITING DASHBOARD FUNCTIONALITY")
        print("=" * 50)
        
        dashboard_metrics = {
            'dashboard_accessible': False,
            'plotly_detected': False,
            'interactivity_features': [],
            'styling_quality': {},
            'mobile_friendly': False
        }
        
        dashboard_score = 0
        
        if not self.github_config['base_url']:
            self.log_finding('ERROR', 'DASHBOARD', "No base URL for dashboard testing")
            return {'score': 0, 'metrics': dashboard_metrics}
        
        dashboard_url = urljoin(self.github_config['base_url'], '/dashboard.html')
        
        try:
            response = requests.get(dashboard_url, 
                                  timeout=30,
                                  headers={'User-Agent': 'TDD-Template-Auditor/1.0'})
            
            if response.status_code == 200:
                dashboard_metrics['dashboard_accessible'] = True
                dashboard_score += 30
                self.log_finding('SUCCESS', 'DASHBOARD', "Dashboard page accessible")
                
                content = response.text
                
                # Check for Plotly integration
                plotly_indicators = [
                    'plotly', 'Plotly', 'plotly.js', 'plotly.min.js',
                    'Plotly.newPlot', 'go.Figure', 'plotly-graph-div'
                ]
                found_plotly = [indicator for indicator in plotly_indicators 
                              if indicator in content]
                
                if found_plotly:
                    dashboard_metrics['plotly_detected'] = True
                    dashboard_score += 25
                    self.log_finding('SUCCESS', 'DASHBOARD', 
                                   f"Plotly integration detected: {', '.join(found_plotly[:3])}")
                else:
                    self.log_finding('WARNING', 'DASHBOARD', "No Plotly integration detected")
                
                # Check for interactive features
                interactive_features = []
                
                if 'onclick' in content or 'addEventListener' in content:
                    interactive_features.append('click_handlers')
                if 'hover' in content.lower():
                    interactive_features.append('hover_effects')
                if 'responsive' in content.lower():
                    interactive_features.append('responsive_design')
                if 'update' in content and 'chart' in content.lower():
                    interactive_features.append('dynamic_updates')
                if 'filter' in content.lower():
                    interactive_features.append('data_filtering')
                
                dashboard_metrics['interactivity_features'] = interactive_features
                
                if len(interactive_features) >= 3:
                    dashboard_score += 20
                    self.log_finding('SUCCESS', 'DASHBOARD', 
                                   f"Rich interactivity: {', '.join(interactive_features)}")
                elif len(interactive_features) >= 1:
                    dashboard_score += 10
                    self.log_finding('WARNING', 'DASHBOARD', 
                                   f"Basic interactivity: {', '.join(interactive_features)}")
                else:
                    self.log_finding('WARNING', 'DASHBOARD', "Limited interactivity detected")
                
                # Check styling quality
                styling_features = {}
                
                if 'gradient' in content.lower():
                    styling_features['gradients'] = True
                    dashboard_score += 5
                if 'css' in content.lower() or '<style' in content:
                    styling_features['custom_css'] = True
                    dashboard_score += 5
                if 'bootstrap' in content.lower() or 'materialize' in content.lower():
                    styling_features['css_framework'] = True
                    dashboard_score += 5
                if 'animation' in content.lower():
                    styling_features['animations'] = True
                    dashboard_score += 5
                
                dashboard_metrics['styling_quality'] = styling_features
                
                # Check for mobile-friendly indicators
                mobile_indicators = [
                    'viewport', 'responsive', 'mobile', '@media',
                    'flex', 'grid', 'col-', 'container'
                ]
                found_mobile = [indicator for indicator in mobile_indicators 
                              if indicator in content.lower()]
                
                if len(found_mobile) >= 2:
                    dashboard_metrics['mobile_friendly'] = True
                    dashboard_score += 10
                    self.log_finding('SUCCESS', 'DASHBOARD', "Mobile-friendly design detected")
                
                # Content quality check
                if len(content) > 5000:  # Substantial dashboard
                    dashboard_score += 10
                    self.log_finding('SUCCESS', 'DASHBOARD', "Comprehensive dashboard content")
                elif len(content) > 2000:
                    dashboard_score += 5
                    self.log_finding('WARNING', 'DASHBOARD', "Basic dashboard content")
                else:
                    self.log_finding('WARNING', 'DASHBOARD', "Minimal dashboard content")
                
            elif response.status_code == 404:
                self.log_finding('CRITICAL', 'DASHBOARD', "Dashboard not found (404)")
            else:
                self.log_finding('ERROR', 'DASHBOARD', 
                               f"Dashboard not accessible: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_finding('ERROR', 'DASHBOARD', f"Dashboard request failed: {str(e)}")
        except Exception as e:
            self.log_finding('ERROR', 'DASHBOARD', f"Dashboard test failed: {str(e)}")
        
        self.metrics['dashboard_functionality_score'] = dashboard_score
        
        return {
            'score': dashboard_score,
            'metrics': dashboard_metrics
        }
    
    def audit_jekyll_build_status(self) -> Dict[str, Any]:
        """Audit Jekyll build and deployment status."""
        print("\n🏗️ AUDITING JEKYLL BUILD STATUS")
        print("=" * 50)
        
        jekyll_metrics = {
            'jekyll_files_present': False,
            'build_indicators': [],
            'generated_files': [],
            'css_compiled': False,
            'includes_processed': False
        }
        
        jekyll_score = 0
        
        # Check for Jekyll source files
        jekyll_files = {
            'docs/_config.yml': 'Jekyll configuration',
            'docs/Gemfile': 'Ruby dependencies',
            'docs/index.md': 'Main content page'
        }
        
        jekyll_files_found = 0
        for file_path, description in jekyll_files.items():
            if (self.project_root / file_path).exists():
                jekyll_files_found += 1
        
        if jekyll_files_found >= 2:
            jekyll_metrics['jekyll_files_present'] = True
            jekyll_score += 20
            self.log_finding('SUCCESS', 'JEKYLL', f"Jekyll source files present ({jekyll_files_found}/3)")
        else:
            self.log_finding('WARNING', 'JEKYLL', f"Limited Jekyll files ({jekyll_files_found}/3)")
        
        # Test for Jekyll build indicators via live site
        if self.github_config['base_url']:
            try:
                response = requests.get(self.github_config['base_url'], 
                                      timeout=20,
                                      headers={'User-Agent': 'TDD-Template-Auditor/1.0'})
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Check for Jekyll-generated content
                    jekyll_indicators = []
                    
                    if '<!-- Generated by Jekyll' in content:
                        jekyll_indicators.append('jekyll_generator_comment')
                    if '_site' not in content and 'jekyll' in content.lower():
                        jekyll_indicators.append('jekyll_processing')
                    if 'liquid' in content or '{{' in content:
                        jekyll_indicators.append('liquid_templates')
                    if '/assets/' in content:
                        jekyll_indicators.append('assets_path')
                    if '<link' in content and 'css' in content:
                        jekyll_indicators.append('css_compilation')
                        jekyll_metrics['css_compiled'] = True
                        
                    jekyll_metrics['build_indicators'] = jekyll_indicators
                    
                    if len(jekyll_indicators) >= 3:
                        jekyll_score += 30
                        self.log_finding('SUCCESS', 'JEKYLL', 
                                       f"Strong Jekyll build evidence: {', '.join(jekyll_indicators)}")
                    elif len(jekyll_indicators) >= 1:
                        jekyll_score += 20
                        self.log_finding('SUCCESS', 'JEKYLL', 
                                       f"Jekyll build evidence: {', '.join(jekyll_indicators)}")
                    else:
                        jekyll_score += 10
                        self.log_finding('WARNING', 'JEKYLL', "Limited Jekyll build evidence")
                    
                    # Check for processed includes/layouts
                    if '<head>' in content and '<html' in content and '<!DOCTYPE' in content:
                        jekyll_metrics['includes_processed'] = True
                        jekyll_score += 15
                        self.log_finding('SUCCESS', 'JEKYLL', "Jekyll layout processing confirmed")
                    
                    # Test asset accessibility
                    asset_patterns = re.findall(r'/assets/[^"\'>\s]+', content)
                    if asset_patterns:
                        # Test a few assets
                        tested_assets = 0
                        working_assets = 0
                        
                        for asset_path in asset_patterns[:3]:  # Test first 3 assets
                            asset_url = urljoin(self.github_config['base_url'], asset_path)
                            try:
                                asset_response = requests.head(asset_url, timeout=10)
                                tested_assets += 1
                                if asset_response.status_code == 200:
                                    working_assets += 1
                            except:
                                tested_assets += 1
                        
                        if working_assets >= tested_assets * 0.8:  # 80% assets working
                            jekyll_score += 10
                            self.log_finding('SUCCESS', 'JEKYLL', 
                                           f"Jekyll assets accessible ({working_assets}/{tested_assets})")
                        else:
                            self.log_finding('WARNING', 'JEKYLL', 
                                           f"Some Jekyll assets missing ({working_assets}/{tested_assets})")
                    
            except Exception as e:
                self.log_finding('WARNING', 'JEKYLL', f"Jekyll build status check failed: {str(e)}")
        
        # Bonus for proper Jekyll directory structure
        jekyll_dirs = ['docs/_layouts', 'docs/_includes', 'docs/_sass', 'docs/assets']
        found_dirs = sum(1 for dir_path in jekyll_dirs 
                        if (self.project_root / dir_path).exists())
        
        if found_dirs >= 2:
            jekyll_score += 10
            self.log_finding('SUCCESS', 'JEKYLL', f"Good Jekyll directory structure ({found_dirs}/4)")
        
        self.metrics['jekyll_build_score'] = jekyll_score
        
        return {
            'score': jekyll_score,
            'metrics': jekyll_metrics
        }
    
    def generate_live_deployment_report(self) -> Dict[str, Any]:
        """Generate comprehensive live deployment report."""
        print("\n📊 GENERATING LIVE DEPLOYMENT REPORT")
        print("=" * 50)
        
        # Calculate overall deployment score
        deployment_weights = {
            'github_pages_score': 0.35,
            'url_validation_score': 0.30,
            'dashboard_functionality_score': 0.25,
            'jekyll_build_score': 0.10
        }
        
        overall_score = 0
        for metric, weight in deployment_weights.items():
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
            'deployment_status': self._calculate_deployment_status(overall_score),
            'github_config': self.github_config,
            'weighted_scores': {k: round(self.metrics.get(k, 0), 2) for k in deployment_weights.keys()},
            'weights_used': deployment_weights,
            'metrics': self.metrics,
            'summary': {
                'total_findings': len(self.findings),
                'critical_issues': len(critical_issues),
                'errors': len(errors),
                'warnings': len(warnings),
                'successes': len(successes)
            },
            'findings': self.findings,
            'recommendations': self._generate_deployment_recommendations()
        }
        
        # Console summary
        grade_colors = {
            'A+': '🟢', 'A': '🟢', 'B+': '🔵', 'B': '🔵', 
            'C+': '🟡', 'C': '🟡', 'D': '🟠', 'F': '🔴'
        }
        status_colors = {'LIVE': '🟢', 'PARTIAL': '🔵', 'ISSUES': '🟡', 'DOWN': '🔴'}
        
        grade_color = grade_colors.get(report['grade'], '⚪')
        status_color = status_colors.get(report['deployment_status'], '⚪')
        
        print(f"\n{grade_color} OVERALL DEPLOYMENT GRADE: {report['grade']} ({overall_score:.1f}%)")
        print(f"{status_color} DEPLOYMENT STATUS: {report['deployment_status']}")
        print(f"🌐 GitHub Pages URL: {self.github_config['base_url']}")
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
    
    def _calculate_deployment_status(self, score: float) -> str:
        """Calculate deployment status."""
        critical_issues = [f for f in self.findings if f['level'] == 'CRITICAL']
        
        if critical_issues:
            return 'DOWN'
        elif score >= 85:
            return 'LIVE'
        elif score >= 60:
            return 'PARTIAL'
        else:
            return 'ISSUES'
    
    def _generate_deployment_recommendations(self) -> List[str]:
        """Generate actionable deployment recommendations."""
        recommendations = []
        
        critical_count = len([f for f in self.findings if f['level'] == 'CRITICAL'])
        if critical_count > 0:
            recommendations.append(f"🔥 CRITICAL: Fix {critical_count} critical deployment issues immediately")
        
        if self.metrics.get('github_pages_score', 0) < 60:
            recommendations.append("🌐 CRITICAL: GitHub Pages not accessible - check repository settings")
        
        if self.metrics.get('url_validation_score', 0) < 70:
            recommendations.append("🔍 HIGH: Fix 404 errors and broken URLs")
        
        if self.metrics.get('dashboard_functionality_score', 0) < 60:
            recommendations.append("📊 HIGH: Dashboard not working - check Plotly integration")
        
        if self.metrics.get('jekyll_build_score', 0) < 70:
            recommendations.append("🏗️ MEDIUM: Jekyll build issues - check configuration")
        
        error_count = len([f for f in self.findings if f['level'] == 'ERROR'])
        if error_count >= 3:
            recommendations.append(f"❌ MEDIUM: Resolve {error_count} deployment errors")
        
        if not recommendations:
            recommendations.append("🎉 Excellent! Deployment is live and working perfectly")
        
        return recommendations


def main():
    """Main live deployment audit execution."""
    parser = argparse.ArgumentParser(description="🌐 TDD Template Live Deployment Audit")
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output with detailed findings')
    parser.add_argument('--check-all-urls', action='store_true',
                       help='Check additional URLs including assets')
    parser.add_argument('--report', choices=['console', 'json', 'both'], 
                       default='console', help='Report output format')
    parser.add_argument('--output', '-o', help='Output file for JSON report')
    
    args = parser.parse_args()
    
    print("🌐 TDD PROJECT TEMPLATE - LIVE DEPLOYMENT AUDIT")
    print("=" * 60)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Project: {Path.cwd()}")
    print(f"🔍 Check All URLs: {'YES' if args.check_all_urls else 'NO'}")
    
    auditor = LiveDeploymentAuditor(verbose=args.verbose, check_all_urls=args.check_all_urls)
    
    try:
        # Run all live deployment audits
        pages_results = auditor.audit_github_pages_availability()
        url_results = auditor.audit_specific_urls_404_detection()
        dashboard_results = auditor.audit_dashboard_functionality()
        jekyll_results = auditor.audit_jekyll_build_status()
        
        # Generate final report
        report = auditor.generate_live_deployment_report()
        
        # Output report
        if args.report in ['json', 'both']:
            output_file = args.output or f'live_deployment_audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 JSON report saved: {output_file}")
        
        # Return exit code based on deployment status
        status_codes = {'LIVE': 0, 'PARTIAL': 1, 'ISSUES': 2, 'DOWN': 3}
        return status_codes.get(report['deployment_status'], 3)
        
    except KeyboardInterrupt:
        print("\n❌ Live deployment audit cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Live deployment audit failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())