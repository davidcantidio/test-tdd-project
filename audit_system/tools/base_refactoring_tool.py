#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Refactoring Tool - Foundation for all Agno refactoring tools.

This module provides the base class for all refactoring tools in the Agno system.
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

try:
    from agno.tools import Tool
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    # Fallback Tool class for compatibility
    class Tool:
        def __init__(self, name: str, description: str):
            self.name = name
            self.description = description

@dataclass
class RefactoringTarget:
    """Represents a target for refactoring."""
    start_line: int
    end_line: int
    target_type: str  # method, block, expression, etc.
    complexity_score: float
    confidence: float
    description: str
    code_snippet: str
    suggested_improvement: str
    benefits: List[str]
    risks: List[str]

@dataclass
class RefactoringResult:
    """Result of applying a refactoring."""
    success: bool
    original_code: str
    refactored_code: str
    targets_processed: List[RefactoringTarget]
    improvements: Dict[str, float]  # complexity_reduction, readability_improvement, etc.
    warnings: List[str]
    errors: List[str]
    execution_time: float
    tokens_used: int = 0

class BaseRefactoringTool(Tool, ABC):
    """
    Base class for all Agno refactoring tools.
    
    Provides common functionality for:
    - AST parsing and analysis
    - Code pattern detection
    - Refactoring target identification
    - Safe code transformation
    - Result validation
    """
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Tool metadata
        tool_name = name or self.get_tool_name()
        tool_description = description or self.get_tool_description()
        
        super().__init__(
            name=tool_name,
            description=tool_description
        )
        
        # Configuration
        self.dry_run = False
        self.backup_enabled = True
        self.validation_enabled = True
        
        # Thresholds
        self.complexity_threshold = 10
        self.confidence_threshold = 0.7
        self.max_targets_per_file = 10
        
        self.logger.info(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the tool name for Agno registration."""
        pass
    
    @abstractmethod
    def get_tool_description(self) -> str:
        """Get the tool description for Agno registration."""
        pass
    
    @abstractmethod
    def _analyze_ast(self, tree: ast.AST, source_code: str) -> List[RefactoringTarget]:
        """Analyze AST and identify refactoring targets."""
        pass
    
    @abstractmethod
    def _apply_refactoring(self, code: str, targets: List[RefactoringTarget]) -> RefactoringResult:
        """Apply the refactoring to the code."""
        pass
    
    def analyze_code(self, code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze code for refactoring opportunities.
        
        This is the main entry point for Agno agents.
        """
        try:
            # Parse AST
            tree = ast.parse(code)
            
            # Analyze for targets
            targets = self._analyze_ast(tree, code)
            
            # Filter by confidence threshold
            high_confidence_targets = [
                target for target in targets 
                if target.confidence >= self.confidence_threshold
            ]
            
            # Limit number of targets
            if len(high_confidence_targets) > self.max_targets_per_file:
                high_confidence_targets = sorted(
                    high_confidence_targets, 
                    key=lambda t: t.confidence, 
                    reverse=True
                )[:self.max_targets_per_file]
            
            # Prepare result
            result = {
                "tool_name": self.name,
                "file_path": file_path or "unknown",
                "targets_found": len(targets),
                "high_confidence_targets": len(high_confidence_targets),
                "targets": [self._target_to_dict(target) for target in high_confidence_targets],
                "analysis_summary": self._generate_analysis_summary(targets),
                "recommendations": self._generate_recommendations(high_confidence_targets)
            }
            
            self.logger.info(
                f"Analysis complete: {len(targets)} targets found, "
                f"{len(high_confidence_targets)} high confidence"
            )
            
            return result
            
        except SyntaxError as e:
            self.logger.error(f"Syntax error in code: {e}")
            return {
                "error": f"Syntax error: {e}",
                "targets": [],
                "success": False
            }
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                "error": f"Analysis failed: {e}",
                "targets": [],
                "success": False
            }
    
    def apply_refactoring(self, code: str, target_indices: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Apply refactoring to code.
        
        This is the main refactoring entry point for Agno agents.
        """
        try:
            # First analyze to get targets
            analysis = self.analyze_code(code)
            if "error" in analysis:
                return analysis
            
            targets = [self._dict_to_target(target_dict) for target_dict in analysis["targets"]]
            
            # Filter by requested indices if provided
            if target_indices is not None:
                targets = [targets[i] for i in target_indices if 0 <= i < len(targets)]
            
            if not targets:
                return {
                    "success": False,
                    "message": "No targets to refactor",
                    "original_code": code,
                    "refactored_code": code
                }
            
            # Apply refactoring
            result = self._apply_refactoring(code, targets)
            
            # Validate result
            if self.validation_enabled:
                validation_result = self._validate_refactored_code(result)
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": f"Validation failed: {validation_result['errors']}",
                        "original_code": code,
                        "refactored_code": code
                    }
            
            # Prepare response
            response = {
                "success": result.success,
                "original_code": result.original_code,
                "refactored_code": result.refactored_code,
                "targets_processed": len(result.targets_processed),
                "improvements": result.improvements,
                "warnings": result.warnings,
                "errors": result.errors,
                "execution_time": result.execution_time,
                "tokens_used": result.tokens_used
            }
            
            self.logger.info(
                f"Refactoring {'successful' if result.success else 'failed'}: "
                f"{len(result.targets_processed)} targets processed"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Refactoring failed: {e}")
            return {
                "success": False,
                "error": f"Refactoring failed: {e}",
                "original_code": code,
                "refactored_code": code
            }
    
    def _target_to_dict(self, target: RefactoringTarget) -> Dict[str, Any]:
        """Convert RefactoringTarget to dictionary."""
        return {
            "start_line": target.start_line,
            "end_line": target.end_line,
            "target_type": target.target_type,
            "complexity_score": target.complexity_score,
            "confidence": target.confidence,
            "description": target.description,
            "code_snippet": target.code_snippet,
            "suggested_improvement": target.suggested_improvement,
            "benefits": target.benefits,
            "risks": target.risks
        }
    
    def _dict_to_target(self, target_dict: Dict[str, Any]) -> RefactoringTarget:
        """Convert dictionary to RefactoringTarget."""
        return RefactoringTarget(
            start_line=target_dict["start_line"],
            end_line=target_dict["end_line"],
            target_type=target_dict["target_type"],
            complexity_score=target_dict["complexity_score"],
            confidence=target_dict["confidence"],
            description=target_dict["description"],
            code_snippet=target_dict["code_snippet"],
            suggested_improvement=target_dict["suggested_improvement"],
            benefits=target_dict["benefits"],
            risks=target_dict["risks"]
        )
    
    def _generate_analysis_summary(self, targets: List[RefactoringTarget]) -> str:
        """Generate a human-readable analysis summary."""
        if not targets:
            return "No refactoring opportunities found."
        
        high_confidence = len([t for t in targets if t.confidence >= 0.8])
        medium_confidence = len([t for t in targets if 0.6 <= t.confidence < 0.8])
        
        complexity_scores = [t.complexity_score for t in targets]
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        
        return (
            f"Found {len(targets)} refactoring opportunities. "
            f"{high_confidence} high confidence, {medium_confidence} medium confidence. "
            f"Average complexity score: {avg_complexity:.1f}"
        )
    
    def _generate_recommendations(self, targets: List[RefactoringTarget]) -> List[str]:
        """Generate refactoring recommendations."""
        if not targets:
            return []
        
        recommendations = []
        
        # Group by target type
        type_counts = {}
        for target in targets:
            type_counts[target.target_type] = type_counts.get(target.target_type, 0) + 1
        
        for target_type, count in type_counts.items():
            recommendations.append(f"Consider refactoring {count} {target_type}(s)")
        
        # Add priority recommendations
        high_priority = [t for t in targets if t.confidence > 0.9 and t.complexity_score > 15]
        if high_priority:
            recommendations.append(f"High priority: {len(high_priority)} targets with very high confidence")
        
        return recommendations
    
    def _validate_refactored_code(self, result: RefactoringResult) -> Dict[str, Any]:
        """Validate refactored code."""
        validation_errors = []
        
        try:
            # Syntax validation
            ast.parse(result.refactored_code)
        except SyntaxError as e:
            validation_errors.append(f"Syntax error: {e}")
        
        # Basic length validation (refactored code shouldn't be dramatically different)
        original_lines = len(result.original_code.splitlines())
        refactored_lines = len(result.refactored_code.splitlines())
        
        if abs(refactored_lines - original_lines) > original_lines * 0.5:
            validation_errors.append(
                f"Dramatic line count change: {original_lines} -> {refactored_lines}"
            )
        
        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors
        }
    
    # Utility methods for subclasses
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of AST node."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.Try):
                complexity += len(child.handlers)
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.ListComp):
                complexity += 1
            elif isinstance(child, ast.DictComp):
                complexity += 1
            elif isinstance(child, ast.SetComp):
                complexity += 1
            elif isinstance(child, ast.GeneratorExp):
                complexity += 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity (SonarQube style)."""
        complexity = 0
        nesting_level = 0
        
        def visit_node(n, current_nesting=0):
            nonlocal complexity
            
            if isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                # Base increment + nesting increment
                complexity += 1 + current_nesting
                # Visit children with increased nesting
                for child in ast.iter_child_nodes(n):
                    visit_node(child, current_nesting + 1)
            elif isinstance(n, (ast.And, ast.Or)):
                complexity += 1
                # Visit children with same nesting
                for child in ast.iter_child_nodes(n):
                    visit_node(child, current_nesting)
            elif isinstance(n, ast.Try):
                complexity += 1
                # Visit children with increased nesting for except handlers
                for child in ast.iter_child_nodes(n):
                    if isinstance(child, ast.ExceptHandler):
                        complexity += 1 + current_nesting
                        for grandchild in ast.iter_child_nodes(child):
                            visit_node(grandchild, current_nesting + 1)
                    else:
                        visit_node(child, current_nesting)
            elif isinstance(n, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1 + current_nesting
                for child in ast.iter_child_nodes(n):
                    visit_node(child, current_nesting)
            elif isinstance(n, ast.Lambda):
                complexity += 1 + current_nesting
                for child in ast.iter_child_nodes(n):
                    visit_node(child, current_nesting)
            else:
                # Visit children with same nesting
                for child in ast.iter_child_nodes(n):
                    visit_node(child, current_nesting)
        
        visit_node(node)
        return complexity
    
    def _get_function_signature(self, func_node: ast.FunctionDef) -> str:
        """Get function signature as string."""
        args = []
        
        # Regular arguments
        for arg in func_node.args.args:
            args.append(arg.arg)
        
        # Default arguments
        defaults = func_node.args.defaults
        if defaults:
            num_defaults = len(defaults)
            num_args = len(func_node.args.args)
            for i, default in enumerate(defaults):
                arg_index = num_args - num_defaults + i
                if arg_index < len(func_node.args.args):
                    arg_name = func_node.args.args[arg_index].arg
                    # Simple default representation
                    args[arg_index] = f"{arg_name}=..."
        
        # *args
        if func_node.args.vararg:
            args.append(f"*{func_node.args.vararg.arg}")
        
        # **kwargs
        if func_node.args.kwarg:
            args.append(f"**{func_node.args.kwarg.arg}")
        
        return f"def {func_node.name}({', '.join(args)}):"
    
    def _extract_code_snippet(self, source_code: str, start_line: int, end_line: int) -> str:
        """Extract code snippet from source."""
        lines = source_code.splitlines()
        
        # Convert to 0-based indexing
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        
        return '\n'.join(lines[start_idx:end_idx])
    
    def _get_indentation(self, line: str) -> str:
        """Get indentation from line."""
        return line[:len(line) - len(line.lstrip())]
    
    def _normalize_indentation(self, code: str, target_indentation: str = "") -> str:
        """Normalize indentation of code block."""
        lines = code.splitlines()
        if not lines:
            return code
        
        # Find minimum indentation
        min_indent = float('inf')
        for line in lines:
            if line.strip():  # Skip empty lines
                indent_len = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent_len)
        
        if min_indent == float('inf'):
            min_indent = 0
        
        # Remove minimum indentation and add target indentation
        normalized_lines = []
        for line in lines:
            if line.strip():
                normalized_lines.append(target_indentation + line[min_indent:])
            else:
                normalized_lines.append("")
        
        return '\n'.join(normalized_lines)

# Tool registration for Agno (if available)
if AGNO_AVAILABLE:
    # This will be inherited by concrete tools
    pass
else:
    # Fallback for systems without Agno
    pass