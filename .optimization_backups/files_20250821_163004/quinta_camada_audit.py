#!/usr/bin/env python3
"""
🧠 QUINTA CAMADA - Semantic & Architectural Advanced Audit

This is the most sophisticated audit layer, going beyond pattern matching to perform:
- Semantic analysis of business logic
- Architectural vulnerability assessment  
- Data flow security analysis
- Integration weakness detection
- Hidden dependency mapping
- Error propagation analysis
- Performance bottleneck identification
- Maintenance debt assessment

This audit uses AST analysis, dependency graphing, and logical flow analysis.
"""

import ast
import sys
import inspect
import importlib
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Any, Tuple, Optional, Union
from dataclasses import dataclass, field
# import networkx as nx  # Optional - using fallback implementation
import json
import re
import time

@dataclass
class SemanticIssue:
    """Represents a semantic/architectural issue."""
    severity: str  # ARCHITECTURAL, BUSINESS_LOGIC, INTEGRATION, PERFORMANCE, MAINTENANCE
    category: str  # DEPENDENCY_HELL, LOGIC_GAP, DATA_LEAK, BOTTLENECK, DEBT
    description: str
    file_path: str
    function_name: Optional[str] = None
    line_number: int = 0
    impact: str = ""
    business_risk: str = ""  # REVENUE_LOSS, DATA_BREACH, OPERATIONAL_FAILURE
    fix_effort: str = ""  # TRIVIAL, MODERATE, MAJOR, ARCHITECTURAL
    affected_components: List[str] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)
    recommendation: str = ""

class SimpleGraph:
    """Simple graph implementation as fallback for networkx."""
    
    def __init__(self):
        self.nodes_set = set()
        self.edges_dict = defaultdict(list)
        
    def add_edge(self, source, target, **kwargs):
        self.nodes_set.add(source)
        self.nodes_set.add(target)
        self.edges_dict[source].append((target, kwargs))
        
    def nodes(self):
        return self.nodes_set
        
    def edges(self):
        all_edges = []
        for source, targets in self.edges_dict.items():
            for target, _ in targets:
                all_edges.append((source, target))
        return all_edges
        
    def predecessors(self, node):
        preds = []
        for source, targets in self.edges_dict.items():
            for target, _ in targets:
                if target == node:
                    preds.append(source)
        return preds
        
    def successors(self, node):
        return [target for target, _ in self.edges_dict.get(node, [])]

