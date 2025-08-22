#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complexity Analyzer Tool - Agno tool for code complexity analysis.

This tool provides comprehensive complexity analysis including:
- Cyclomatic complexity
- Cognitive complexity  
- Maintainability index
- Nesting depth analysis
"""

from __future__ import annotations

import ast
import math
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass

from .base_refactoring_tool import BaseRefactoringTool, RefactoringTarget

# Configuration Constants
class ComplexityThresholds:
    """Constants for complexity analysis thresholds."""
    CYCLOMATIC_COMPLEXITY = 10
    COGNITIVE_COMPLEXITY = 15
    MAINTAINABILITY_INDEX = 20
    NESTING_DEPTH = 4
    LINES_OF_CODE = 50
    CLASS_COMPLEXITY = 50
    PARAMETER_COUNT = 5
    SEVERITY_NORMALIZATION = 20.0  # Was magic number 20
    LINE_WEIGHT_FACTOR = 0.1  # Was magic number for line count severity

@dataclass
class ComplexityMetrics:
    """Complexity metrics for a code element."""
    cyclomatic_complexity: int
    cognitive_complexity: int
    maintainability_index: float
    max_nesting_depth: int
    line_count: int
    parameter_count: int
    
class ComplexityAnalyzerTool(BaseRefactoringTool):
    """
    Agno tool for analyzing code complexity metrics.
    
    Analyzes:
    - Cyclomatic complexity (McCabe)
    - Cognitive complexity (SonarQube style)
    - Maintainability index
    - Nesting depth
    - Method/function complexity
    """
    
    def __init__(self):
        super().__init__()
        
        # Complexity thresholds (using constants)
        self.cyclomatic_threshold = ComplexityThresholds.CYCLOMATIC_COMPLEXITY
        self.cognitive_threshold = ComplexityThresholds.COGNITIVE_COMPLEXITY
        self.maintainability_threshold = ComplexityThresholds.MAINTAINABILITY_INDEX
        self.nesting_threshold = ComplexityThresholds.NESTING_DEPTH
        self.lines_threshold = ComplexityThresholds.LINES_OF_CODE
    
    def get_tool_name(self) -> str:
        return "complexity_analyzer"
    
    def get_tool_description(self) -> str:
        return (
            "Analyzes code complexity metrics including cyclomatic complexity, "
            "cognitive complexity, maintainability index, and nesting depth. "
            "Identifies methods and functions that exceed complexity thresholds."
        )
    
    def _analyze_ast(self, tree: ast.AST, source_code: str) -> List[RefactoringTarget]:
        """Analyze AST for complexity issues."""
        targets = []
        source_lines = source_code.splitlines()
        
        # Analyze all functions and methods
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics = self._calculate_function_complexity(node, source_lines)
                
                # Check if any threshold is exceeded
                if self._exceeds_thresholds(metrics):
                    target = self._create_complexity_target(node, metrics, source_lines)
                    targets.append(target)
        
        # Analyze classes for overall complexity
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_metrics = self._calculate_class_complexity(node, source_lines)
                if class_metrics["total_complexity"] > ComplexityThresholds.CLASS_COMPLEXITY:
                    target = self._create_class_complexity_target(node, class_metrics, source_lines)
                    targets.append(target)
        
        return targets
    
    def _calculate_function_complexity(self, func_node: ast.AST, source_lines: List[str]) -> ComplexityMetrics:
        """Calculate complexity metrics for a function."""
        # Cyclomatic complexity
        cyclomatic = self._calculate_cyclomatic_complexity(func_node)
        
        # Cognitive complexity
        cognitive = self._calculate_cognitive_complexity(func_node)
        
        # Line count
        start_line = func_node.lineno
        end_line = getattr(func_node, 'end_lineno', start_line)
        line_count = end_line - start_line + 1
        
        # Parameter count
        param_count = len(func_node.args.args)
        if func_node.args.vararg:
            param_count += 1
        if func_node.args.kwarg:
            param_count += 1
        
        # Nesting depth
        max_depth = self._calculate_max_nesting_depth(func_node)
        
        # Maintainability index (simplified)
        maintainability = self._calculate_maintainability_index(
            cyclomatic, line_count, len(source_lines)
        )
        
        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            maintainability_index=maintainability,
            max_nesting_depth=max_depth,
            line_count=line_count,
            parameter_count=param_count
        )
    
    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity (SonarQube style).

        Performs depth-aware traversal to correctly calculate cognitive complexity.
        Nesting level is properly incremented and decremented as we traverse the tree.
        
        Args:
            node: AST node to analyze
            
        Returns:
            Cognitive complexity score
            
        Example:
            >>> tool = ComplexityAnalyzerTool()
            >>> source = "def simple(): return 1"
            >>> tree = ast.parse(source)
            >>> func_node = tree.body[0]
            >>> complexity = tool._calculate_cognitive_complexity(func_node)
            >>> complexity >= 0
            True
        """
        return self._visit_for_cognitive_complexity(node, depth=0)
    
    def _visit_for_cognitive_complexity(self, node: ast.AST, depth: int = 0) -> int:
        """Recursive visitor for cognitive complexity calculation.
        
        Args:
            node: Current AST node
            depth: Current nesting depth
            
        Returns:
            Cognitive complexity score for this node and its children
        """
        score = 0
        
        for child in ast.iter_child_nodes(node):
            # Control flow structures add complexity based on nesting
            if self._is_control_flow_node(child):
                score += 1 + depth
                score += self._visit_for_cognitive_complexity(child, depth + 1)
            # Exception handlers add complexity
            elif isinstance(child, ast.ExceptHandler):
                score += 1 + depth
                score += self._visit_for_cognitive_complexity(child, depth + 1)
            # Boolean operations add complexity for each additional operand
            elif isinstance(child, ast.BoolOp) and len(child.values) > 1:
                score += len(child.values) - 1
                score += self._visit_for_cognitive_complexity(child, depth)
            # Comprehensions and expressions add nested complexity
            elif self._is_nested_expression(child):
                score += 1 + depth
                score += self._visit_for_cognitive_complexity(child, depth + 1)
            else:
                score += self._visit_for_cognitive_complexity(child, depth)
                
        return score
    
    def _is_control_flow_node(self, node: ast.AST) -> bool:
        """Check if node represents a control flow structure."""
        return isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try, ast.With))
    
    def _is_nested_expression(self, node: ast.AST) -> bool:
        """Check if node represents a nested expression that adds cognitive load."""
        return isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp, ast.Lambda, ast.IfExp))
    
    def _calculate_max_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0
        
        def visit_node(n):
            nonlocal max_depth, current_depth
            
            if isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.Try)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
                
                # Visit children
                for child in ast.iter_child_nodes(n):
                    visit_node(child)
                
                current_depth -= 1
            else:
                # Visit children
                for child in ast.iter_child_nodes(n):
                    visit_node(child)
        
        visit_node(node)
        return max_depth
    
    def _calculate_maintainability_index(self, cyclomatic: int, loc: int, total_loc: int) -> float:
        """Calculate maintainability index (simplified Halstead-based)."""
        # Simplified formula: higher is better
        try:
            # Avoid log(0) errors
            volume = max(1, loc * math.log2(max(2, cyclomatic + 1)))
            mi = 171 - 5.2 * math.log(volume) - 0.23 * cyclomatic - 16.2 * math.log(max(1, loc))
            return max(0, mi)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def _calculate_class_complexity(self, class_node: ast.ClassDef, source_lines: List[str]) -> Dict[str, Any]:
        """Calculate complexity metrics for a class."""
        total_complexity = 0
        method_count = 0
        total_lines = 0
        
        for node in ast.walk(class_node):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node != class_node:  # Don't count the class itself
                    metrics = self._calculate_function_complexity(node, source_lines)
                    total_complexity += metrics.cyclomatic_complexity
                    method_count += 1
                    total_lines += metrics.line_count
        
        return {
            "total_complexity": total_complexity,
            "method_count": method_count,
            "total_lines": total_lines,
            "average_method_complexity": total_complexity / max(1, method_count),
            "class_name": class_node.name
        }
    
    def _exceeds_thresholds(self, metrics: ComplexityMetrics) -> bool:
        """Check if complexity metrics exceed any thresholds."""
        return (
            metrics.cyclomatic_complexity > self.cyclomatic_threshold or
            metrics.cognitive_complexity > self.cognitive_threshold or
            metrics.maintainability_index < self.maintainability_threshold or
            metrics.max_nesting_depth > self.nesting_threshold or
            metrics.line_count > self.lines_threshold
        )
    
    def _create_complexity_target(
        self, 
        func_node: ast.AST, 
        metrics: ComplexityMetrics, 
        source_lines: List[str]
    ) -> RefactoringTarget:
        """Create a refactoring target for complex function.
        
        This method has been refactored to use extracted helper methods
        for better maintainability and single responsibility.
        """
        issues = self._calculate_issue_descriptions(metrics)
        severity = self._calculate_issue_severity(metrics)
        
        return self._build_refactoring_target(func_node, issues, severity, source_lines, metrics)
    
    def _calculate_issue_severity(self, metrics: ComplexityMetrics) -> float:
        """Calculate the overall severity score for complexity issues.
        
        Args:
            metrics: Complexity metrics for the function
            
        Returns:
            Numeric severity score
        """
        severity = 0.0
        
        # Cyclomatic complexity penalty
        if metrics.cyclomatic_complexity > self.cyclomatic_threshold:
            severity += metrics.cyclomatic_complexity - self.cyclomatic_threshold
        
        # Cognitive complexity penalty
        if metrics.cognitive_complexity > self.cognitive_threshold:
            severity += metrics.cognitive_complexity - self.cognitive_threshold
        
        # Maintainability penalty
        if metrics.maintainability_index < self.maintainability_threshold:
            severity += self.maintainability_threshold - metrics.maintainability_index
        
        # Nesting depth penalty
        if metrics.max_nesting_depth > self.nesting_threshold:
            severity += metrics.max_nesting_depth - self.nesting_threshold
        
        # Line count penalty (reduced weight)
        if metrics.line_count > self.lines_threshold:
            severity += (metrics.line_count - self.lines_threshold) * ComplexityThresholds.LINE_WEIGHT_FACTOR
        
        return severity
    
    def _calculate_issue_descriptions(self, metrics: ComplexityMetrics) -> List[str]:
        """Generate list of specific complexity issues.
        
        Args:
            metrics: Complexity metrics for the function
            
        Returns:
            List of issue descriptions
        """
        issues = []
        
        if metrics.cyclomatic_complexity > self.cyclomatic_threshold:
            issues.append(f"High cyclomatic complexity: {metrics.cyclomatic_complexity}")
        
        if metrics.cognitive_complexity > self.cognitive_threshold:
            issues.append(f"High cognitive complexity: {metrics.cognitive_complexity}")
        
        if metrics.maintainability_index < self.maintainability_threshold:
            issues.append(f"Low maintainability index: {metrics.maintainability_index:.1f}")
        
        if metrics.max_nesting_depth > self.nesting_threshold:
            issues.append(f"Deep nesting: {metrics.max_nesting_depth} levels")
        
        if metrics.line_count > self.lines_threshold:
            issues.append(f"Long function: {metrics.line_count} lines")
        
        return issues
    
    def _build_refactoring_target(
        self,
        func_node: ast.AST,
        issues: List[str],
        severity: float,
        source_lines: List[str],
        metrics: ComplexityMetrics
    ) -> RefactoringTarget:
        """Build the final RefactoringTarget object.
        
        Args:
            func_node: AST node for the function
            issues: List of complexity issues
            severity: Overall severity score
            source_lines: Source code lines
            metrics: Complexity metrics
            
        Returns:
            Configured RefactoringTarget
        """
        description = f"Function '{func_node.name}' has complexity issues: {', '.join(issues)}"
        
        code_snippet = self._extract_code_snippet(
            '\n'.join(source_lines), 
            func_node.lineno, 
            getattr(func_node, 'end_lineno', func_node.lineno)
        )
        
        # Calculate confidence based on severity (normalized)
        confidence = min(1.0, severity / ComplexityThresholds.SEVERITY_NORMALIZATION)
        
        return RefactoringTarget(
            start_line=func_node.lineno,
            end_line=getattr(func_node, 'end_lineno', func_node.lineno),
            target_type="complexity_reduction",
            complexity_score=severity,
            confidence=confidence,
            description=description,
            code_snippet=code_snippet,
            suggested_improvement=self._generate_complexity_improvement(func_node, metrics),
            benefits=[
                "Improved code readability",
                "Better testability",
                "Easier maintenance",
                "Reduced cognitive load"
            ],
            risks=[
                "May require significant refactoring",
                "Potential performance overhead from method calls",
                "Need to ensure test coverage"
            ]
        )
    
    def _create_class_complexity_target(
        self, 
        class_node: ast.ClassDef, 
        class_metrics: Dict[str, Any], 
        source_lines: List[str]
    ) -> RefactoringTarget:
        """Create a refactoring target for complex class."""
        description = (
            f"Class '{class_metrics['class_name']}' has high complexity: "
            f"{class_metrics['total_complexity']} total complexity across "
            f"{class_metrics['method_count']} methods"
        )
        
        code_snippet = self._extract_code_snippet(
            '\n'.join(source_lines), class_node.lineno, getattr(class_node, 'end_lineno', class_node.lineno)
        )
        
        return RefactoringTarget(
            start_line=class_node.lineno,
            end_line=getattr(class_node, 'end_lineno', class_node.lineno),
            target_type="class_decomposition",
            complexity_score=class_metrics['total_complexity'],
            confidence=0.8,
            description=description,
            code_snippet=code_snippet[:500] + "..." if len(code_snippet) > 500 else code_snippet,
            suggested_improvement=self._generate_class_improvement(class_node, class_metrics),
            benefits=[
                "Better separation of concerns",
                "Improved testability",
                "Single responsibility adherence",
                "Easier code navigation"
            ],
            risks=[
                "Significant refactoring effort",
                "Potential interface changes",
                "Need for comprehensive testing"
            ]
        )
    
    def _generate_complexity_improvement(self, func_node: ast.AST, metrics: ComplexityMetrics) -> str:
        """Generate improvement suggestions for complex function."""
        suggestions = []
        
        if metrics.line_count > self.lines_threshold:
            suggestions.append("Consider extracting logical blocks into separate methods")
        
        if metrics.max_nesting_depth > self.nesting_threshold:
            suggestions.append("Reduce nesting by using early returns and guard clauses")
        
        if metrics.parameter_count > ComplexityThresholds.PARAMETER_COUNT:
            suggestions.append("Consider using parameter objects or configuration classes")
        
        if metrics.cyclomatic_complexity > self.cyclomatic_threshold:
            suggestions.append("Split complex conditional logic into separate methods")
        
        if metrics.cognitive_complexity > self.cognitive_threshold:
            suggestions.append("Simplify logic by extracting helper methods")
        
        return f"""
Complexity Improvement Plan for '{func_node.name}':

Current Metrics:
- Cyclomatic Complexity: {metrics.cyclomatic_complexity}
- Cognitive Complexity: {metrics.cognitive_complexity}
- Lines of Code: {metrics.line_count}
- Nesting Depth: {metrics.max_nesting_depth}
- Maintainability Index: {metrics.maintainability_index:.1f}

Recommended Actions:
{chr(10).join(f"• {suggestion}" for suggestion in suggestions)}

Target Metrics:
- Cyclomatic Complexity: < {self.cyclomatic_threshold}
- Cognitive Complexity: < {self.cognitive_threshold}
- Nesting Depth: < {self.nesting_threshold}
- Maintainability Index: > {self.maintainability_threshold}
"""
    
    def _generate_class_improvement(self, class_node: ast.ClassDef, class_metrics: Dict[str, Any]) -> str:
        """Generate improvement suggestions for complex class."""
        return f"""
Class Complexity Improvement Plan for '{class_metrics['class_name']}':

Current Metrics:
- Total Complexity: {class_metrics['total_complexity']}
- Method Count: {class_metrics['method_count']}
- Average Method Complexity: {class_metrics['average_method_complexity']:.1f}
- Total Lines: {class_metrics['total_lines']}

Recommended Actions:
• Consider splitting class based on responsibilities
• Extract related methods into separate classes
• Use composition over inheritance
• Apply Single Responsibility Principle
• Consider facade or adapter patterns

Target: Keep classes focused on single responsibility with < 20 total complexity
"""
    
    def _apply_refactoring(self, code: str, targets: List[RefactoringTarget]) -> Any:
        """Complexity analyzer doesn't apply refactoring directly."""
        # This tool only analyzes complexity, doesn't apply refactoring
        # Return a result indicating analysis only
        from .base_refactoring_tool import RefactoringResult
        import time
        
        return RefactoringResult(
            success=True,
            original_code=code,
            refactored_code=code,  # No changes made
            targets_processed=targets,
            improvements={
                "complexity_analysis_completed": len(targets),
                "issues_identified": len(targets)
            },
            warnings=["This tool only analyzes complexity - use specific refactoring tools to apply changes"],
            errors=[],
            execution_time=0.1,
            tokens_used=0
        )