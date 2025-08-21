#!/usr/bin/env python3
"""
🕵️ Deep Architecture Audit - Third Layer Analysis

Advanced architectural analysis beyond surface-level validations.
Detects subtle but critical issues that can compromise system integrity.

FOCUS AREAS:
1. Circular dependency analysis
2. Hidden code duplication (semantic similarity)
3. Architectural violations (SOLID principles)
4. Performance anti-patterns
5. Security vulnerabilities
6. Maintainability issues
7. Hidden coupling
"""

import ast
import os
import sys
import re
import json
import hashlib
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Any, Tuple
from dataclasses import dataclass
import importlib.util

@dataclass
class ArchitecturalIssue:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # COUPLING, DUPLICATION, VIOLATION, SECURITY, PERFORMANCE
    description: str
    file_path: str
    line_number: int = 0
    recommendation: str = ""
    impact: str = ""

class DeepArchitectureAnalyzer:
    def __init__(self):
        self.issues = []
        self.module_dependencies = defaultdict(set)
        self.function_signatures = defaultdict(list)
        self.class_hierarchies = defaultdict(list)
        self.imports_graph = defaultdict(set)
        self.code_patterns = defaultdict(list)
        self.security_patterns = []
        self.performance_patterns = []
        
    def add_issue(self, severity: str, category: str, description: str, 
                  file_path: str, line: int = 0, recommendation: str = "", impact: str = ""):
        self.issues.append(ArchitecturalIssue(
            severity, category, description, file_path, line, recommendation, impact
        ))

    def analyze_circular_dependencies(self):
        """Detect circular import dependencies."""
        print("🔍 Analyzing circular dependencies...")
        
        def find_cycles(graph):
            visited = set()
            rec_stack = set()
            cycles = []
            
            def dfs(node, path):
                if node in rec_stack:
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    cycles.append(cycle)
                    return
                
                if node in visited:
                    return
                    
                visited.add(node)
                rec_stack.add(node)
                path.append(node)
                
                for neighbor in graph.get(node, []):
                    dfs(neighbor, path[:])
                
                rec_stack.remove(node)
                path.pop()
            
            for node in graph:
                if node not in visited:
                    dfs(node, [])
            
            return cycles
        
        cycles = find_cycles(self.imports_graph)
        
        for cycle in cycles:
            if len(cycle) > 2:  # Only report significant cycles
                cycle_str = " → ".join(cycle)
                self.add_issue(
                    "CRITICAL", "COUPLING",
                    f"Circular dependency detected: {cycle_str}",
                    cycle[0],
                    recommendation="Refactor to eliminate circular dependencies using dependency inversion",
                    impact="Can cause import failures, initialization order issues, and tight coupling"
                )

    # TODO: Consider extracting this block into a separate method
    def analyze_semantic_duplication(self):
        """Detect semantically similar code blocks."""
        print("🔍 Analyzing semantic code duplication...")
        
        # Group functions by similarity metrics
        similar_groups = defaultdict(list)
        
        for signature, occurrences in self.function_signatures.items():
            if len(occurrences) > 1:
                # Check if functions are actually different implementations
                code_hashes = []
                for occurrence in occurrences:
                    # Create a hash based on function structure
                    code_hash = self._hash_function_structure(occurrence)
                    code_hashes.append((code_hash, occurrence))
                
                # Group by similar structure
                hash_groups = defaultdict(list)
                for code_hash, occurrence in code_hashes:
                    hash_groups[code_hash].append(occurrence)
                
                for hash_val, similar_funcs in hash_groups.items():
                    if len(similar_funcs) > 1:
                        similar_groups[signature].extend(similar_funcs)
        
        for func_name, similar_funcs in similar_groups.items():
            if len(similar_funcs) > 1:
                locations = [f"{func['file']}:{func['line']}" for func in similar_funcs]
                self.add_issue(
                    "HIGH", "DUPLICATION",
                    f"Semantic duplication of function '{func_name}': {', '.join(locations)}",
                    similar_funcs[0]['file'],
                    similar_funcs[0]['line'],
                    recommendation="Extract common logic into shared utility functions",
                    impact="Increases maintenance burden and risk of inconsistent changes"
                )

