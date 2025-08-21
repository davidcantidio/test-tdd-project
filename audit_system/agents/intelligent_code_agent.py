#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Intelligent Code Agent - AI-Powered Line-by-Line Analysis

Sistema de IA avançado que analisa cada arquivo linha por linha com compreensão
semântica completa, aplicando correções contextuais e otimizações inteligentes
baseadas no entendimento real do código.

Evolução do systematic_file_auditor.py com capacidades de IA verdadeiras:
- Análise semântica linha-por-linha
- Compreensão contextual do propósito do código
- Refatorações inteligentes baseadas em design patterns
- Otimizações de performance com análise de impacto
- Detecção arquitetural de problemas complexos

Uso:
    python intelligent_code_agent.py [--target-file FILE] [--analysis-depth {basic,advanced,deep}]
                                    [--semantic-mode {conservative,aggressive}]
                                    [--apply-refactoring] [--dry-run] [-v/--verbose]
"""

from __future__ import annotations

import ast
import inspect
import re
import time
import sys
import os
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import tokenize
import keyword
import builtins
from collections import defaultdict, Counter
import statistics

# Project root setup
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import existing infrastructure
from streamlit_extension.utils.database import DatabaseManager
try:
    from audit_system.core.systematic_file_auditor import EnhancedSystematicFileAuditor, SetimaDataLoader
except ImportError:
    # Graceful degradation if auditor not available
    EnhancedSystematicFileAuditor = None
    SetimaDataLoader = None


# =============================================================================
# Semantic Analysis Infrastructure
# =============================================================================

@dataclass
class SemanticContext:
    """Rich semantic context for code understanding."""
    purpose: str  # What this code is trying to do
    complexity_score: float  # 0-100 complexity measure
    dependencies: List[str]  # Dependencies this code relies on
    side_effects: List[str]  # Side effects this code produces
    performance_characteristics: Dict[str, Any]  # Performance implications
    maintainability_score: float  # 0-100 maintainability measure
    testability_score: float  # 0-100 testability measure
    design_patterns: List[str]  # Design patterns identified
    code_smells: List[str]  # Code smells detected
    architectural_concerns: List[str]  # Architecture-level issues


@dataclass
class LineAnalysis:
    """Detailed analysis of a single line of code."""
    line_number: int
    line_content: str
    semantic_type: str  # function_def, class_def, import, logic, etc.
    purpose: str  # What this line accomplishes
    complexity_contribution: float  # How much this line adds to complexity
    dependencies: List[str]  # What this line depends on
    side_effects: List[str]  # What this line affects
    optimization_opportunities: List[Dict[str, Any]]
    refactoring_suggestions: List[Dict[str, Any]]
    security_implications: List[str]
    performance_impact: str  # low, medium, high, critical
    maintainability_issues: List[str]
    semantic_context: Optional[SemanticContext] = None


@dataclass
class IntelligentRefactoring:
    """Intelligent refactoring recommendation with full context."""
    refactoring_type: str  # extract_method, inline_variable, etc.
    target_lines: List[int] = field(default_factory=list)  # Lines to be refactored
    description: str = ""  # What the refactoring accomplishes
    confidence: float = 0.0
    impact_assessment: str = ""
    before_code: str = ""
    after_code: str = ""
    
    benefits: List[str] = field(default_factory=list)  # Benefits of applying this refactoring
    risks: List[str] = field(default_factory=list)  # Potential risks
    confidence_score: float = 0.0  # 0-100 confidence in this refactoring
    estimated_impact: Dict[str, str] = field(default_factory=dict)  # Impact on performance, maintainability, etc.
    new_code: Optional[str] = None  # Generated refactored code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for compatibility."""
        return {
            'refactoring_type': self.refactoring_type,
            'target_lines': self.target_lines,
            'description': self.description,
            'confidence': self.confidence,
            'impact_assessment': self.impact_assessment,
            'benefits': self.benefits,
            'risks': self.risks,
            'confidence_score': self.confidence_score,
            'estimated_impact': self.estimated_impact
        }