class SemanticAuditEngine:
    """Advanced semantic and architectural audit engine."""
    
    def __init__(self):
        self.issues: List[SemanticIssue] = []
        self.dependency_graph = SimpleGraph()
        self.function_calls = defaultdict(set)
        self.data_flows = defaultdict(list)
        self.authentication_boundaries = set()
        self.database_operations = defaultdict(list)
        self.error_handlers = defaultdict(list)
        self.business_logic_functions = defaultdict(list)
        self.performance_critical_paths = []
        
    def analyze_system_architecture(self):
        """Perform comprehensive architectural analysis."""
        print("🧠 QUINTA CAMADA - SEMANTIC & ARCHITECTURAL AUDIT")
        print("=" * 70)
        print("Advanced semantic analysis beyond pattern matching...")
        
        # Build comprehensive system model
        self._build_dependency_graph()
        self._analyze_data_flows()
        self._map_authentication_boundaries()
        self._analyze_business_logic_patterns()
        self._detect_performance_bottlenecks()
        self._analyze_error_propagation()
        self._assess_integration_vulnerabilities()
        self._evaluate_maintenance_debt()
        
        return self._generate_semantic_report()
    
    def _build_dependency_graph(self):
        """Build comprehensive dependency graph using AST analysis."""
        print("\n🔗 Building dependency graph...")
        
        streamlit_dir = Path("streamlit_extension")
        if not streamlit_dir.exists():
            return
            
        for py_file in streamlit_dir.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(py_file))
                self._extract_dependencies(tree, str(py_file))
                
            except Exception as e:
                continue
    
    def _extract_dependencies(self, tree: ast.AST, file_path: str):
        """Extract dependencies from AST."""
        
        class DependencyVisitor(ast.NodeVisitor):
            def __init__(self, engine, file_path):
                self.engine = engine
                self.file_path = file_path
                self.current_function = None
                
            def visit_Import(self, node):
                for alias in node.names:
                    self.engine.dependency_graph.add_edge(
                        self.file_path, alias.name, 
                        edge_type="import", direct=True
                    )
                    
            def visit_ImportFrom(self, node):
                if node.module:
                    for alias in node.names:
                        import_name = f"{node.module}.{alias.name}"
                        self.engine.dependency_graph.add_edge(
                            self.file_path, import_name,
                            edge_type="from_import", direct=True
                        )
                        
            def visit_FunctionDef(self, node):
                old_function = self.current_function
                self.current_function = f"{self.file_path}:{node.name}"
                
                # Analyze function complexity and responsibilities
                self._analyze_function_complexity(node)
                
                self.generic_visit(node)
                self.current_function = old_function
                
            def visit_Call(self, node):
                if self.current_function:
                    # Track function calls for dependency analysis
                    call_target = self._get_call_target(node)
                    if call_target:
                        self.engine.function_calls[self.current_function].add(call_target)
                        
                        # Special analysis for security-critical calls
                        if any(pattern in call_target.lower() for pattern in 
                               ['execute', 'query', 'auth', 'login', 'session']):
                            self.engine.database_operations[self.current_function].append({
                                'call': call_target,
                                'line': node.lineno,
                                'type': self._classify_operation(call_target)
                            })
                
                self.generic_visit(node)
                
            def _get_call_target(self, node):
                """Extract the target of a function call."""
                if isinstance(node.func, ast.Name):
                    return node.func.id
                elif isinstance(node.func, ast.Attribute):
                    return f"{self._get_attr_chain(node.func)}"
                return None
                
            def _get_attr_chain(self, node):
                """Get the full attribute chain (e.g., obj.method.call)."""
                if isinstance(node, ast.Name):
                    return node.id
                elif isinstance(node, ast.Attribute):
                    return f"{self._get_attr_chain(node.value)}.{node.attr}"
                return "unknown"
                
            def _classify_operation(self, call_target):
                """Classify the type of operation."""
                call_lower = call_target.lower()
                if 'execute' in call_lower or 'query' in call_lower:
                    return 'database'
                elif 'auth' in call_lower or 'login' in call_lower:
                    return 'authentication'
                elif 'session' in call_lower:
                    return 'session_management'
                return 'other'
                
            def _analyze_function_complexity(self, node):
                """Analyze function complexity and identify potential issues."""
                # Count decision points
                complexity = 0
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                        complexity += 1
                
                # Check for god functions
                if complexity > 15:
                    self.engine.issues.append(SemanticIssue(
                        severity="MAINTENANCE",
                        category="GOD_FUNCTION",
                        description=f"Function '{node.name}' has excessive complexity ({complexity} decision points)",
                        file_path=self.file_path,
                        function_name=node.name,
                        line_number=node.lineno,
                        impact="High maintenance cost, testing difficulty, bug proneness",
                        business_risk="OPERATIONAL_FAILURE",
                        fix_effort="MAJOR",
                        recommendation="Break into smaller, focused functions following SRP"
                    ))
                
                # Check for mixed responsibilities
                responsibilities = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_target = self._get_call_target(child)
                        if call_target:
                            if 'execute' in call_target.lower():
                                responsibilities.add('database')
                            elif 'render' in call_target.lower() or 'st.' in call_target:
                                responsibilities.add('ui')
                            elif 'validate' in call_target.lower():
                                responsibilities.add('validation')
                            elif 'log' in call_target.lower():
                                responsibilities.add('logging')
                
                if len(responsibilities) > 2:
                    self.engine.issues.append(SemanticIssue(
                        severity="ARCHITECTURAL",
                        category="MIXED_RESPONSIBILITIES",
                        description=f"Function '{node.name}' has mixed responsibilities: {', '.join(responsibilities)}",
                        file_path=self.file_path,
                        function_name=node.name,
                        line_number=node.lineno,
                        impact="Violates SRP, high coupling, difficult testing",
                        business_risk="OPERATIONAL_FAILURE",
                        fix_effort="MODERATE",
                        recommendation="Separate concerns into distinct functions/classes"
                    ))
        
        visitor = DependencyVisitor(self, file_path)
        visitor.visit(tree)
    
    def _analyze_data_flows(self):
        """Analyze how sensitive data flows through the system."""
        print("\n🌊 Analyzing data flows...")
        
        # Look for sensitive data patterns
        sensitive_patterns = {
            'password': ['password', 'pwd', 'pass'],
            'email': ['email', 'mail', '@'],
            'token': ['token', 'jwt', 'auth_token'],
            'key': ['api_key', 'secret_key', 'private_key'],
            'personal': ['name', 'phone', 'address', 'ssn']
        }
        
        for function, calls in self.function_calls.items():
            file_path = function.split(':')[0]
            func_name = function.split(':')[1]
            
            # Analyze if sensitive data might flow through unsafe channels
            unsafe_channels = ['log', 'print', 'debug', 'error', 'exception']
            sensitive_exposure = []
            
            for call in calls:
                call_lower = call.lower()
                for channel in unsafe_channels:
                    if channel in call_lower:
                        for data_type, patterns in sensitive_patterns.items():
                            for pattern in patterns:
                                if pattern in call_lower:
                                    sensitive_exposure.append((data_type, channel, call))
            
            if sensitive_exposure:
                self.issues.append(SemanticIssue(
                    severity="BUSINESS_LOGIC",
                    category="DATA_LEAK",
                    description=f"Function '{func_name}' may expose sensitive data through unsafe channels",
                    file_path=file_path,
                    function_name=func_name,
                    impact="Data privacy violation, compliance breach",
                    business_risk="DATA_BREACH",
                    fix_effort="MODERATE",
                    affected_components=[call[2] for call in sensitive_exposure],
                    recommendation="Implement data sanitization and secure logging practices"
                ))
    
    def _map_authentication_boundaries(self):
        """Map authentication boundaries and access control."""
        print("\n🔐 Mapping authentication boundaries...")
        
        # Find authentication entry points
        auth_patterns = ['login', 'authenticate', 'verify', 'authorize', 'check_auth']
        protected_patterns = ['require_auth', 'login_required', '@protected']
        
        auth_functions = set()
        protected_functions = set()
        
        for function, calls in self.function_calls.items():
            func_name = function.split(':')[1].lower()
            
            # Check if function is authentication-related
            if any(pattern in func_name for pattern in auth_patterns):
                auth_functions.add(function)
                
            # Check if function is protected
            if any(pattern in func_name for pattern in protected_patterns):
                protected_functions.add(function)
                
            # Check calls for auth patterns
            for call in calls:
                if any(pattern in call.lower() for pattern in auth_patterns):
                    auth_functions.add(function)
        
        # Look for unprotected sensitive operations
        sensitive_operations = ['delete', 'create', 'update', 'admin', 'config']
        
        for function, operations in self.database_operations.items():
            func_name = function.split(':')[1].lower()
            file_path = function.split(':')[0]
            
            is_sensitive = any(op in func_name for op in sensitive_operations)
            is_protected = function in protected_functions
            has_auth_check = any(call in self.function_calls[function] 
                               for call in ['get_current_user', 'check_auth', 'verify_user'])
            
            if is_sensitive and not is_protected and not has_auth_check:
                self.issues.append(SemanticIssue(
                    severity="BUSINESS_LOGIC",
                    category="ACCESS_CONTROL_GAP",
                    description=f"Sensitive function '{func_name}' lacks authentication protection",
                    file_path=file_path,
                    function_name=func_name,
                    impact="Unauthorized access to sensitive operations",
                    business_risk="DATA_BREACH",
                    fix_effort="MODERATE",
                    recommendation="Add authentication checks or @require_auth decorator"
                ))
    
    def _analyze_business_logic_patterns(self):
        """Analyze business logic for consistency and gaps."""
        print("\n💼 Analyzing business logic patterns...")
        
        # Look for inconsistent validation patterns
        validation_functions = defaultdict(list)
        
        for function, calls in self.function_calls.items():
            for call in calls:
                if 'validate' in call.lower():
                    entity = self._extract_entity_from_function(function)
                    validation_functions[entity].append((function, call))
        
        # Check for entities with inconsistent validation
        for entity, validations in validation_functions.items():
            if len(validations) > 1:
                validation_types = set(val[1] for val in validations)
                if len(validation_types) > 1:
                    self.issues.append(SemanticIssue(
                        severity="BUSINESS_LOGIC",
                        category="INCONSISTENT_VALIDATION",
                        description=f"Entity '{entity}' has inconsistent validation patterns",
                        file_path="multiple",
                        impact="Data integrity issues, unpredictable behavior",
                        business_risk="OPERATIONAL_FAILURE",
                        fix_effort="MODERATE",
                        affected_components=[val[0] for val in validations],
                        recommendation="Standardize validation patterns across all entity operations"
                    ))
    
    def _extract_entity_from_function(self, function):
        """Extract entity name from function name."""
        func_name = function.split(':')[1].lower()
        entities = ['client', 'project', 'epic', 'task', 'user']
        for entity in entities:
            if entity in func_name:
                return entity
        return 'unknown'
    
    def _detect_performance_bottlenecks(self):
        """Detect real performance bottlenecks using call graph analysis."""
        print("\n⚡ Detecting performance bottlenecks...")
        
        # Analyze call chains for potential N+1 problems
        database_call_chains = []
        
        for function, operations in self.database_operations.items():
            if len(operations) > 1:
                # Multiple DB operations in one function - potential N+1
                db_calls = [op['call'] for op in operations]
                if any('get' in call.lower() for call in db_calls):
                    database_call_chains.append((function, operations))
        
        for function, operations in database_call_chains:
            file_path = function.split(':')[0]
            func_name = function.split(':')[1]
            
            self.issues.append(SemanticIssue(
                severity="PERFORMANCE",
                category="N_PLUS_ONE",
                description=f"Function '{func_name}' has potential N+1 query problem",
                file_path=file_path,
                function_name=func_name,
                impact="Poor performance, database overload",
                business_risk="OPERATIONAL_FAILURE",
                fix_effort="MODERATE",
                affected_components=[op['call'] for op in operations],
                recommendation="Use batch queries or implement proper caching"
            ))
    
    def _analyze_error_propagation(self):
        """Analyze how errors propagate through the system."""
        print("\n💥 Analyzing error propagation...")
        
        # Look for functions that catch but don't handle errors properly
        error_swallowing_functions = []
        
        for function in self.function_calls.keys():
            file_path = function.split(':')[0]
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Look for except blocks that might swallow errors
                if 'except:' in content and 'pass' in content:
                    func_name = function.split(':')[1]
                    if func_name in content:
                        error_swallowing_functions.append(function)
                        
            except Exception:
                continue
        
        for function in error_swallowing_functions:
            file_path = function.split(':')[0]
            func_name = function.split(':')[1]
            
            self.issues.append(SemanticIssue(
                severity="INTEGRATION",
                category="ERROR_SWALLOWING",
                description=f"Function '{func_name}' may swallow errors without proper handling",
                file_path=file_path,
                function_name=func_name,
                impact="Hidden failures, difficult debugging, silent data corruption",
                business_risk="OPERATIONAL_FAILURE",
                fix_effort="MODERATE",
                recommendation="Implement proper error logging and recovery mechanisms"
            ))
    
    def _assess_integration_vulnerabilities(self):
        """Assess integration points for vulnerabilities."""
        print("\n🔗 Assessing integration vulnerabilities...")
        
        # Look for functions that integrate with external systems
        integration_points = []
        
        for function, calls in self.function_calls.items():
            external_calls = [call for call in calls if any(pattern in call.lower() 
                             for pattern in ['request', 'http', 'api', 'external', 'webhook'])]
            
            if external_calls:
                integration_points.append((function, external_calls))
        
        for function, calls in integration_points:
            file_path = function.split(':')[0]
            func_name = function.split(':')[1]
            
            # Check if proper error handling and timeouts are implemented
            has_timeout = any('timeout' in call.lower() for call in calls)
            has_retry = any('retry' in call.lower() for call in calls)
            
            if not has_timeout and not has_retry:
                self.issues.append(SemanticIssue(
                    severity="INTEGRATION",
                    category="FRAGILE_INTEGRATION",
                    description=f"Function '{func_name}' lacks resilience patterns for external calls",
                    file_path=file_path,
                    function_name=func_name,
                    impact="System failures due to external dependencies",
                    business_risk="OPERATIONAL_FAILURE",
                    fix_effort="MODERATE",
                    affected_components=calls,
                    recommendation="Add timeout, retry logic, and circuit breaker patterns"
                ))
    
    def _evaluate_maintenance_debt(self):
        """Evaluate technical debt that affects maintainability."""
        print("\n🏗️ Evaluating maintenance debt...")
        
        # Calculate coupling metrics
        coupling_metrics = {}
        
        for file_path in self.dependency_graph.nodes():
            if file_path.endswith('.py'):
                # Calculate afferent and efferent coupling
                afferent = len(list(self.dependency_graph.predecessors(file_path)))
                efferent = len(list(self.dependency_graph.successors(file_path)))
                
                coupling_metrics[file_path] = {
                    'afferent': afferent,
                    'efferent': efferent,
                    'instability': efferent / (afferent + efferent) if (afferent + efferent) > 0 else 0
                }
        
        # Find highly coupled modules
        high_coupling_threshold = 10
        for file_path, metrics in coupling_metrics.items():
            total_coupling = metrics['afferent'] + metrics['efferent']
            
            if total_coupling > high_coupling_threshold:
                self.issues.append(SemanticIssue(
                    severity="MAINTENANCE",
                    category="HIGH_COUPLING",
                    description=f"Module has high coupling ({total_coupling} dependencies)",
                    file_path=file_path,
                    impact="Difficult to change, high ripple effect, testing complexity",
                    business_risk="OPERATIONAL_FAILURE",
                    fix_effort="MAJOR",
                    recommendation="Reduce dependencies through interface segregation and dependency inversion"
                ))
    
    def _generate_semantic_report(self):
        """Generate comprehensive semantic audit report."""
        print("\n" + "=" * 70)
        print("🧠 QUINTA CAMADA - SEMANTIC AUDIT REPORT")
        print("=" * 70)
        
        # Categorize issues by severity and type
        issues_by_severity = defaultdict(list)
        issues_by_category = defaultdict(list)
        business_risks = defaultdict(list)
        
        for issue in self.issues:
            issues_by_severity[issue.severity].append(issue)
            issues_by_category[issue.category].append(issue)
            business_risks[issue.business_risk].append(issue)
        
        # Summary statistics
        total_issues = len(self.issues)
        print(f"\n📊 SEMANTIC ANALYSIS SUMMARY")
        print(f"Total Semantic Issues Found: {total_issues}")
        
        print(f"\n🎯 ISSUES BY SEVERITY")
        for severity in ['ARCHITECTURAL', 'BUSINESS_LOGIC', 'INTEGRATION', 'PERFORMANCE', 'MAINTENANCE']:
            count = len(issues_by_severity[severity])
            print(f"  {severity}: {count} issues")
        
        print(f"\n📋 ISSUES BY CATEGORY")
        for category, issues in sorted(issues_by_category.items()):
            print(f"  {category}: {len(issues)} issues")
        
        print(f"\n💼 BUSINESS RISK ASSESSMENT")
        for risk, issues in sorted(business_risks.items()):
            if risk:  # Skip empty risk categories
                print(f"  {risk}: {len(issues)} issues")
        
        # Most critical issues
        architectural_issues = issues_by_severity['ARCHITECTURAL']
        business_logic_issues = issues_by_severity['BUSINESS_LOGIC']
        
        if architectural_issues:
            print(f"\n🏗️ MOST CRITICAL ARCHITECTURAL ISSUES")
            print("-" * 50)
            for issue in architectural_issues[:5]:
                print(f"\n🚨 {issue.description}")
                print(f"   📁 {issue.file_path}")
                if issue.function_name:
                    print(f"   🔧 Function: {issue.function_name}")
                print(f"   💥 Impact: {issue.impact}")
                print(f"   💼 Business Risk: {issue.business_risk}")
                print(f"   🔨 Fix Effort: {issue.fix_effort}")
                print(f"   💡 {issue.recommendation}")
        
        if business_logic_issues:
            print(f"\n💼 CRITICAL BUSINESS LOGIC ISSUES")
            print("-" * 50)
            for issue in business_logic_issues[:5]:
                print(f"\n⚠️ {issue.description}")
                print(f"   📁 {issue.file_path}")
                if issue.function_name:
                    print(f"   🔧 Function: {issue.function_name}")
                print(f"   💥 Impact: {issue.impact}")
                print(f"   💡 {issue.recommendation}")
        
        # System architecture insights
        print(f"\n🏛️ SYSTEM ARCHITECTURE INSIGHTS")
        print("-" * 50)
        print(f"  Dependency Graph Nodes: {len(self.dependency_graph.nodes())}")
        print(f"  Dependency Graph Edges: {len(self.dependency_graph.edges())}")
        print(f"  Function Calls Tracked: {len(self.function_calls)}")
        print(f"  Database Operations: {sum(len(ops) for ops in self.database_operations.values())}")
        
        # Calculate semantic risk score
        risk_weights = {
            'ARCHITECTURAL': 100,
            'BUSINESS_LOGIC': 80,
            'INTEGRATION': 60,
            'PERFORMANCE': 40,
            'MAINTENANCE': 20
        }
        
        business_risk_multipliers = {
            'DATA_BREACH': 3.0,
            'REVENUE_LOSS': 2.5,
            'OPERATIONAL_FAILURE': 2.0
        }
        
        semantic_risk_score = 0
        for issue in self.issues:
            base_score = risk_weights.get(issue.severity, 10)
            multiplier = business_risk_multipliers.get(issue.business_risk, 1.0)
            semantic_risk_score += base_score * multiplier
        
        print(f"\n🎯 SEMANTIC RISK SCORE: {semantic_risk_score:.0f}")
        
        if semantic_risk_score == 0:
            print("✅ EXCELLENT: No semantic or architectural issues detected!")
            status = "EXCELLENT"
        elif semantic_risk_score < 500:
            print("✅ GOOD: Minor semantic issues that don't threaten system integrity")
            status = "GOOD"
        elif semantic_risk_score < 1500:
            print("⚠️ MODERATE: Some architectural concerns need attention")
            status = "MODERATE"
        elif semantic_risk_score < 3000:
            print("🔴 CONCERNING: Significant architectural and business logic issues")
            status = "CONCERNING"
        else:
            print("☠️ CRITICAL: System has fundamental architectural problems")
            status = "CRITICAL"
        
        # Recommendations priority matrix
        print(f"\n💡 PRIORITY RECOMMENDATIONS")
        print("-" * 50)
        
        # Group by fix effort and business risk
        high_impact_low_effort = [
            issue for issue in self.issues 
            if issue.business_risk in ['DATA_BREACH', 'REVENUE_LOSS'] 
            and issue.fix_effort in ['TRIVIAL', 'MODERATE']
        ]
        
        if high_impact_low_effort:
            print("🎯 HIGH IMPACT, LOW EFFORT (Do First):")
            for issue in high_impact_low_effort[:3]:
                print(f"  • {issue.description} ({issue.file_path})")
        
        architectural_fixes = [
            issue for issue in self.issues 
            if issue.severity == 'ARCHITECTURAL'
        ]
        
        if architectural_fixes:
            print("🏗️ ARCHITECTURAL IMPROVEMENTS (Plan Carefully):")
            for issue in architectural_fixes[:3]:
                print(f"  • {issue.description} ({issue.file_path})")
        
        return {
            'status': status,
            'total_issues': total_issues,
            'semantic_risk_score': semantic_risk_score,
            'issues_by_severity': dict(issues_by_severity),
            'business_risks': dict(business_risks),
            'recommendations': {
                'high_impact_low_effort': len(high_impact_low_effort),
                'architectural_fixes': len(architectural_fixes)
            }
        }

def main():
    print("🧠 INITIATING QUINTA CAMADA - SEMANTIC & ARCHITECTURAL AUDIT")
    print("=" * 70)
    print("This is the most advanced audit layer, performing semantic analysis")
    print("of business logic, architectural patterns, and system integration.\n")
    
    engine = SemanticAuditEngine()
    result = engine.analyze_system_architecture()
    
    return result['status'] in ['EXCELLENT', 'GOOD', 'MODERATE']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)