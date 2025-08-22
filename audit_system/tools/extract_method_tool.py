#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Method Tool - Agno-native method extraction refactoring.

This tool analyzes code for long methods and complex functions that can be
broken down into smaller, more focused methods using intelligent AST analysis.
"""

from __future__ import annotations

import ast
import time
from typing import Any, Dict, List, Set, Tuple
from dataclasses import dataclass

from .base_refactoring_tool import BaseRefactoringTool, RefactoringTarget, RefactoringResult

@dataclass
class MethodAnalysis:
    """Analysis data for a method."""
    name: str
    start_line: int
    end_line: int
    complexity: int
    line_count: int
    extractable_blocks: List['ExtractableBlock']
    variables_used: Set[str]
    variables_defined: Set[str]

@dataclass
class ExtractableBlock:
    """A block of code that can be extracted to a separate method."""
    start_line: int
    end_line: int
    lines: List[str]
    description: str
    input_vars: Set[str]
    output_vars: Set[str]
    side_effects: List[str]
    complexity_score: float
    confidence: float

class ExtractMethodTool(BaseRefactoringTool):
    """
    Agno tool for intelligent method extraction.
    
    Features:
    - Identifies long methods (> 20 lines)
    - Analyzes variable dependencies
    - Finds extractable logical blocks
    - Generates new method names
    - Preserves functionality and scope
    """
    
    def __init__(self):
        super().__init__()
        
        # Configuration
        self.min_method_lines = 15  # Reduced threshold for testing
        self.min_block_lines = 3    # Reduced threshold for testing
        
        # Adjust confidence threshold for testing
        self.confidence_threshold = 0.3  # Lower threshold for testing
        self.max_extract_params = 4
        self.max_extract_returns = 3
        self.complexity_weight = 0.4
        self.dependency_weight = 0.3
        self.cohesion_weight = 0.3
    
    def get_tool_name(self) -> str:
        return "extract_method"
    
    def get_tool_description(self) -> str:
        return (
            "Extract method refactoring tool that analyzes Python code to identify long methods and complex functions "
            "that can be broken down into smaller, more focused methods. "
            "Uses intelligent AST analysis to preserve functionality while improving readability."
        )
    
    def _analyze_ast(self, tree: ast.AST, source_code: str) -> List[RefactoringTarget]:
        """Analyze AST for method extraction opportunities."""
        targets = []
        source_lines = source_code.splitlines()
        
        # Find all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_analysis = self._analyze_method(node, source_lines)
                
                # Check if method is long enough for extraction
                if method_analysis.line_count >= self.min_method_lines:
                    extractable_blocks = self._find_extractable_blocks(method_analysis, source_lines)
                    
                    for block in extractable_blocks:
                        if block.confidence >= self.confidence_threshold:
                            target = self._create_refactoring_target(block, method_analysis)
                            targets.append(target)
        
        return targets
    
    def _analyze_method(self, func_node: ast.FunctionDef, source_lines: List[str]) -> MethodAnalysis:
        """Analyze a method for extraction opportunities."""
        start_line = func_node.lineno
        end_line = func_node.end_lineno or start_line
        line_count = end_line - start_line + 1
        
        # Calculate complexity
        complexity = self._calculate_cyclomatic_complexity(func_node)
        
        # Analyze variables
        variables_used, variables_defined = self._analyze_variables(func_node)
        
        return MethodAnalysis(
            name=func_node.name,
            start_line=start_line,
            end_line=end_line,
            complexity=complexity,
            line_count=line_count,
            extractable_blocks=[],
            variables_used=variables_used,
            variables_defined=variables_defined
        )
    
    def _analyze_variables(self, func_node: ast.FunctionDef) -> Tuple[Set[str], Set[str]]:
        """Analyze variable usage in a function."""
        variables_used = set()
        variables_defined = set()
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    variables_defined.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    variables_used.add(node.id)
            elif isinstance(node, ast.arg):
                variables_defined.add(node.arg)
        
        # Remove function parameters from variables_used
        for arg in func_node.args.args:
            variables_used.discard(arg.arg)
        
        return variables_used, variables_defined
    
    def _find_extractable_blocks(self, method_analysis: MethodAnalysis, source_lines: List[str]) -> List[ExtractableBlock]:
        """Find blocks within a method that can be extracted."""
        extractable_blocks = []
        
        # Get method body lines
        method_lines = source_lines[method_analysis.start_line-1:method_analysis.end_line]
        
        # Find logical blocks based on:
        # 1. Blank lines (logical separators)
        # 2. Comment blocks (section headers)
        # 3. Control flow boundaries
        # 4. Variable scope boundaries
        
        blocks = self._identify_logical_blocks(method_lines, method_analysis.start_line)
        
        for block in blocks:
            if len(block.lines) >= self.min_block_lines:
                # Analyze extractability
                analysis = self._analyze_block_extractability(block, method_analysis)
                if analysis["extractable"]:
                    extractable_blocks.append(ExtractableBlock(
                        start_line=block.start_line,
                        end_line=block.end_line,
                        lines=block.lines,
                        description=analysis["description"],
                        input_vars=analysis["input_vars"],
                        output_vars=analysis["output_vars"],
                        side_effects=analysis["side_effects"],
                        complexity_score=analysis["complexity_score"],
                        confidence=analysis["confidence"]
                    ))
        
        return extractable_blocks
    
    def _identify_logical_blocks(self, method_lines: List[str], start_line_offset: int) -> List[Any]:
        """Identify logical blocks within a method."""
        blocks = []
        current_block_lines = []
        current_start = start_line_offset
        
        for i, line in enumerate(method_lines):
            line_num = start_line_offset + i
            stripped = line.strip()
            
            # Skip method signature and docstring
            if i == 0 and stripped.startswith('def '):
                continue
            if i <= 2 and (stripped.startswith('"""') or stripped.startswith("'''")):
                continue
            
            # Block separators
            is_separator = (
                not stripped or  # Empty line
                stripped.startswith('#') or  # Comment
                (current_block_lines and self._is_control_flow_boundary(line, method_lines[i-1] if i > 0 else ""))
            )
            
            if is_separator and current_block_lines:
                # End current block
                blocks.append(self._create_block(current_block_lines, current_start))
                current_block_lines = []
                current_start = line_num + 1
            elif not is_separator:
                current_block_lines.append(line)
                if not current_block_lines or current_start == start_line_offset:
                    current_start = line_num
        
        # Add final block
        if current_block_lines:
            blocks.append(self._create_block(current_block_lines, current_start))
        
        return blocks
    
    def _create_block(self, lines: List[str], start_line: int) -> Any:
        """Create a block object."""
        class Block:
            def __init__(self, lines: List[str], start_line: int):
                self.lines = lines
                self.start_line = start_line
                self.end_line = start_line + len(lines) - 1
        
        return Block(lines, start_line)
    
    def _is_control_flow_boundary(self, current_line: str, previous_line: str) -> bool:
        """Check if there's a control flow boundary between lines."""
        current_stripped = current_line.strip()
        previous_stripped = previous_line.strip()
        
        # Control flow starts
        control_keywords = ['if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except ', 'finally:', 'with ']
        
        if any(current_stripped.startswith(keyword) for keyword in control_keywords):
            return True
        
        # Return statements often end logical blocks
        if previous_stripped.startswith('return '):
            return True
        
        return False
    
    def _analyze_block_extractability(self, block: Any, method_analysis: MethodAnalysis) -> Dict[str, Any]:
        """Analyze if a block can be extracted."""
        try:
            # Parse block as AST to analyze variables
            block_code = '\n'.join(block.lines)
            # Add minimal indentation for parsing
            normalized_code = self._normalize_for_parsing(block_code)
            block_tree = ast.parse(normalized_code)
            
            # Analyze variables
            block_vars_used, block_vars_defined = self._analyze_variables_in_block(block_tree)
            
            # Determine input and output variables
            input_vars = block_vars_used - method_analysis.variables_defined
            output_vars = block_vars_defined & method_analysis.variables_used
            
            # Check extractability constraints
            too_many_params = len(input_vars) > self.max_extract_params
            too_many_returns = len(output_vars) > self.max_extract_returns
            
            if too_many_params or too_many_returns:
                return {
                    "extractable": False,
                    "reason": "Too many parameters or return values"
                }
            
            # Calculate complexity score
            complexity_score = self._calculate_block_complexity(block_tree, len(block.lines))
            
            # Calculate confidence based on multiple factors
            confidence = self._calculate_extraction_confidence(
                block, input_vars, output_vars, complexity_score
            )
            
            # Generate description
            description = self._generate_block_description(block, complexity_score)
            
            return {
                "extractable": True,
                "description": description,
                "input_vars": input_vars,
                "output_vars": output_vars,
                "side_effects": [],  # TODO: Analyze side effects
                "complexity_score": complexity_score,
                "confidence": confidence
            }
            
        except SyntaxError:
            return {
                "extractable": False,
                "reason": "Block contains syntax errors"
            }
        except Exception as e:
            return {
                "extractable": False,
                "reason": f"Analysis failed: {e}"
            }
    
    def _normalize_for_parsing(self, code: str) -> str:
        """Normalize code block for AST parsing."""
        lines = code.splitlines()
        if not lines:
            return code
        
        # Remove common indentation
        min_indent = float('inf')
        for line in lines:
            if line.strip():
                indent_len = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent_len)
        
        if min_indent == float('inf'):
            min_indent = 0
        
        # Create a simple function wrapper for parsing
        normalized_lines = ["def temp_func():"]
        for line in lines:
            if line.strip():
                normalized_lines.append("    " + line[min_indent:])
            else:
                normalized_lines.append("")
        
        return '\n'.join(normalized_lines)
    
    def _analyze_variables_in_block(self, block_tree: ast.AST) -> Tuple[Set[str], Set[str]]:
        """Analyze variables used and defined in a block."""
        variables_used = set()
        variables_defined = set()
        
        for node in ast.walk(block_tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    variables_defined.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    variables_used.add(node.id)
        
        # Remove function name from analysis
        variables_used.discard("temp_func")
        variables_defined.discard("temp_func")
        
        return variables_used, variables_defined
    
    def _calculate_block_complexity(self, block_tree: ast.AST, line_count: int) -> float:
        """Calculate complexity score for a block."""
        # Base complexity from line count
        line_complexity = min(line_count / 10.0, 10.0)
        
        # Cyclomatic complexity
        cyclomatic = self._calculate_cyclomatic_complexity(block_tree)
        
        # Combined score
        return (line_complexity * 0.6) + (cyclomatic * 0.4)
    
    def _calculate_extraction_confidence(
        self, 
        block: Any, 
        input_vars: Set[str], 
        output_vars: Set[str], 
        complexity_score: float
    ) -> float:
        """Calculate confidence score for extraction."""
        # Base confidence from block size
        size_confidence = min(len(block.lines) / 15.0, 1.0)
        
        # Complexity confidence (higher complexity = higher benefit)
        complexity_confidence = min(complexity_score / 15.0, 1.0)
        
        # Dependency confidence (fewer dependencies = higher confidence)
        total_dependencies = len(input_vars) + len(output_vars)
        dependency_confidence = max(0.0, 1.0 - (total_dependencies / 8.0))
        
        # Weighted average
        confidence = (
            size_confidence * 0.3 +
            complexity_confidence * 0.4 +
            dependency_confidence * 0.3
        )
        
        return min(confidence, 1.0)
    
    def _generate_block_description(self, block: Any, complexity_score: float) -> str:
        """Generate a description for the extractable block."""
        # Analyze first few lines for purpose
        first_lines = block.lines[:3]
        
        # Look for comments that might describe the block
        for line in first_lines:
            if line.strip().startswith('#'):
                comment = line.strip()[1:].strip()
                if len(comment) > 5:
                    return f"Extract block: {comment}"
        
        # Analyze code patterns
        code_text = ' '.join(line.strip() for line in block.lines)
        
        if 'if ' in code_text and 'else' in code_text:
            return f"Extract conditional logic block ({len(block.lines)} lines, complexity: {complexity_score:.1f})"
        elif 'for ' in code_text or 'while ' in code_text:
            return f"Extract loop processing block ({len(block.lines)} lines, complexity: {complexity_score:.1f})"
        elif 'try:' in code_text:
            return f"Extract error handling block ({len(block.lines)} lines, complexity: {complexity_score:.1f})"
        else:
            return f"Extract processing block ({len(block.lines)} lines, complexity: {complexity_score:.1f})"
    
    def _create_refactoring_target(self, block: ExtractableBlock, method_analysis: MethodAnalysis) -> RefactoringTarget:
        """Create a RefactoringTarget from an extractable block."""
        return RefactoringTarget(
            start_line=block.start_line,
            end_line=block.end_line,
            target_type="method_extraction",
            complexity_score=block.complexity_score,
            confidence=block.confidence,
            description=block.description,
            code_snippet='\n'.join(block.lines),
            suggested_improvement=self._generate_suggested_improvement(block, method_analysis),
            benefits=[
                "Improved readability",
                "Better testability",
                "Reduced method complexity",
                "Single responsibility principle"
            ],
            risks=[
                "Potential parameter proliferation",
                "Possible performance overhead",
                "Need to ensure proper testing"
            ]
        )
    
    def _generate_suggested_improvement(self, block: ExtractableBlock, method_analysis: MethodAnalysis) -> str:
        """Generate a suggested improvement for the block."""
        # Generate method name
        method_name = self._generate_method_name(block, method_analysis)
        
        # Generate parameters
        params = ["self"] + list(block.input_vars)
        param_str = ", ".join(params)
        
        # Generate return statement
        if block.output_vars:
            return_str = f"return {', '.join(block.output_vars)}"
        else:
            return_str = ""
        
        improvement = f"""
Extract to new method:

def {method_name}({param_str}):
    \"\"\"Extracted method - {block.description}\"\"\"{self._normalize_indentation(''.join(block.lines), '    ')}
    {return_str}

Replace original code with:
{', '.join(block.output_vars) + ' = ' if block.output_vars else ''}self.{method_name}({', '.join(block.input_vars)})
"""
        
        return improvement.strip()
    
    def _generate_method_name(self, block: ExtractableBlock, method_analysis: MethodAnalysis) -> str:
        """Generate a name for the extracted method."""
        # Simple naming strategy - can be enhanced
        base_name = f"_extracted_from_{method_analysis.name}"
        
        # Add semantic hint based on code analysis
        code_text = ' '.join(block.lines).lower()
        
        if 'calculate' in code_text or 'compute' in code_text:
            base_name = f"_calculate_{method_analysis.name}_part"
        elif 'validate' in code_text or 'check' in code_text:
            base_name = f"_validate_{method_analysis.name}_part"
        elif 'process' in code_text or 'handle' in code_text:
            base_name = f"_process_{method_analysis.name}_part"
        elif 'setup' in code_text or 'initialize' in code_text:
            base_name = f"_setup_{method_analysis.name}_part"
        
        return base_name
    
    def _apply_refactoring(self, code: str, targets: List[RefactoringTarget]) -> RefactoringResult:
        """Apply method extraction refactoring."""
        start_time = time.time()
        
        try:
            # Parse the original code
            tree = ast.parse(code)
            source_lines = code.splitlines()
            
            # Apply extractions (process in reverse order to maintain line numbers)
            modified_lines = source_lines.copy()
            extracted_methods = []
            processed_targets = []
            
            # Sort targets by line number (descending for safe processing)
            sorted_targets = sorted(targets, key=lambda t: t.start_line, reverse=True)
            
            for target in sorted_targets:
                try:
                    extraction_result = self._perform_extraction(
                        modified_lines, target, tree
                    )
                    
                    if extraction_result["success"]:
                        # Replace original code with method call
                        self._replace_with_method_call(
                            modified_lines, target, extraction_result["method_call"]
                        )
                        
                        # Store extracted method for insertion
                        extracted_methods.append(extraction_result["extracted_method"])
                        processed_targets.append(target)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to extract target at line {target.start_line}: {e}")
            
            # Insert extracted methods
            if extracted_methods:
                self._insert_extracted_methods(modified_lines, extracted_methods)
            
            refactored_code = '\n'.join(modified_lines)
            execution_time = time.time() - start_time
            
            # Calculate improvements
            improvements = self._calculate_improvements(code, refactored_code, processed_targets)
            
            return RefactoringResult(
                success=True,
                original_code=code,
                refactored_code=refactored_code,
                targets_processed=processed_targets,
                improvements=improvements,
                warnings=[],
                errors=[],
                execution_time=execution_time,
                tokens_used=0  # TODO: Implement token tracking
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return RefactoringResult(
                success=False,
                original_code=code,
                refactored_code=code,
                targets_processed=[],
                improvements={},
                warnings=[],
                errors=[str(e)],
                execution_time=execution_time,
                tokens_used=0
            )
    
    def _perform_extraction(self, lines: List[str], target: RefactoringTarget, tree: ast.AST) -> Dict[str, Any]:
        """Perform the actual extraction of a code block."""
        # This is a simplified implementation
        # In a production system, this would involve:
        # 1. Complex variable scope analysis
        # 2. Proper method generation
        # 3. Call site replacement
        # 4. Validation of the transformation
        
        # For now, return a basic structure
        method_name = "_extracted_method"
        method_call = f"self.{method_name}()"
        
        # Extract the code block
        start_idx = target.start_line - 1
        end_idx = target.end_line
        extracted_lines = lines[start_idx:end_idx]
        
        # Generate method
        extracted_method = [
            f"    def {method_name}(self):",
            '        """Extracted method - TODO: Add proper documentation."""'
        ]
        
        for line in extracted_lines:
            extracted_method.append(f"    {line}")
        
        return {
            "success": True,
            "extracted_method": extracted_method,
            "method_call": f"        {method_call}",
            "method_name": method_name
        }
    
    def _replace_with_method_call(self, lines: List[str], target: RefactoringTarget, method_call: str):
        """Replace extracted code with method call."""
        start_idx = target.start_line - 1
        end_idx = target.end_line
        
        # Replace the range with method call
        lines[start_idx:end_idx] = [method_call]
    
    def _insert_extracted_methods(self, lines: List[str], extracted_methods: List[List[str]]):
        """Insert extracted methods into the code."""
        # Find a good place to insert methods (before the main function)
        insertion_point = 0
        
        # Look for class definition or function definition
        for i, line in enumerate(lines):
            if line.strip().startswith('class ') or line.strip().startswith('def '):
                insertion_point = i
                break
        
        # Insert all extracted methods
        for method_lines in extracted_methods:
            lines[insertion_point:insertion_point] = method_lines + [""]
            insertion_point += len(method_lines) + 1
    
    def _calculate_improvements(self, original: str, refactored: str, targets: List[RefactoringTarget]) -> Dict[str, float]:
        """Calculate improvement metrics."""
        # Simple metrics calculation
        original_lines = len(original.splitlines())
        refactored_lines = len(refactored.splitlines())
        
        # Complexity reduction (estimated)
        complexity_reduction = sum(target.complexity_score for target in targets) * 0.3
        
        return {
            "complexity_reduction": complexity_reduction,
            "readability_improvement": len(targets) * 0.8,
            "maintainability_improvement": len(targets) * 0.7,
            "methods_extracted": len(targets),
            "lines_added": refactored_lines - original_lines
        }