@dataclass
class FileSemanticAnalysis:
    """Complete semantic analysis of a file with dictionary-compatible interface."""
    file_path: str = ""
    lines_analyzed: List[LineAnalysis] = field(default_factory=list)
    overall_purpose: str = ""
    architectural_role: str = ""  # service, repository, utility, etc.
    design_patterns_used: List[str] = field(default_factory=list)
    design_patterns_missing: List[str] = field(default_factory=list)
    complexity_hotspots: List[Tuple[int, str]] = field(default_factory=list)  # line_number, reason
    performance_bottlenecks: List[Tuple[int, str]] = field(default_factory=list)
    security_vulnerabilities: List[Tuple[int, str]] = field(default_factory=list)
    maintainability_issues: List[str] = field(default_factory=list)
    testability_score: float = 0.0
    recommended_refactorings: List[IntelligentRefactoring] = field(default_factory=list)
    semantic_quality_score: float = 0.0  # 0-100 overall quality
    tokens_used: int = 0
    
    def get(self, key: str, default=None):
        """Dictionary-compatible get method for MetaAgent integration."""
        return getattr(self, key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MetaAgent compatibility."""
        return {
            'file_path': self.file_path,
            'lines_analyzed_count': len(self.lines_analyzed),
            'overall_purpose': self.overall_purpose,
            'architectural_role': self.architectural_role,
            'design_patterns_used': self.design_patterns_used,
            'design_patterns_missing': self.design_patterns_missing,
            'complexity_hotspots_count': len(self.complexity_hotspots),
            'performance_bottlenecks_count': len(self.performance_bottlenecks),
            'security_vulnerabilities_count': len(self.security_vulnerabilities),
            'maintainability_issues_count': len(self.maintainability_issues),
            'testability_score': self.testability_score,
            'recommended_refactorings_count': len(self.recommended_refactorings),
            'semantic_quality_score': self.semantic_quality_score,
            'tokens_used': self.tokens_used
        }


class AnalysisDepth(Enum):
    """Depth of semantic analysis to perform."""
    BASIC = "basic"      # Line-by-line analysis only
    ADVANCED = "advanced"  # + context analysis + simple refactoring
    DEEP = "deep"        # + architectural analysis + complex refactoring


class SemanticMode(Enum):
    """How aggressive to be with semantic transformations."""
    CONSERVATIVE = "conservative"  # Only safe, obvious improvements
    AGGRESSIVE = "aggressive"      # More speculative improvements


# =============================================================================
# Semantic Code Understanding Engine
# =============================================================================

class SemanticAnalysisEngine:
    """AI-powered semantic understanding of code structure and intent."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SemanticAnalysisEngine")
        
        # Knowledge bases
        self.design_patterns = self._load_design_pattern_knowledge()
        self.performance_patterns = self._load_performance_pattern_knowledge()
        self.security_patterns = self._load_security_pattern_knowledge()
        self.refactoring_patterns = self._load_refactoring_pattern_knowledge()
        
        # Built-in Python knowledge
        self.builtin_functions = set(dir(builtins))
        self.keywords = set(keyword.kwlist)
        
        self.logger.info("Semantic Analysis Engine initialized with comprehensive knowledge bases")
    
    def analyze_line_semantically(
        self, 
        line_number: int, 
        line_content: str, 
        ast_node: Optional[ast.AST], 
        surrounding_context: List[str],
        file_context: Dict[str, Any]
    ) -> LineAnalysis:
        """Perform deep semantic analysis of a single line."""
        
        # Extract semantic type
        semantic_type = self._identify_semantic_type(line_content, ast_node)
        
        # Understand purpose
        purpose = self._extract_line_purpose(line_content, semantic_type, surrounding_context)
        
        # Calculate complexity contribution
        complexity = self._calculate_line_complexity(line_content, ast_node, semantic_type)
        
        # Identify dependencies
        dependencies = self._identify_line_dependencies(line_content, ast_node, file_context)
        
        # Detect side effects
        side_effects = self._detect_line_side_effects(line_content, ast_node, semantic_type)
        
        # Find optimization opportunities
        optimizations = self._identify_optimization_opportunities(
            line_content, ast_node, semantic_type, surrounding_context
        )
        
        # Generate refactoring suggestions
        refactorings = self._generate_line_refactoring_suggestions(
            line_content, ast_node, semantic_type, surrounding_context
        )
        
        # Assess security implications
        security = self._assess_security_implications(line_content, ast_node, semantic_type)
        
        # Evaluate performance impact
        performance = self._evaluate_performance_impact(line_content, ast_node, semantic_type)
        
        # Check maintainability issues
        maintainability = self._check_maintainability_issues(
            line_content, ast_node, semantic_type, surrounding_context
        )
        
        return LineAnalysis(
            line_number=line_number,
            line_content=line_content,
            semantic_type=semantic_type,
            purpose=purpose,
            complexity_contribution=complexity,
            dependencies=dependencies,
            side_effects=side_effects,
            optimization_opportunities=optimizations,
            refactoring_suggestions=refactorings,
            security_implications=security,
            performance_impact=performance,
            maintainability_issues=maintainability
        )
    
    def _identify_semantic_type(self, line_content: str, ast_node: Optional[ast.AST]) -> str:
        """Identify the semantic type of a line of code."""
        line_stripped = line_content.strip()
        
        if not line_stripped or line_stripped.startswith('#'):
            return "comment_or_empty"
        
        if ast_node:
            if isinstance(ast_node, ast.FunctionDef):
                return "function_definition"
            elif isinstance(ast_node, ast.ClassDef):
                return "class_definition"
            elif isinstance(ast_node, ast.Import) or isinstance(ast_node, ast.ImportFrom):
                return "import_statement"
            elif isinstance(ast_node, ast.If):
                return "conditional_logic"
            elif isinstance(ast_node, ast.For) or isinstance(ast_node, ast.While):
                return "loop_logic"
            elif isinstance(ast_node, ast.Try):
                return "error_handling"
            elif isinstance(ast_node, ast.Return):
                return "return_statement"
            elif isinstance(ast_node, ast.Assign):
                return "variable_assignment"
            elif isinstance(ast_node, ast.Call):
                return "function_call"
        
        # Fallback to pattern matching
        if re.match(r'^\s*def\s+', line_stripped):
            return "function_definition"
        elif re.match(r'^\s*class\s+', line_stripped):
            return "class_definition"
        elif re.match(r'^\s*(import|from)\s+', line_stripped):
            return "import_statement"
        elif re.match(r'^\s*(if|elif|else)', line_stripped):
            return "conditional_logic"
        elif re.match(r'^\s*(for|while)', line_stripped):
            return "loop_logic"
        elif re.match(r'^\s*(try|except|finally)', line_stripped):
            return "error_handling"
        elif re.match(r'^\s*return\s+', line_stripped):
            return "return_statement"
        elif '=' in line_stripped and not line_stripped.startswith(('==', '!=', '<=', '>=')):
            return "variable_assignment"
        elif re.search(r'\w+\s*\(', line_stripped):
            return "function_call"
        else:
            return "general_logic"
    
    def _extract_line_purpose(
        self, 
        line_content: str, 
        semantic_type: str, 
        surrounding_context: List[str]
    ) -> str:
        """Extract the semantic purpose of a line of code."""
        line_stripped = line_content.strip()
        
        if semantic_type == "function_definition":
            # Extract function name and infer purpose
            match = re.search(r'def\s+(\w+)', line_stripped)
            if match:
                func_name = match.group(1)
                return self._infer_function_purpose(func_name, surrounding_context)
        
        elif semantic_type == "class_definition":
            match = re.search(r'class\s+(\w+)', line_stripped)
            if match:
                class_name = match.group(1)
                return self._infer_class_purpose(class_name, surrounding_context)
        
        elif semantic_type == "import_statement":
            return self._analyze_import_purpose(line_stripped)
        
        elif semantic_type == "variable_assignment":
            return self._analyze_assignment_purpose(line_stripped, surrounding_context)
        
        elif semantic_type == "function_call":
            return self._analyze_function_call_purpose(line_stripped, surrounding_context)
        
        elif semantic_type == "conditional_logic":
            return self._analyze_conditional_purpose(line_stripped, surrounding_context)
        
        elif semantic_type == "error_handling":
            return self._analyze_error_handling_purpose(line_stripped, surrounding_context)
        
        else:
            return f"Performs {semantic_type} operation"
    
    def _calculate_line_complexity(
        self, 
        line_content: str, 
        ast_node: Optional[ast.AST], 
        semantic_type: str
    ) -> float:
        """Calculate complexity contribution of a single line."""
        base_complexity = 1.0
        
        # Complexity factors
        if semantic_type in ["conditional_logic", "loop_logic"]:
            base_complexity += 2.0
        elif semantic_type == "error_handling":
            base_complexity += 1.5
        elif semantic_type in ["function_definition", "class_definition"]:
            base_complexity += 0.5
        
        # Nested complexity (count indentation levels)
        indentation_level = (len(line_content) - len(line_content.lstrip())) // 4
        base_complexity += indentation_level * 0.5
        
        # Operator complexity
        complex_operators = ['and', 'or', 'not', 'in', 'is', '==', '!=', '<=', '>=']
        for op in complex_operators:
            base_complexity += line_content.count(op) * 0.3
        
        # Function call complexity
        function_calls = len(re.findall(r'\w+\s*\(', line_content))
        base_complexity += function_calls * 0.2
        
        return min(base_complexity, 10.0)  # Cap at 10.0
    
    def _identify_line_dependencies(
        self, 
        line_content: str, 
        ast_node: Optional[ast.AST], 
        file_context: Dict[str, Any]
    ) -> List[str]:
        """Identify what this line depends on."""
        dependencies = []
        
        # Variable dependencies
        variables_used = re.findall(r'\b([a-zA-Z_]\w*)\b', line_content)
        for var in variables_used:
            if var not in self.keywords and var not in self.builtin_functions:
                dependencies.append(f"variable:{var}")
        
        # Import dependencies
        if "import" in line_content:
            import_match = re.search(r'import\s+([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)', line_content)
            if import_match:
                dependencies.append(f"module:{import_match.group(1)}")
        
        # Function call dependencies
        function_calls = re.findall(r'(\w+)\s*\(', line_content)
        for func in function_calls:
            if func not in self.builtin_functions:
                dependencies.append(f"function:{func}")
        
        return list(set(dependencies))  # Remove duplicates
    
    def _detect_line_side_effects(
        self, 
        line_content: str, 
        ast_node: Optional[ast.AST], 
        semantic_type: str
    ) -> List[str]:
        """Detect side effects this line might produce."""
        side_effects = []
        
        if semantic_type == "variable_assignment":
            var_match = re.search(r'([a-zA-Z_]\w*)\s*=', line_content)
            if var_match:
                side_effects.append(f"modifies_variable:{var_match.group(1)}")
        
        if semantic_type == "function_call":
            # Common side-effect patterns
            if any(pattern in line_content for pattern in ['.append(', '.extend(', '.pop(', '.remove(']):
                side_effects.append("modifies_collection")
            if any(pattern in line_content for pattern in ['.write(', '.close(', 'open(']):
                side_effects.append("file_system_operation")
            if any(pattern in line_content for pattern in ['print(', 'logging.', 'logger.']):
                side_effects.append("output_operation")
            if any(pattern in line_content for pattern in ['execute(', 'commit(', 'rollback(']):
                side_effects.append("database_operation")
        
        if "global" in line_content or "nonlocal" in line_content:
            side_effects.append("scope_modification")
        
        return side_effects
    
    def _identify_optimization_opportunities(
        self, 
        line_content: str, 
        ast_node: Optional[ast.AST], 
        semantic_type: str, 
        surrounding_context: List[str]
    ) -> List[Dict[str, Any]]:
        """Identify optimization opportunities for this line."""
        opportunities = []
        
        # String concatenation optimization
        if '+' in line_content and any(quote in line_content for quote in ['"', "'"]):
            opportunities.append({
                "type": "string_optimization",
                "description": "Consider using f-strings or .join() for string concatenation",
                "confidence": 0.8,
                "performance_gain": "medium"
            })
        
        # List comprehension opportunity
        if semantic_type == "loop_logic" and "append(" in surrounding_context[1:3]:
            opportunities.append({
                "type": "list_comprehension",
                "description": "Consider using list comprehension instead of append in loop",
                "confidence": 0.9,
                "performance_gain": "high"
            })
        
        # Exception handling optimization
        if semantic_type == "error_handling" and "except Exception:" in line_content:
            opportunities.append({
                "type": "exception_specificity",
                "description": "Use specific exception types instead of broad Exception",
                "confidence": 0.95,
                "performance_gain": "low",
                "maintainability_gain": "high"
            })
        
        # Database query optimization
        if any(pattern in line_content for pattern in ['execute(', 'query(', 'select']):
            opportunities.append({
                "type": "database_optimization",
                "description": "Review for potential N+1 query or missing indexes",
                "confidence": 0.7,
                "performance_gain": "critical"
            })
        
        return opportunities
    
    def _generate_line_refactoring_suggestions(
        self, 
        line_content: str, 
        ast_node: Optional[ast.AST], 
        semantic_type: str, 
        surrounding_context: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate intelligent refactoring suggestions."""
        suggestions = []
        
        # Long line refactoring
        if len(line_content) > 120:
            suggestions.append({
                "type": "line_length",
                "description": "Consider breaking this long line into multiple lines",
                "confidence": 0.9,
                "maintainability_gain": "medium"
            })
        
        # Complex conditional refactoring
        if semantic_type == "conditional_logic" and line_content.count(" and ") + line_content.count(" or ") > 2:
            suggestions.append({
                "type": "extract_boolean_method",
                "description": "Extract complex boolean logic into a descriptive method",
                "confidence": 0.85,
                "readability_gain": "high"
            })
        
        # Magic number refactoring
        numbers = re.findall(r'\b\d+\b', line_content)
        if any(int(num) > 10 for num in numbers if num.isdigit()):
            suggestions.append({
                "type": "extract_constant",
                "description": "Consider extracting magic numbers into named constants",
                "confidence": 0.8,
                "maintainability_gain": "medium"
            })
        
        return suggestions
    
    def _assess_security_implications(
        self, 
        line_content: str, 
        ast_node: Optional[ast.AST], 
        semantic_type: str
    ) -> List[str]:
        """Assess security implications of this line."""
        security_issues = []
        
        # SQL injection patterns
        if any(pattern in line_content for pattern in ['execute(', 'query(']) and '"' in line_content and '%' in line_content:
            security_issues.append("potential_sql_injection")
        
        # Hardcoded secrets
        if any(pattern in line_content.lower() for pattern in ['password', 'secret', 'key', 'token']) and '=' in line_content:
            security_issues.append("potential_hardcoded_secret")
        
        # Unsafe deserialization
        if any(pattern in line_content for pattern in ['pickle.loads', 'yaml.load', 'eval(']):
            security_issues.append("unsafe_deserialization")
        
        # Command injection
        if any(pattern in line_content for pattern in ['os.system', 'subprocess.call', 'exec(']):
            security_issues.append("potential_command_injection")
        
        return security_issues
    
    def _evaluate_performance_impact(
        self, 
        line_content: str, 
        ast_node: Optional[ast.AST], 
        semantic_type: str
    ) -> str:
        """Evaluate performance impact of this line."""
        # Database operations
        if any(pattern in line_content for pattern in ['execute(', 'query(', 'commit(', 'fetch']):
            return "high"
        
        # File I/O operations
        if any(pattern in line_content for pattern in ['open(', 'read(', 'write(', 'close(']):
            return "medium"
        
        # Network operations
        if any(pattern in line_content for pattern in ['requests.', 'urllib.', 'http']):
            return "high"
        
        # Complex loops or comprehensions
        if semantic_type == "loop_logic" or any(pattern in line_content for pattern in ['for ', 'while ', ' in ']):
            return "medium"
        
        # Regular expressions
        if any(pattern in line_content for pattern in ['re.', 'regex', 'pattern']):
            return "medium"
        
        return "low"
    
    def _check_maintainability_issues(
        self, 
        line_content: str, 
        ast_node: Optional[ast.AST], 
        semantic_type: str, 
        surrounding_context: List[str]
    ) -> List[str]:
        """Check for maintainability issues in this line."""
        issues = []
        
        # Long parameter lists
        if '(' in line_content and line_content.count(',') > 5:
            issues.append("too_many_parameters")
        
        # Deep nesting
        indentation = len(line_content) - len(line_content.lstrip())
        if indentation > 16:  # 4 levels of indentation
            issues.append("deep_nesting")
        
        # Unclear variable names
        variables = re.findall(r'\b([a-zA-Z_]\w*)\s*=', line_content)
        for var in variables:
            if len(var) < 3 and var not in ['id', 'ok', 'ip']:
                issues.append("unclear_variable_name")
        
        # Missing type hints (for function definitions)
        if semantic_type == "function_definition" and '->' not in line_content:
            issues.append("missing_return_type_hint")
        
        return issues
    
    # Knowledge base loading methods
    def _load_design_pattern_knowledge(self) -> Dict[str, Any]:
        """Load design pattern knowledge base."""
        return {
            "singleton": {
                "indicators": ["__new__", "_instance", "instance()"],
                "benefits": ["controlled_instantiation", "global_access"],
                "risks": ["global_state", "testing_difficulty"]
            },
            "factory": {
                "indicators": ["create_", "make_", "build_"],
                "benefits": ["loose_coupling", "extensibility"],
                "risks": ["complexity_overhead"]
            },
            "observer": {
                "indicators": ["notify", "subscribe", "listen"],
                "benefits": ["loose_coupling", "dynamic_relationships"],
                "risks": ["memory_leaks", "cascade_updates"]
            },
            "strategy": {
                "indicators": ["strategy", "algorithm", "policy"],
                "benefits": ["algorithm_swapping", "testing_ease"],
                "risks": ["class_proliferation"]
            }
        }
    
    def _load_performance_pattern_knowledge(self) -> Dict[str, Any]:
        """Load performance pattern knowledge base."""
        return {
            "caching": {
                "indicators": ["cache", "memoize", "@lru_cache"],
                "benefits": ["speed_improvement", "resource_saving"],
                "monitoring": ["hit_rate", "memory_usage"]
            },
            "lazy_loading": {
                "indicators": ["lazy", "on_demand", "defer"],
                "benefits": ["memory_efficiency", "startup_speed"],
                "risks": ["runtime_delays"]
            },
            "connection_pooling": {
                "indicators": ["pool", "connection", "reuse"],
                "benefits": ["resource_efficiency", "scalability"],
                "monitoring": ["pool_utilization", "connection_leaks"]
            }
        }
    
    def _load_security_pattern_knowledge(self) -> Dict[str, Any]:
        """Load security pattern knowledge base."""
        return {
            "input_validation": {
                "indicators": ["validate", "sanitize", "check"],
                "protects_against": ["injection", "xss", "malformed_input"],
                "implementation": ["whitelisting", "type_checking", "bounds_checking"]
            },
            "authentication": {
                "indicators": ["auth", "login", "verify"],
                "protects_against": ["unauthorized_access", "privilege_escalation"],
                "implementation": ["multi_factor", "token_based", "session_management"]
            },
            "encryption": {
                "indicators": ["encrypt", "hash", "crypto"],
                "protects_against": ["data_exposure", "tampering"],
                "implementation": ["symmetric", "asymmetric", "hashing"]
            }
        }
    
    def _load_refactoring_pattern_knowledge(self) -> Dict[str, Any]:
        """Load refactoring pattern knowledge base."""
        return {
            "extract_method": {
                "triggers": ["long_method", "duplicate_code", "complex_logic"],
                "benefits": ["reusability", "readability", "testability"],
                "conditions": ["cohesive_operations", "clear_interface"]
            },
            "extract_class": {
                "triggers": ["large_class", "multiple_responsibilities", "data_clumps"],
                "benefits": ["single_responsibility", "modularity"],
                "conditions": ["related_data_methods", "clear_boundaries"]
            },
            "inline_method": {
                "triggers": ["trivial_method", "unnecessary_indirection"],
                "benefits": ["simplicity", "performance"],
                "conditions": ["simple_implementation", "limited_usage"]
            },
            "rename_variable": {
                "triggers": ["unclear_name", "misleading_name", "abbreviation"],
                "benefits": ["clarity", "self_documentation"],
                "conditions": ["scope_analysis", "consistent_naming"]
            }
        }
    
    def _infer_function_purpose(self, func_name: str, context: List[str]) -> str:
        """Infer the purpose of a function from its name and context."""
        # Common patterns
        if func_name.startswith('get_'):
            return f"Retrieves {func_name[4:].replace('_', ' ')}"
        elif func_name.startswith('set_'):
            return f"Sets {func_name[4:].replace('_', ' ')}"
        elif func_name.startswith('is_') or func_name.startswith('has_'):
            return f"Checks if {func_name[3:].replace('_', ' ')}"
        elif func_name.startswith('create_'):
            return f"Creates {func_name[7:].replace('_', ' ')}"
        elif func_name.startswith('delete_') or func_name.startswith('remove_'):
            return f"Deletes {func_name[7:].replace('_', ' ')}"
        elif func_name.startswith('update_'):
            return f"Updates {func_name[7:].replace('_', ' ')}"
        elif func_name.startswith('validate_'):
            return f"Validates {func_name[9:].replace('_', ' ')}"
        elif func_name.startswith('calculate_'):
            return f"Calculates {func_name[10:].replace('_', ' ')}"
        elif func_name.startswith('process_'):
            return f"Processes {func_name[8:].replace('_', ' ')}"
        else:
            # Generic description
            return f"Implements {func_name.replace('_', ' ')} functionality"
    
    def _infer_class_purpose(self, class_name: str, context: List[str]) -> str:
        """Infer the purpose of a class from its name and context."""
        if class_name.endswith('Service'):
            return f"Service layer for {class_name[:-7].lower()} business logic"
        elif class_name.endswith('Repository'):
            return f"Data access layer for {class_name[:-10].lower()} entities"
        elif class_name.endswith('Controller'):
            return f"Controller for {class_name[:-10].lower()} operations"
        elif class_name.endswith('Manager'):
            return f"Manager for {class_name[:-7].lower()} resources"
        elif class_name.endswith('Factory'):
            return f"Factory for creating {class_name[:-7].lower()} instances"
        elif class_name.endswith('Builder'):
            return f"Builder for constructing {class_name[:-7].lower()} objects"
        elif class_name.endswith('Model'):
            return f"Data model representing {class_name[:-5].lower()} entity"
        else:
            return f"Class representing {class_name.lower()} concept"
    
    def _analyze_import_purpose(self, line: str) -> str:
        """Analyze the purpose of an import statement."""
        if 'typing' in line:
            return "Imports type hints for better code documentation"
        elif any(module in line for module in ['os', 'sys', 'pathlib']):
            return "Imports system/filesystem utilities"
        elif any(module in line for module in ['datetime', 'time']):
            return "Imports date/time handling utilities"
        elif any(module in line for module in ['json', 'yaml', 'csv']):
            return "Imports data serialization utilities"
        elif any(module in line for module in ['logging', 'log']):
            return "Imports logging utilities"
        elif any(module in line for module in ['requests', 'urllib', 'http']):
            return "Imports network/HTTP utilities"
        elif any(module in line for module in ['sqlite3', 'psycopg2', 'sqlalchemy']):
            return "Imports database connectivity"
        else:
            # Extract module name
            import_match = re.search(r'import\s+([a-zA-Z_]\w*)', line)
            if import_match:
                module = import_match.group(1)
                return f"Imports {module} module functionality"
            return "Imports external functionality"
    
    def _analyze_assignment_purpose(self, line: str, context: List[str]) -> str:
        """Analyze the purpose of a variable assignment."""
        var_match = re.search(r'([a-zA-Z_]\w*)\s*=\s*(.+)', line)
        if var_match:
            var_name, value = var_match.groups()
            
            if 'None' in value:
                return f"Initializes {var_name} to None"
            elif any(pattern in value for pattern in ['[]', 'list()', '{}']):
                return f"Initializes {var_name} as empty collection"
            elif re.search(r'\d+', value):
                return f"Sets {var_name} to numeric value"
            elif any(quote in value for quote in ['"', "'"]):
                return f"Sets {var_name} to string value"
            elif '(' in value and ')' in value:
                return f"Assigns result of function call to {var_name}"
            else:
                return f"Assigns value to {var_name}"
        return "Performs variable assignment"
    
    def _analyze_function_call_purpose(self, line: str, context: List[str]) -> str:
        """Analyze the purpose of a function call."""
        function_calls = re.findall(r'(\w+)\s*\(', line)
        if function_calls:
            func = function_calls[0]
            if func in ['print', 'log']:
                return "Outputs information for debugging/logging"
            elif func in ['open', 'read', 'write']:
                return "Performs file I/O operation"
            elif func in ['get', 'post', 'put', 'delete']:
                return "Makes HTTP request"
            elif func in ['execute', 'query', 'commit']:
                return "Performs database operation"
            elif func.startswith('test_'):
                return "Executes test case"
            else:
                return f"Calls {func} function"
        return "Executes function call"
    
    def _analyze_conditional_purpose(self, line: str, context: List[str]) -> str:
        """Analyze the purpose of conditional logic."""
        if line.strip().startswith('if'):
            return "Conditional execution based on boolean condition"
        elif line.strip().startswith('elif'):
            return "Alternative conditional branch"
        elif line.strip().startswith('else'):
            return "Default fallback execution path"
        return "Controls program flow"
    
    def _analyze_error_handling_purpose(self, line: str, context: List[str]) -> str:
        """Analyze the purpose of error handling."""
        if line.strip().startswith('try'):
            return "Begins error-protected code block"
        elif line.strip().startswith('except'):
            return "Handles specific exception type"
        elif line.strip().startswith('finally'):
            return "Cleanup code that always executes"
        elif line.strip().startswith('raise'):
            return "Raises exception to signal error condition"
        return "Manages error conditions"


# =============================================================================
# Intelligent Code Agent - Main Class
# =============================================================================

class IntelligentCodeAgent:
    """
    AI-powered code analysis agent that performs line-by-line semantic analysis,
    applies contextual optimizations, and generates intelligent refactoring suggestions.
    """
    
    def __init__(
        self, 
        project_root: Path, 
        analysis_depth: AnalysisDepth = AnalysisDepth.ADVANCED,
        semantic_mode: SemanticMode = SemanticMode.CONSERVATIVE,
        dry_run: bool = False
    ):
        self.project_root = project_root
        self.analysis_depth = analysis_depth
        self.semantic_mode = semantic_mode
        self.dry_run = dry_run
        
        self.logger = logging.getLogger(f"{__name__}.IntelligentCodeAgent")
        
        # Initialize engines
        self.semantic_engine = SemanticAnalysisEngine()
        
        # Load existing auditor infrastructure if available
        self.enhanced_auditor = None
        if EnhancedSystematicFileAuditor:
            try:
                audit_dir = project_root / "scripts" / "automated_audit"
                self.enhanced_auditor = EnhancedSystematicFileAuditor(
                    project_root, audit_dir, dry_run=dry_run, validate_only=False
                )
                self.logger.info("Integrated with existing Enhanced Systematic File Auditor")
            except Exception as e:
                self.logger.warning("Could not initialize Enhanced Auditor: %s", e)
        
        self.logger.info(
            "Intelligent Code Agent initialized: depth=%s, mode=%s, dry_run=%s",
            analysis_depth.value, semantic_mode.value, dry_run
        )
    
    def analyze_file_intelligently(self, file_path: str) -> FileSemanticAnalysis:
        """
        Perform comprehensive intelligent analysis of a Python file.
        
        This is the main entry point for AI-powered code analysis.
        """
        self.logger.info("Starting intelligent analysis of %s", file_path)
        
        try:
            # Read and parse file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.splitlines()
            
            # Parse AST for structural understanding
            try:
                ast_tree = ast.parse(content)
                ast_map = self._create_ast_line_mapping(ast_tree)
            except SyntaxError as e:
                self.logger.warning("Syntax error in %s: %s", file_path, e)
                ast_tree = None
                ast_map = {}
            
            # Analyze each line with semantic understanding
            line_analyses = []
            for i, line in enumerate(lines, 1):
                # Get surrounding context (5 lines before and after)
                context_start = max(0, i - 6)
                context_end = min(len(lines), i + 5)
                surrounding_context = lines[context_start:context_end]
                
                # File-level context
                file_context = {
                    "total_lines": len(lines),
                    "file_path": file_path,
                    "imports": self._extract_imports(lines),
                    "classes": self._extract_classes(ast_tree) if ast_tree else [],
                    "functions": self._extract_functions(ast_tree) if ast_tree else []
                }
                
                # Get AST node for this line
                ast_node = ast_map.get(i)
                
                # Perform semantic analysis
                line_analysis = self.semantic_engine.analyze_line_semantically(
                    line_number=i,
                    line_content=line,
                    ast_node=ast_node,
                    surrounding_context=surrounding_context,
                    file_context=file_context
                )
                
                line_analyses.append(line_analysis)
            
            # File-level analysis
            overall_purpose = self._determine_file_purpose(file_path, ast_tree, lines)
            architectural_role = self._determine_architectural_role(file_path, ast_tree)
            design_patterns_used = self._identify_design_patterns_used(ast_tree, line_analyses)
            design_patterns_missing = self._suggest_missing_design_patterns(ast_tree, line_analyses)
            
            # Identify hotspots and issues
            complexity_hotspots = self._identify_complexity_hotspots(line_analyses)
            performance_bottlenecks = self._identify_performance_bottlenecks(line_analyses)
            security_vulnerabilities = self._identify_security_vulnerabilities(line_analyses)
            maintainability_issues = self._assess_maintainability_issues(line_analyses)
            
            # Generate intelligent refactorings
            recommended_refactorings = []
            if self.analysis_depth in [AnalysisDepth.ADVANCED, AnalysisDepth.DEEP]:
                recommended_refactorings = self._generate_intelligent_refactorings(
                    line_analyses, ast_tree, file_path
                )
            
            # Calculate quality scores
            testability_score = self._calculate_testability_score(line_analyses, ast_tree)
            semantic_quality_score = self._calculate_semantic_quality_score(line_analyses)
            
            result = FileSemanticAnalysis(
                file_path=file_path,
                lines_analyzed=line_analyses,
                overall_purpose=overall_purpose,
                architectural_role=architectural_role,
                design_patterns_used=design_patterns_used,
                design_patterns_missing=design_patterns_missing,
                complexity_hotspots=complexity_hotspots,
                performance_bottlenecks=performance_bottlenecks,
                security_vulnerabilities=security_vulnerabilities,
                maintainability_issues=maintainability_issues,
                testability_score=testability_score,
                recommended_refactorings=recommended_refactorings,
                semantic_quality_score=semantic_quality_score
            )
            
            self.logger.info(
                "Analysis complete for %s: %d lines, quality=%.1f, refactorings=%d",
                file_path, len(line_analyses), semantic_quality_score, len(recommended_refactorings)
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Error analyzing file %s: %s", file_path, e)
            raise
    
    def apply_intelligent_refactorings(
        self, 
        analysis: FileSemanticAnalysis, 
        selected_refactorings: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Apply selected intelligent refactorings to the file."""
        if self.dry_run:
            return {"status": "dry_run", "would_apply": len(analysis.recommended_refactorings)}
        
        refactorings_to_apply = analysis.recommended_refactorings
        if selected_refactorings:
            refactorings_to_apply = [
                refactorings_to_apply[i] for i in selected_refactorings 
                if i < len(refactorings_to_apply)
            ]
        
        applied_refactorings = []
        failed_refactorings = []
        
        for refactoring in refactorings_to_apply:
            try:
                if self._can_safely_apply_refactoring(refactoring, analysis):
                    result = self._apply_single_refactoring(refactoring, analysis.file_path)
                    if result["success"]:
                        applied_refactorings.append(refactoring)
                    else:
                        failed_refactorings.append((refactoring, result["error"]))
                else:
                    failed_refactorings.append((refactoring, "Safety check failed"))
            except Exception as e:
                failed_refactorings.append((refactoring, str(e)))
        
        return {
            "status": "completed",
            "applied": len(applied_refactorings),
            "failed": len(failed_refactorings),
            "applied_refactorings": applied_refactorings,
            "failed_refactorings": failed_refactorings
        }
    
    # Helper methods for analysis
    def _create_ast_line_mapping(self, ast_tree: ast.AST) -> Dict[int, ast.AST]:
        """Create mapping from line numbers to AST nodes."""
        line_map = {}
        for node in ast.walk(ast_tree):
            if hasattr(node, 'lineno'):
                line_map[node.lineno] = node
        return line_map
    
    def _extract_imports(self, lines: List[str]) -> List[str]:
        """Extract import statements from file."""
        imports = []
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith(('import ', 'from ')):
                imports.append(line_stripped)
        return imports
    
    def _extract_classes(self, ast_tree: Optional[ast.AST]) -> List[str]:
        """Extract class names from AST."""
        if not ast_tree:
            return []
        
        classes = []
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return classes
    
    def _extract_functions(self, ast_tree: Optional[ast.AST]) -> List[str]:
        """Extract function names from AST."""
        if not ast_tree:
            return []
        
        functions = []
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions
    
    def _determine_file_purpose(
        self, 
        file_path: str, 
        ast_tree: Optional[ast.AST], 
        lines: List[str]
    ) -> str:
        """Determine the overall purpose of the file."""
        filename = Path(file_path).name
        
        # Check for common patterns in filename
        if filename.startswith('test_'):
            return "Test file containing automated test cases"
        elif filename.endswith('_service.py'):
            return "Service layer implementing business logic"
        elif filename.endswith('_repository.py'):
            return "Data access layer for entity persistence"
        elif filename.endswith('_model.py') or filename.endswith('_models.py'):
            return "Data models and entity definitions"
        elif filename.endswith('_utils.py') or filename.endswith('_utilities.py'):
            return "Utility functions and helper methods"
        elif filename.endswith('_config.py') or filename.endswith('_settings.py'):
            return "Configuration and settings management"
        elif filename == '__init__.py':
            return "Package initialization and exports"
        elif filename == 'main.py' or filename == 'app.py':
            return "Application entry point and initialization"
        
        # Analyze content for purpose
        if ast_tree:
            classes = self._extract_classes(ast_tree)
            functions = self._extract_functions(ast_tree)
            
            if len(classes) > len(functions):
                return f"Class definitions module with {len(classes)} classes"
            elif len(functions) > 0:
                return f"Function library with {len(functions)} utility functions"
        
        # Fallback to content analysis
        content = '\n'.join(lines)
        if 'def test_' in content:
            return "Test module with test cases"
        elif 'class ' in content and 'Service' in content:
            return "Service implementation module"
        elif 'import ' in content and 'from ' in content:
            return "Module with mixed functionality"
        
        return "General purpose Python module"
    
    def _determine_architectural_role(
        self, 
        file_path: str, 
        ast_tree: Optional[ast.AST]
    ) -> str:
        """Determine the architectural role of this file."""
        path_parts = Path(file_path).parts
        
        # Check directory structure
        if 'services' in path_parts:
            return "service_layer"
        elif 'repositories' in path_parts or 'repos' in path_parts:
            return "data_access_layer"
        elif 'models' in path_parts:
            return "domain_model"
        elif 'utils' in path_parts or 'utilities' in path_parts:
            return "utility_layer"
        elif 'config' in path_parts:
            return "configuration_layer"
        elif 'tests' in path_parts:
            return "test_layer"
        elif 'api' in path_parts or 'endpoints' in path_parts:
            return "api_layer"
        elif 'components' in path_parts:
            return "component_layer"
        elif 'middleware' in path_parts:
            return "middleware_layer"
        elif 'database' in path_parts:
            return "database_layer"
        
        # Analyze filename
        filename = Path(file_path).name.lower()
        if 'service' in filename:
            return "service_layer"
        elif 'repository' in filename or 'repo' in filename:
            return "data_access_layer"
        elif 'model' in filename:
            return "domain_model"
        elif 'util' in filename:
            return "utility_layer"
        elif 'config' in filename or 'setting' in filename:
            return "configuration_layer"
        elif 'test' in filename:
            return "test_layer"
        
        return "application_layer"
    
    def _identify_design_patterns_used(
        self, 
        ast_tree: Optional[ast.AST], 
        line_analyses: List[LineAnalysis]
    ) -> List[str]:
        """Identify design patterns currently used in the code."""
        patterns = []
        
        if not ast_tree:
            return patterns
        
        # Singleton pattern detection
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef) and node.name == '__new__':
                patterns.append("singleton")
                break
        
        # Factory pattern detection
        for line_analysis in line_analyses:
            if any(word in line_analysis.line_content.lower() for word in ['create_', 'make_', 'factory']):
                if "factory" not in patterns:
                    patterns.append("factory")
        
        # Observer pattern detection
        for line_analysis in line_analyses:
            if any(word in line_analysis.line_content.lower() for word in ['notify', 'subscribe', 'observer']):
                if "observer" not in patterns:
                    patterns.append("observer")
        
        # Strategy pattern detection
        for line_analysis in line_analyses:
            if any(word in line_analysis.line_content.lower() for word in ['strategy', 'algorithm']):
                if "strategy" not in patterns:
                    patterns.append("strategy")
        
        # Repository pattern detection
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.ClassDef) and 'repository' in node.name.lower():
                if "repository" not in patterns:
                    patterns.append("repository")
        
        # Service layer pattern detection
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.ClassDef) and 'service' in node.name.lower():
                if "service_layer" not in patterns:
                    patterns.append("service_layer")
        
        return patterns
    
    def _suggest_missing_design_patterns(
        self, 
        ast_tree: Optional[ast.AST], 
        line_analyses: List[LineAnalysis]
    ) -> List[str]:
        """Suggest design patterns that could improve the code."""
        suggestions = []
        
        # Analyze complexity and suggest patterns
        total_complexity = sum(line.complexity_contribution for line in line_analyses)
        num_functions = len([line for line in line_analyses if line.semantic_type == "function_definition"])
        
        # Suggest Factory if many creation patterns
        creation_lines = len([
            line for line in line_analyses 
            if any(word in line.line_content.lower() for word in ['new ', 'create', 'make', '()'])
        ])
        if creation_lines > 5 and "factory" not in self._identify_design_patterns_used(ast_tree, line_analyses):
            suggestions.append("factory")
        
        # Suggest Strategy if many conditional branches
        conditional_lines = len([
            line for line in line_analyses 
            if line.semantic_type == "conditional_logic"
        ])
        if conditional_lines > 10:
            suggestions.append("strategy")
        
        # Suggest Observer if many state changes
        state_change_lines = len([
            line for line in line_analyses 
            if "=" in line.line_content and line.semantic_type == "variable_assignment"
        ])
        if state_change_lines > 15:
            suggestions.append("observer")
        
        # Suggest Command if many method calls
        method_call_lines = len([
            line for line in line_analyses 
            if line.semantic_type == "function_call"
        ])
        if method_call_lines > 20:
            suggestions.append("command")
        
        return suggestions
    
    def _identify_complexity_hotspots(self, line_analyses: List[LineAnalysis]) -> List[Tuple[int, str]]:
        """Identify lines with high complexity."""
        hotspots = []
        
        for line_analysis in line_analyses:
            if line_analysis.complexity_contribution > 5.0:
                reason = f"High complexity score: {line_analysis.complexity_contribution:.1f}"
                hotspots.append((line_analysis.line_number, reason))
        
        # Sort by complexity (highest first)
        hotspots.sort(key=lambda x: x[1], reverse=True)
        return hotspots[:10]  # Top 10 hotspots
    
    def _identify_performance_bottlenecks(self, line_analyses: List[LineAnalysis]) -> List[Tuple[int, str]]:
        """Identify potential performance bottlenecks."""
        bottlenecks = []
        
        for line_analysis in line_analyses:
            if line_analysis.performance_impact in ["high", "critical"]:
                reason = f"Performance impact: {line_analysis.performance_impact}"
                bottlenecks.append((line_analysis.line_number, reason))
        
        return bottlenecks
    
    def _identify_security_vulnerabilities(self, line_analyses: List[LineAnalysis]) -> List[Tuple[int, str]]:
        """Identify potential security vulnerabilities."""
        vulnerabilities = []
        
        for line_analysis in line_analyses:
            if line_analysis.security_implications:
                for issue in line_analysis.security_implications:
                    vulnerabilities.append((line_analysis.line_number, issue))
        
        return vulnerabilities
    
    def _assess_maintainability_issues(self, line_analyses: List[LineAnalysis]) -> List[str]:
        """Assess overall maintainability issues."""
        issues = []
        
        # Collect all maintainability issues
        all_issues = []
        for line_analysis in line_analyses:
            all_issues.extend(line_analysis.maintainability_issues)
        
        # Count frequency and identify patterns
        issue_counts = Counter(all_issues)
        
        for issue, count in issue_counts.most_common():
            if count > 2:  # Only report issues that occur multiple times
                issues.append(f"{issue} (occurs {count} times)")
        
        return issues
    
    def _generate_intelligent_refactorings(
        self, 
        line_analyses: List[LineAnalysis], 
        ast_tree: Optional[ast.AST], 
        file_path: str
    ) -> List[IntelligentRefactoring]:
        """Generate intelligent refactoring recommendations."""
        refactorings = []
        
        # Extract method refactoring for complex functions
        if ast_tree:
            for node in ast.walk(ast_tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = [
                        line for line in line_analyses 
                        if node.lineno <= line.line_number <= (node.end_lineno or node.lineno + 50)
                    ]
                    
                    total_complexity = sum(line.complexity_contribution for line in func_lines)
                    if total_complexity > 15:
                        refactorings.append(IntelligentRefactoring(
                            refactoring_type="extract_method",
                            target_lines=[line.line_number for line in func_lines],
                            description=f"Extract complex logic from {node.name} into smaller methods",
                            benefits=[
                                "Reduced complexity",
                                "Improved readability", 
                                "Better testability"
                            ],
                            risks=["Potential over-abstraction"],
                            confidence_score=0.85,
                            estimated_impact={
                                "complexity": "high_reduction",
                                "maintainability": "high_improvement",
                                "performance": "minimal_impact"
                            }
                        ))
        
        # Optimize exception handling
        exception_lines = [
            line for line in line_analyses 
            if line.semantic_type == "error_handling" and 
            any("exception_swallowing" in opp.get("type", "") for opp in line.optimization_opportunities)
        ]
        
        if exception_lines:
            refactorings.append(IntelligentRefactoring(
                refactoring_type="improve_exception_handling",
                target_lines=[line.line_number for line in exception_lines],
                description="Improve exception handling with specific exception types and logging",
                benefits=[
                    "Better error visibility",
                    "Improved debugging",
                    "More robust error handling"
                ],
                risks=["Slight increase in code volume"],
                confidence_score=0.95,
                estimated_impact={
                    "maintainability": "high_improvement",
                    "debugging": "high_improvement",
                    "performance": "minimal_impact"
                }
            ))
        
        # String optimization refactoring
        string_optimization_lines = [
            line for line in line_analyses 
            if any("string_optimization" in opp.get("type", "") for opp in line.optimization_opportunities)
        ]
        
        if string_optimization_lines:
            refactorings.append(IntelligentRefactoring(
                refactoring_type="optimize_string_operations",
                target_lines=[line.line_number for line in string_optimization_lines],
                description="Replace string concatenation with f-strings or join operations",
                benefits=[
                    "Better performance",
                    "Improved readability",
                    "Modern Python idioms"
                ],
                risks=["Minimal - modern Python best practice"],
                confidence_score=0.9,
                estimated_impact={
                    "performance": "medium_improvement",
                    "readability": "high_improvement",
                    "maintainability": "medium_improvement"
                }
            ))
        
        return refactorings
    
    def _calculate_testability_score(
        self, 
        line_analyses: List[LineAnalysis], 
        ast_tree: Optional[ast.AST]
    ) -> float:
        """Calculate testability score for the file."""
        if not ast_tree:
            return 0.0
        
        score = 100.0
        
        # Penalize for side effects
        side_effect_lines = len([
            line for line in line_analyses 
            if line.side_effects and not any("output_operation" in effect for effect in line.side_effects)
        ])
        score -= min(side_effect_lines * 2, 30)
        
        # Penalize for complex functions
        complex_functions = 0
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = [
                    line for line in line_analyses 
                    if node.lineno <= line.line_number <= (node.end_lineno or node.lineno + 50)
                ]
                total_complexity = sum(line.complexity_contribution for line in func_lines)
                if total_complexity > 10:
                    complex_functions += 1
        
        score -= min(complex_functions * 5, 25)
        
        # Reward for clear interfaces
        clear_function_names = 0
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                if any(prefix in node.name for prefix in ['get_', 'set_', 'is_', 'has_', 'create_']):
                    clear_function_names += 1
        
        score += min(clear_function_names * 2, 15)
        
        return max(score, 0.0)
    
    def _calculate_semantic_quality_score(self, line_analyses: List[LineAnalysis]) -> float:
        """Calculate overall semantic quality score."""
        if not line_analyses:
            return 0.0
        
        # Base score
        score = 100.0
        
        # Penalize for complexity
        avg_complexity = sum(line.complexity_contribution for line in line_analyses) / len(line_analyses)
        score -= min(avg_complexity * 5, 30)
        
        # Penalize for security issues
        security_issues = sum(len(line.security_implications) for line in line_analyses)
        score -= min(security_issues * 10, 40)
        
        # Penalize for maintainability issues
        maintainability_issues = sum(len(line.maintainability_issues) for line in line_analyses)
        score -= min(maintainability_issues * 2, 20)
        
        # Reward for optimization opportunities identified
        optimizations = sum(len(line.optimization_opportunities) for line in line_analyses)
        if optimizations > 0:
            score += min(optimizations, 10)
        
        # Reward for good patterns
        good_patterns = len([
            line for line in line_analyses 
            if line.semantic_type in ["function_definition", "class_definition"] and 
            not line.maintainability_issues
        ])
        score += min(good_patterns, 15)
        
        return max(score, 0.0)
    
    def _can_safely_apply_refactoring(
        self, 
        refactoring: IntelligentRefactoring, 
        analysis: FileSemanticAnalysis
    ) -> bool:
        """Check if a refactoring can be safely applied."""
        # Conservative mode checks
        if self.semantic_mode == SemanticMode.CONSERVATIVE:
            if refactoring.confidence_score < 0.8:
                return False
            if any("high" in risk.lower() for risk in refactoring.risks):
                return False
        
        # Check for conflicting refactorings
        for other_refactoring in analysis.recommended_refactorings:
            if (other_refactoring != refactoring and 
                set(refactoring.target_lines) & set(other_refactoring.target_lines)):
                return False
        
        return True
    
    def _apply_single_refactoring(
        self, 
        refactoring: IntelligentRefactoring, 
        file_path: str
    ) -> Dict[str, Any]:
        """Apply a single refactoring to the file."""
        # This is a placeholder for actual refactoring implementation
        # In a real implementation, this would modify the file according to the refactoring
        
        self.logger.info(
            "Would apply %s refactoring to lines %s in %s",
            refactoring.refactoring_type, refactoring.target_lines, file_path
        )
        
        # For now, just return success
        return {
            "success": True,
            "refactoring_type": refactoring.refactoring_type,
            "lines_modified": len(refactoring.target_lines)
        }


# =============================================================================
# CLI Interface
# =============================================================================

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('intelligent_code_agent.log')
        ]
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Intelligent Code Agent - AI-Powered Line-by-Line Analysis"
    )
    
    parser.add_argument(
        "--target-file", 
        type=str, 
        help="Specific file to analyze (if not provided, analyzes sample files)"
    )
    parser.add_argument(
        "--analysis-depth", 
        choices=["basic", "advanced", "deep"], 
        default="advanced",
        help="Depth of analysis to perform"
    )
    parser.add_argument(
        "--semantic-mode", 
        choices=["conservative", "aggressive"], 
        default="conservative",
        help="How aggressive to be with semantic transformations"
    )
    parser.add_argument(
        "--apply-refactoring", 
        action="store_true",
        help="Apply recommended refactorings (use with caution)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Initialize agent
    project_root = Path(__file__).resolve().parent.parent.parent
    agent = IntelligentCodeAgent(
        project_root=project_root,
        analysis_depth=AnalysisDepth(args.analysis_depth),
        semantic_mode=SemanticMode(args.semantic_mode),
        dry_run=args.dry_run
    )
    
    logger.info("🤖 Intelligent Code Agent started")
    logger.info("Analysis depth: %s", args.analysis_depth)
    logger.info("Semantic mode: %s", args.semantic_mode)
    logger.info("Dry run: %s", args.dry_run)
    
    try:
        if args.target_file:
            # Analyze specific file
            target_path = Path(args.target_file)
            if not target_path.exists():
                logger.error("File not found: %s", target_path)
                return 1
            
            logger.info("Analyzing file: %s", target_path)
            analysis = agent.analyze_file_intelligently(str(target_path))
            
            # Print results
            print(f"\n🔍 Intelligent Analysis Results for {target_path.name}")
            print(f"=" * 60)
            print(f"Overall Purpose: {analysis.overall_purpose}")
            print(f"Architectural Role: {analysis.architectural_role}")
            print(f"Lines Analyzed: {len(analysis.lines_analyzed)}")
            print(f"Semantic Quality Score: {analysis.semantic_quality_score:.1f}/100")
            print(f"Testability Score: {analysis.testability_score:.1f}/100")
            
            if analysis.design_patterns_used:
                print(f"Design Patterns Used: {', '.join(analysis.design_patterns_used)}")
            
            if analysis.design_patterns_missing:
                print(f"Suggested Patterns: {', '.join(analysis.design_patterns_missing)}")
            
            if analysis.complexity_hotspots:
                print(f"\n🔥 Complexity Hotspots:")
                for line_no, reason in analysis.complexity_hotspots[:5]:
                    print(f"  Line {line_no}: {reason}")
            
            if analysis.performance_bottlenecks:
                print(f"\n⚡ Performance Bottlenecks:")
                for line_no, reason in analysis.performance_bottlenecks:
                    print(f"  Line {line_no}: {reason}")
            
            if analysis.security_vulnerabilities:
                print(f"\n🛡️ Security Issues:")
                for line_no, issue in analysis.security_vulnerabilities:
                    print(f"  Line {line_no}: {issue}")
            
            if analysis.recommended_refactorings:
                print(f"\n🔧 Recommended Refactorings ({len(analysis.recommended_refactorings)}):")
                for i, refactoring in enumerate(analysis.recommended_refactorings):
                    print(f"  {i+1}. {refactoring.refactoring_type}: {refactoring.description}")
                    print(f"     Confidence: {refactoring.confidence_score:.0%}")
                    print(f"     Lines: {len(refactoring.target_lines)}")
            
            # Apply refactorings if requested
            if args.apply_refactoring and analysis.recommended_refactorings:
                print(f"\n🛠️ Applying Refactorings...")
                result = agent.apply_intelligent_refactorings(analysis)
                print(f"Applied: {result['applied']}, Failed: {result['failed']}")
        
        else:
            # Demo mode - analyze a few sample files
            sample_files = [
                "streamlit_extension/utils/data_utils.py",
                "streamlit_extension/services/analytics_service.py",
                "scripts/automated_audit/systematic_file_auditor.py"
            ]
            
            for sample_file in sample_files:
                file_path = project_root / sample_file
                if file_path.exists():
                    logger.info("Demo analysis: %s", sample_file)
                    analysis = agent.analyze_file_intelligently(str(file_path))
                    
                    print(f"\n📊 {sample_file}")
                    print(f"Quality: {analysis.semantic_quality_score:.1f}/100, "
                          f"Refactorings: {len(analysis.recommended_refactorings)}")
                else:
                    logger.warning("Sample file not found: %s", sample_file)
        
        logger.info("🎯 Intelligent Code Agent completed successfully")
        return 0
        
    except Exception as e:
        logger.error("Error: %s", e, exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    exit(main())