# TODO: Consider extracting this block into a separate method

    def analyze_solid_violations(self):
        """Detect SOLID principle violations."""
        print("🔍 Analyzing SOLID principle violations...")
        
        # Single Responsibility Principle violations
        for pattern_type, patterns in self.code_patterns.items():
            if pattern_type == "large_classes":
                for pattern in patterns:
                    if pattern['method_count'] > 15 or pattern['line_count'] > 500:
                        self.add_issue(
                            "MEDIUM", "VIOLATION",
                            f"Potential SRP violation: Class '{pattern['name']}' has {pattern['method_count']} methods and {pattern['line_count']} lines",
                            pattern['file'],
                            pattern['line'],
                            recommendation="Consider breaking down into smaller, focused classes",
                            impact="Difficult to test, maintain, and understand"
                        )
            
            elif pattern_type == "god_functions":
                for pattern in patterns:
                    if pattern['line_count'] > 50:
                        self.add_issue(
                            "MEDIUM", "VIOLATION",
                            f"Potential function complexity violation: '{pattern['name']}' has {pattern['line_count']} lines",
                            pattern['file'],
                            pattern['line'],
                            recommendation="Break down into smaller, focused functions",
                            # TODO: Consider extracting this block into a separate method
                            impact="Hard to test and maintain"
                        )

    def analyze_security_vulnerabilities(self):
        """Detect security anti-patterns and vulnerabilities."""
        print("🔍 Analyzing security vulnerabilities...")
        
        security_patterns = [
            # SQL Injection patterns
            (r'f".*SELECT.*{.*}"', "SQL Injection risk: f-string in SQL query", "HIGH"),
            (r'f\'.*SELECT.*{.*}\'', "SQL Injection risk: f-string in SQL query", "HIGH"),
            (r'\.format\(.*\).*SELECT', "SQL Injection risk: .format() in SQL", "HIGH"),
            (r'%.*%.*SELECT', "SQL Injection risk: % formatting in SQL", "HIGH"),
            
            # Unsafe serialization
            (r'pickle\.loads?\(', "Security risk: pickle deserialization", "HIGH"),
            (r'eval\(', "Security risk: eval() usage", "CRITICAL"),
            (r'exec\(', "Security risk: exec() usage", "CRITICAL"),
            
            # Weak hashing
            (r'hashlib\.md5\(', "Security risk: MD5 hashing", "MEDIUM"),
            (r'hashlib\.sha1\(', "Security risk: SHA1 hashing", "MEDIUM"),
            
            # Hardcoded secrets
            (r'password\s*=\s*["\'][^"\']+["\']', "Security risk: hardcoded password", "HIGH"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Security risk: hardcoded API key", "HIGH"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Security risk: hardcoded secret", "HIGH"),
        ]
        
        for file_path, content in self._get_all_file_contents():
            for pattern, description, severity in security_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_no = content[:match.start()].count('\n') + 1
                    self.add_issue(
                        severity, "SECURITY",
                        description,
                        file_path,
                        line_no,
                        # TODO: Consider extracting this block into a separate method
                        recommendation="Use parameterized queries, safe serialization, strong hashing",
                        impact="Potential data breach or system compromise"
                    )

    def analyze_performance_issues(self):
        """Detect performance anti-patterns."""
        print("🔍 Analyzing performance issues...")
        
        performance_patterns = [
            # Inefficient loops
            (r'for.*in.*range\(len\(.*\)\)', "Performance: inefficient loop pattern", "LOW"),
            
            # Inefficient string operations
            (r'\+\=.*["\']', "Performance: string concatenation in loop", "MEDIUM"),
            
            # Import issues
            (r'import \*', "Performance: wildcard imports", "MEDIUM"),
            
            # Database issues (N+1 queries)
            (r'for.*in.*:\s*.*\.execute\(', "Performance: potential N+1 query pattern", "HIGH"),
        ]
        
        for file_path, content in self._get_all_file_contents():
            for pattern, description, severity in performance_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_no = content[:match.start()].count('\n') + 1
                    self.add_issue(
                        severity, "PERFORMANCE",
                        description,
                        file_path,
                        # TODO: Consider extracting this block into a separate method
                        line_no,
                        recommendation="Optimize data access patterns and avoid inefficient operations",
                        impact="Degraded system performance"
                    )

    def analyze_hidden_coupling(self):
        """Detect hidden coupling and tight dependencies."""
        print("🔍 Analyzing hidden coupling...")
        
        # Analyze import patterns for excessive dependencies
        module_import_counts = defaultdict(int)
        
        for module, imports in self.imports_graph.items():
            module_import_counts[module] = len(imports)
        
        # Flag modules with excessive dependencies
        for module, import_count in module_import_counts.items():
            if import_count > 20:
                self.add_issue(
                    "MEDIUM", "COUPLING",
                    # TODO: Consider extracting this block into a separate method
                    f"High coupling: module '{module}' imports {import_count} other modules",
                    module,
                    recommendation="Consider dependency injection or facade patterns",
                    impact="Makes testing difficult and increases change ripple effects"
                )

    def analyze_architectural_consistency(self):
        """Check for architectural consistency violations."""
        print("🔍 Analyzing architectural consistency...")
        
        # Check layer violations (e.g., utils importing from services)
        layer_hierarchy = {
            'utils': 0,
            'models': 1, 
            'database': 2,
            'services': 3,
            'components': 4,
            'pages': 5,
            'streamlit_app': 6
        }
        
        for module, imports in self.imports_graph.items():
            module_parts = module.split('/')
            if len(module_parts) >= 2:
                module_layer = None
                for part in module_parts:
                    if part in layer_hierarchy:
                        module_layer = part
                        break
                
                if module_layer:
                    for imported in imports:
                        imported_parts = imported.split('/')
                        for part in imported_parts:
                            if part in layer_hierarchy:
                                imported_layer = part
                                break
                        else:
                            continue
                        
                        # Check if importing from higher layer
                        if (module_layer in layer_hierarchy and 
                            imported_layer in layer_hierarchy and
                            layer_hierarchy[module_layer] < layer_hierarchy[imported_layer]):
                            
                            self.add_issue(
                                "HIGH", "VIOLATION",
                                f"Layer violation: '{module_layer}' layer importing from '{imported_layer}' layer",
                                module,
                                recommendation="Invert dependencies or use abstraction layers",
                                impact="Violates clean architecture principles"
                            )

    def _hash_function_structure(self, func_info: Dict) -> str:
        """Create a hash representing the structure of a function."""
        # This is a simplified version - could be enhanced with AST analysis
        structure_elements = [
            # TODO: Consider extracting this block into a separate method
            func_info.get('name', ''),
            str(func_info.get('arg_count', 0)),
            str(func_info.get('line_count', 0)),
            func_info.get('return_type', ''),
        ]
        return hashlib.md5('|'.join(structure_elements).encode()).hexdigest()

    def _get_all_file_contents(self):
        """Generator that yields (file_path, content) for all Python files."""
        streamlit_dir = Path("streamlit_extension")
        if not streamlit_dir.exists():
            return
        
        for file_path in streamlit_dir.rglob("*.py"):
            # Skip backup files and test files
            if 'copy' in str(file_path) or '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                yield str(file_path), content
            except Exception:
                continue

    def collect_metadata(self):
        """Collect metadata about the codebase for analysis."""
        print("📊 Collecting codebase metadata...")
        
        for file_path, content in self._get_all_file_contents():
            try:
                tree = ast.parse(content, filename=file_path)
                
                class MetadataCollector(ast.NodeVisitor):
                    def __init__(self, analyzer, file_path):
                        self.analyzer = analyzer
                        self.file_path = file_path
                    
                    def visit_Import(self, node):
                        for alias in node.names:
                            self.analyzer.imports_graph[file_path].add(alias.name)
                    
                    def visit_ImportFrom(self, node):
                        if node.module:
                            self.analyzer.imports_graph[file_path].add(node.module)
                    
                    def visit_FunctionDef(self, node):
                        end_line = getattr(node, 'end_lineno', None)
                        if end_line is None:
                            # Estimate line count based on content
                            end_line = node.lineno + 10  # reasonable default
                        
                        func_info = {
                            'name': node.name,
                            'file': file_path,
                            'line': node.lineno,
                            'arg_count': len(node.args.args) if node.args else 0,
                            'line_count': max(1, end_line - node.lineno)
                        }
                        
                        signature = f"{node.name}({func_info['arg_count']})"
                        self.analyzer.function_signatures[signature].append(func_info)
                        
                        # Check for god functions
                        if func_info['line_count'] > 30:
                            self.analyzer.code_patterns['god_functions'].append(func_info)
                    
                    def visit_ClassDef(self, node):
                        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                        end_line = getattr(node, 'end_lineno', None)
                        if end_line is None:
                            end_line = node.lineno + len(methods) * 10  # estimate
                        
                        class_info = {
                            'name': node.name,
                            'file': file_path,
                            'line': node.lineno,
                            'method_count': len(methods),
                            'line_count': max(1, end_line - node.lineno)
                        }
                        
                        # TODO: Consider extracting this block into a separate method
                        self.analyzer.code_patterns['large_classes'].append(class_info)
                
                collector = MetadataCollector(self, file_path)
                collector.visit(tree)
                
            except Exception as e:
                continue

    def generate_report(self):
        """Generate comprehensive audit report."""
        print("\n" + "="*80)
        print("🕵️ DEEP ARCHITECTURE AUDIT REPORT")
        print("="*80)
        
        # Group issues by severity
        issues_by_severity = defaultdict(list)
        for issue in self.issues:
            issues_by_severity[issue.severity].append(issue)
        
        # Group issues by category
        issues_by_category = defaultdict(list)
        for issue in self.issues:
            issues_by_category[issue.category].append(issue)
        
        # Summary statistics
        total_issues = len(self.issues)
        print(f"\n📊 SUMMARY STATISTICS")
        print(f"Total Issues Found: {total_issues}")
        print(f"Critical Issues: {len(issues_by_severity['CRITICAL'])}")
        print(f"High Issues: {len(issues_by_severity['HIGH'])}")
        print(f"Medium Issues: {len(issues_by_severity['MEDIUM'])}")
        print(f"Low Issues: {len(issues_by_severity['LOW'])}")
        
        print(f"\n📋 ISSUES BY CATEGORY")
        for category, issues in issues_by_category.items():
            print(f"{category}: {len(issues)} issues")
        
        # Detailed issues report
        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        
        for severity in severity_order:
            if severity in issues_by_severity:
                print(f"\n🚨 {severity} ISSUES ({len(issues_by_severity[severity])})")
                print("-" * 60)
                
                for issue in issues_by_severity[severity][:10]:  # Limit to top 10
                    print(f"📁 {issue.file_path}:{issue.line_number}")
                    print(f"   {issue.description}")
                    if issue.recommendation:
                        print(f"   💡 Recommendation: {issue.recommendation}")
                    if issue.impact:
                        print(f"   ⚡ Impact: {issue.impact}")
                    print()
        
        # Risk assessment
        risk_score = (
            len(issues_by_severity['CRITICAL']) * 10 +
            len(issues_by_severity['HIGH']) * 5 +
            len(issues_by_severity['MEDIUM']) * 2 +
            len(issues_by_severity['LOW']) * 1
        )
        
        print(f"\n🎯 RISK ASSESSMENT")
        print(f"Risk Score: {risk_score}")
        
        if risk_score == 0:
            print("✅ EXCELLENT: No significant architectural issues detected!")
            return True
        elif risk_score <= 10:
            print("✅ GOOD: Minor issues that can be addressed incrementally")
            return True
        elif risk_score <= 50:
            print("⚠️ MODERATE: Several issues require attention")
            return False
        else:
            print("🚨 HIGH RISK: Critical architectural issues need immediate attention")
            return False

    def run_deep_analysis(self):
        """Run the complete deep architecture analysis."""
        self.collect_metadata()
        self.analyze_circular_dependencies()
        self.analyze_semantic_duplication()
        self.analyze_solid_violations()
        self.analyze_security_vulnerabilities()
        self.analyze_performance_issues()
        self.analyze_hidden_coupling()
        self.analyze_architectural_consistency()
        
        return self.generate_report()

def main():
    analyzer = DeepArchitectureAnalyzer()
    success = analyzer.run_deep_analysis()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)