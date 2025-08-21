#!/usr/bin/env python3
"""
🎯 MIXED RESPONSIBILITIES ANALYZER - Phase 10 SRP Fixes

Identifies and fixes functions that violate Single Responsibility Principle.
Based on quinta camada audit findings: 12 functions with mixed responsibilities.

Target pattern from audit:
"Function 'get_tasks' has mixed responsibilities: database, logging, ui"
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass
import json

@dataclass
class ResponsibilityViolation:
    """Data class for responsibility violations."""
    function_name: str
    file_path: str
    line_number: int
    responsibilities: Set[str]
    severity: str
    code_snippet: str
    suggested_refactor: str

class MixedResponsibilitiesAnalyzer:
    """Analyzes and fixes SRP violations systematically."""
    
    # TODO: Consider extracting this block into a separate method
    def __init__(self):
        self.violations: List[ResponsibilityViolation] = []
        self.files_analyzed = 0
        self.functions_analyzed = 0
        
        # Keywords that indicate different responsibilities
        self.responsibility_keywords = {
            'database': {
                'cursor', 'execute', 'fetchall', 'fetchone', 'commit', 'rollback',
                'get_connection', 'with_db', 'SELECT', 'INSERT', 'UPDATE', 'DELETE',
                'db_manager', 'DatabaseManager', 'sqlite3', 'query', 'transaction'
            },
            'logging': {
                'logger', 'log_', 'debug', 'info', 'warning', 'error', 'critical',
                'logging', 'print(', 'console.log', 'log.', 'audit_', 'track_'
            },
            'ui': {
                'st.', 'streamlit', 'render', 'display', 'show_', 'markdown',
                'error', 'success', 'warning', 'info', 'container', 'column',
                'selectbox', 'text_input', 'button', 'form', 'metric'
            },
            'validation': {
                'validate_', 'check_', 'verify_', 'sanitize_', 'clean_', 
                'is_valid', 'has_valid', 'ValidationError', 'ValueError'
            },
            'business_logic': {
                'calculate_', 'compute_', 'process_', 'transform_', 'convert_',
                'algorithm', 'formula', 'rule_', 'policy_', 'strategy_'
            },
            'file_io': {
                'open(', 'read(', 'write(', 'Path(', 'os.path', 'json.load',
                'json.dump', 'csv.', 'with open', 'file_', 'save_', 'load_'
            },
            'network': {
                'requests.', 'urllib', 'http', 'api_', 'fetch_', 'post_',
                'get_', 'put_', 'delete_', 'response', 'status_code'
            },
            'auth': {
                'auth', 'login', 'logout', 'authenticate', 'authorize',
                'token', 'session', 'user_', 'permission', 'role'
            }
        }
    
# TODO: Consider extracting this block into a separate method
    
    def analyze_all_files(self) -> Dict[str, Any]:
        """Analyze all Python files for SRP violations."""
        print("🎯 ANALYZING MIXED RESPONSIBILITIES...")
        print("=" * 60)
        
        streamlit_dir = Path("streamlit_extension")
        if not streamlit_dir.exists():
            return {"error": "streamlit_extension directory not found"}
        
        # Analyze all Python files
        for py_file in streamlit_dir.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue
                
            self.files_analyzed += 1
            self._analyze_file(py_file)
        
        # TODO: Consider extracting this block into a separate method
        # Generate comprehensive report
        return self._generate_analysis_report()
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file for SRP violations."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Analyze each function
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self.functions_analyzed += 1
                    self._analyze_function(node, file_path, content)
                    
# TODO: Consider extracting this block into a separate method
                    
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def _analyze_function(self, node: ast.FunctionDef, file_path: Path, content: str) -> None:
        """Analyze a single function for mixed responsibilities."""
        function_code = self._extract_function_code(node, content)
        responsibilities = self._identify_responsibilities(function_code)
        
        # Check if function has mixed responsibilities (2+ major categories)
        if len(responsibilities) >= 2:
            # Filter out minor responsibilities to focus on major violations
            major_responsibilities = self._filter_major_responsibilities(responsibilities, function_code)
            
            if len(major_responsibilities) >= 2:
                violation = ResponsibilityViolation(
                    function_name=node.name,
                    file_path=str(file_path),
                    line_number=node.lineno,
                    responsibilities=major_responsibilities,
                    # TODO: Consider extracting this block into a separate method
                    severity=self._calculate_severity(major_responsibilities, function_code),
                    code_snippet=function_code[:300] + "..." if len(function_code) > 300 else function_code,
                    suggested_refactor=self._suggest_refactor(node.name, major_responsibilities)
                )
                self.violations.append(violation)
    
    def _extract_function_code(self, node: ast.FunctionDef, content: str) -> str:
        """Extract the full code of a function."""
        lines = content.split('\n')
        start_line = node.lineno - 1
        
        # Find the end of the function by indentation
        end_line = len(lines)
        base_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
        
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if line.strip() and (len(line) - len(line.lstrip())) <= base_indent:
                end_line = i
                break
        
        return '\n'.join(lines[start_line:end_line])
    
    def _identify_responsibilities(self, code: str) -> Set[str]:
        """Identify what responsibilities a function has."""
        responsibilities = set()
        code_lower = code.lower()
        
# TODO: Consider extracting this block into a separate method
        
        for responsibility, keywords in self.responsibility_keywords.items():
            if any(keyword.lower() in code_lower for keyword in keywords):
                responsibilities.add(responsibility)
        
        return responsibilities
    
    def _filter_major_responsibilities(self, responsibilities: Set[str], code: str) -> Set[str]:
        """Filter to only include major responsibilities (not just incidental keywords)."""
        major_responsibilities = set()
        
        for responsibility in responsibilities:
            keyword_count = 0
            keywords = self.responsibility_keywords[responsibility]
            
            for keyword in keywords:
                keyword_count += code.lower().count(keyword.lower())
            
            # Only include if there are multiple occurrences or strong indicators
            if keyword_count >= 2 or self._has_strong_indicator(responsibility, code):
                major_responsibilities.add(responsibility)
        
        return major_responsibilities
    
    def _has_strong_indicator(self, responsibility: str, code: str) -> bool:
        """Check for strong indicators of a responsibility."""
        strong_indicators = {
            'database': ['cursor.execute', 'get_connection', 'with_db', 'transaction'],
            'ui': ['st.error', 'st.success', 'st.warning', 'st.markdown', 'st.container'],
            'logging': ['logger.error', 'logger.info', 'logger.debug', 'print(f"'],
            # TODO: Consider extracting this block into a separate method
            'validation': ['ValidationError', 'is_valid_', 'sanitize_'],
            'business_logic': ['calculate_', 'algorithm', 'business_rule'],
            'file_io': ['with open', 'json.dump', 'Path('],
            'auth': ['authenticate', 'authorize', 'session_state']
        }
        
        indicators = strong_indicators.get(responsibility, [])
        return any(indicator in code for indicator in indicators)
    
    def _calculate_severity(self, responsibilities: Set[str], code: str) -> str:
        # TODO: Consider extracting this block into a separate method
        """Calculate severity of the SRP violation."""
        if len(responsibilities) >= 4:
            return "CRITICAL"
        elif len(responsibilities) == 3:
            return "HIGH"
        elif 'database' in responsibilities and 'ui' in responsibilities:
            return "HIGH"  # Database + UI is particularly problematic
        else:
            return "MEDIUM"
    
    def _suggest_refactor(self, function_name: str, responsibilities: Set[str]) -> str:
        """Suggest refactoring approach for the function."""
        suggestions = []
        
        if 'database' in responsibilities:
            suggestions.append(f"Extract database operations to {function_name}_data_layer()")
        
        if 'ui' in responsibilities:
            suggestions.append(f"Extract UI rendering to {function_name}_ui_layer()")
        
        # TODO: Consider extracting this block into a separate method
        if 'logging' in responsibilities:
            suggestions.append(f"Extract logging to {function_name}_audit_layer()")
        
        if 'validation' in responsibilities:
            suggestions.append(f"Extract validation to {function_name}_validator()")
        
        if 'business_logic' in responsibilities:
            suggestions.append(f"Extract business logic to {function_name}_processor()")
        
        return " + ".join(suggestions)
    
    def _generate_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        # Sort violations by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
        sorted_violations = sorted(
            self.violations, 
            key=lambda v: (severity_order.get(v.severity, 3), v.function_name)
        )
        
        # Group by severity
        by_severity = {}
        for violation in sorted_violations:
            severity = violation.severity
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(violation)
        
        # Generate statistics
        responsibility_counts = {}
        for violation in self.violations:
            for resp in violation.responsibilities:
                responsibility_counts[resp] = responsibility_counts.get(resp, 0) + 1
        
        return {
            "summary": {
                # TODO: Consider extracting this block into a separate method
                "files_analyzed": self.files_analyzed,
                "functions_analyzed": self.functions_analyzed,
                "violations_found": len(self.violations),
                "critical_violations": len(by_severity.get("CRITICAL", [])),
                "high_violations": len(by_severity.get("HIGH", [])),
                "medium_violations": len(by_severity.get("MEDIUM", [])),
            },
            "violations_by_severity": by_severity,
            "responsibility_frequency": responsibility_counts,
            "top_violations": sorted_violations[:12],  # Focus on top 12 as mentioned in audit
        }
    
    def generate_detailed_report(self, output_file: str = "mixed_responsibilities_report.json"):
        """Generate detailed JSON report."""
        report = self.analyze_all_files()
        
        # Convert violations to serializable format
        serializable_violations = []
        for violation in self.violations:
            serializable_violations.append({
                "function_name": violation.function_name,
                "file_path": violation.file_path,
                "line_number": violation.line_number,
                "responsibilities": list(violation.responsibilities),
                "severity": violation.severity,
                "code_snippet": violation.code_snippet,
                "suggested_refactor": violation.suggested_refactor
            })
        
        # Convert by_severity to serializable format
        serializable_by_severity = {}
        for severity, violations in report.get("violations_by_severity", {}).items():
            serializable_by_severity[severity] = []
            for violation in violations:
                serializable_by_severity[severity].append({
                    "function_name": violation.function_name,
                    "file_path": violation.file_path,
                    "line_number": violation.line_number,
                    "responsibilities": list(violation.responsibilities),
                    "severity": violation.severity,
                    "code_snippet": violation.code_snippet,
                    "suggested_refactor": violation.suggested_refactor
                })
        
        # Convert top_violations to serializable format
        serializable_top_violations = []
        for violation in report.get("top_violations", []):
            serializable_top_violations.append({
                "function_name": violation.function_name,
                "file_path": violation.file_path,
                "line_number": violation.line_number,
                "responsibilities": list(violation.responsibilities),
                "severity": violation.severity,
                "code_snippet": violation.code_snippet,
                "suggested_refactor": violation.suggested_refactor
            })
        
        # Create fully serializable report
        # TODO: Consider extracting this block into a separate method
        serializable_report = {
            "summary": report["summary"],
            "violations_by_severity": serializable_by_severity,
            "responsibility_frequency": report["responsibility_frequency"],
            "top_violations": serializable_top_violations,
            "all_violations": serializable_violations
        }
        
        with open(output_file, 'w') as f:
            json.dump(serializable_report, f, indent=2)
        
        return output_file
    
    def print_analysis_summary(self):
        """Print human-readable analysis summary."""
        report = self.analyze_all_files()
        
        print(f"\n📊 MIXED RESPONSIBILITIES ANALYSIS SUMMARY:")
        print(f"   Files analyzed: {report['summary']['files_analyzed']}")
        print(f"   Functions analyzed: {report['summary']['functions_analyzed']}")
        print(f"   SRP violations found: {report['summary']['violations_found']}")
        print(f"   Critical: {report['summary']['critical_violations']}")
        print(f"   High: {report['summary']['high_violations']}")
        print(f"   Medium: {report['summary']['medium_violations']}")
        
        print(f"\n🔍 TOP 12 VIOLATIONS TO FIX:")
        for i, violation in enumerate(report['top_violations'][:12], 1):
            print(f"   {i}. {violation.function_name} ({violation.file_path})")
            print(f"      Responsibilities: {', '.join(violation.responsibilities)}")
            print(f"      Severity: {violation.severity}")
            print(f"      Refactor: {violation.suggested_refactor}")
            print()
        
        print(f"🎯 RESPONSIBILITY FREQUENCY:")
        for resp, count in sorted(report['responsibility_frequency'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {resp}: {count} functions")


# TODO: Consider extracting this block into a separate method
def main():
    """Main analysis execution."""
    print("🎯 MIXED RESPONSIBILITIES ANALYZER - PHASE 10")
    print("=" * 60)
    print("Identifying 12 functions that violate Single Responsibility Principle\n")
    
    analyzer = MixedResponsibilitiesAnalyzer()
    
    # Generate detailed report
    report_file = analyzer.generate_detailed_report()
    
    # Print summary
    analyzer.print_analysis_summary()
    
    print(f"\n📋 DETAILED REPORT SAVED: {report_file}")
    print(f"📈 NEXT: Create systematic refactoring plan for top 12 violations")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)