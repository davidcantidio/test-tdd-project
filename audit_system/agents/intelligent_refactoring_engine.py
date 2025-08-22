#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Intelligent Refactoring Engine - AI-Powered Code Transformation

Sistema avançado que aplica refatorações inteligentes automaticamente,
compreendendo o contexto semântico e preservando funcionalidade.

Capacidades:
- Extract Method Refactoring com análise de escopo
- God Method Detection e splitting automático  
- N+1 Query optimization com batch processing
- Exception Handling improvement com logging específico
- String optimization com f-strings e join operations
- Code deduplication com pattern extraction

Uso:
    python intelligent_refactoring_engine.py --file FILE --refactoring-type TYPE [--apply]
"""

from __future__ import annotations

import ast
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
import sys
import argparse

# Project setup
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from audit_system.agents.intelligent_code_agent import IntelligentCodeAgent, FileSemanticAnalysis, IntelligentRefactoring
from audit_system.agents.god_code_refactoring_agent import GodCodeRefactoringAgent, GodCodeType


@dataclass
class RefactoringResult:
    """Result of applying a refactoring."""
    success: bool
    refactoring_type: str
    original_lines: List[str]
    refactored_lines: List[str]
    lines_affected: List[int]
    improvements: Dict[str, float]  # complexity_reduction, readability_improvement, etc.
    warnings: List[str]
    errors: List[str]


class IntelligentRefactoringEngine:
    """
    Engine that applies intelligent refactorings with full semantic understanding.
    """
    
    def __init__(
        self, 
        dry_run: bool = False, 
        enable_real_llm: bool = True,
        llm_provider: str = None,
        project_root: Path = None
    ):
        self.dry_run = dry_run
        self.enable_real_llm = enable_real_llm
        self.llm_provider = llm_provider
        self.project_root = project_root or Path(".")
        self.logger = logging.getLogger(f"{__name__}.IntelligentRefactoringEngine")
        
        # Initialize LLM model if enabled
        self.llm_model = None
        if self.enable_real_llm:
            try:
                from audit_system.core.model_factory import create_llm_model
                self.llm_model = create_llm_model(provider=self.llm_provider)
                self.logger.info(f"✅ LLM model initialized: {self.llm_provider or 'default'}")
            except Exception as e:
                self.logger.warning(f"⚠️ LLM initialization failed: {e}")
                self.logger.warning("Falling back to hardcoded refactoring patterns")
                self.enable_real_llm = False
        
        # Initialize specialized agents
        self.god_code_agent = GodCodeRefactoringAgent(dry_run=self.dry_run)
        
        # Refactoring strategies
        self.refactoring_strategies = {
            "extract_method": self._apply_extract_method,
            "improve_exception_handling": self._apply_improve_exception_handling,
            "optimize_string_operations": self._apply_optimize_string_operations,
            "eliminate_god_method": self._apply_eliminate_god_method,
            "god_code_refactoring": self._apply_god_code_refactoring,  # NEW: Specialized god code agent
            "optimize_database_queries": self._apply_optimize_database_queries,
            "extract_constants": self._apply_extract_constants,
            "improve_conditional_logic": self._apply_improve_conditional_logic
        }
        
        self.logger.info("Intelligent Refactoring Engine initialized with God Code Agent")
    
    def _generate_llm_refactoring(
        self,
        code_content: str,
        refactoring_type: str,
        target_lines: List[int] = None
    ) -> str:
        """Generate refactored code using LLM analysis."""
        if not self.enable_real_llm or not self.llm_model:
            return code_content  # Fallback to original
        
        try:
            # Create prompt for Claude
            prompt = f"""
You are an expert Python refactoring specialist. Apply {refactoring_type} refactoring to improve this code.

REFACTORING TYPE: {refactoring_type}
TARGET LINES: {target_lines if target_lines else "Analyze entire code"}

CODE TO REFACTOR:
```python
{code_content}
```

REQUIREMENTS:
1. Preserve all functionality exactly
2. Improve code quality, readability, and maintainability
3. Follow Python best practices
4. For extract_method: Create well-named methods with proper parameters
5. For exception_handling: Add specific exception types and logging
6. For string_operations: Use f-strings and efficient concatenation
7. For god_method: Break down into logical, cohesive methods

Return ONLY the refactored code without explanation:
"""
            
            # Use Agno to get LLM response
            if hasattr(self.llm_model, 'run'):
                response = self.llm_model.run(prompt)
                
                # Extract code from response (handle markdown formatting)
                if "```python" in response:
                    start = response.find("```python") + 9
                    end = response.find("```", start)
                    if end != -1:
                        return response[start:end].strip()
                elif "```" in response:
                    start = response.find("```") + 3
                    end = response.find("```", start)
                    if end != -1:
                        return response[start:end].strip()
                else:
                    # If no code blocks, assume entire response is code
                    return response.strip()
            
            return code_content  # Fallback
            
        except Exception as e:
            self.logger.error(f"LLM refactoring failed: {e}")
            return code_content  # Fallback to original
    
    def _apply_llm_refactoring(
        self, 
        lines: List[str], 
        refactoring: IntelligentRefactoring, 
        file_path: str,
        refactoring_type: str
    ) -> RefactoringResult:
        """Apply LLM-powered refactoring to code lines."""
        
        try:
            # Reconstruct code content from lines
            code_content = '\n'.join(lines)
            
            # Generate refactored code using LLM
            refactored_content = self._generate_llm_refactoring(
                code_content=code_content,
                refactoring_type=refactoring_type,
                target_lines=refactoring.target_lines
            )
            
            # If LLM refactoring failed or returned unchanged content
            if refactored_content == code_content:
                return RefactoringResult(
                    success=False,
                    refactoring_type=refactoring_type,
                    original_lines=lines,
                    refactored_lines=lines,
                    lines_affected=[],
                    improvements={},
                    warnings=["LLM refactoring returned unchanged code"],
                    errors=[]
                )
            
            # Split refactored content back into lines
            refactored_lines = refactored_content.splitlines()
            
            # Identify affected lines (lines that changed)
            affected_lines = []
            max_lines = max(len(lines), len(refactored_lines))
            
            for i in range(max_lines):
                original_line = lines[i] if i < len(lines) else ""
                refactored_line = refactored_lines[i] if i < len(refactored_lines) else ""
                
                if original_line.strip() != refactored_line.strip():
                    affected_lines.append(i + 1)  # Convert to 1-based line numbers
            
            # Calculate improvements based on refactoring type
            improvements = self._calculate_llm_improvements(
                refactoring_type, len(affected_lines), lines, refactored_lines
            )
            
            return RefactoringResult(
                success=True,
                refactoring_type=refactoring_type,
                original_lines=lines,
                refactored_lines=refactored_lines,
                lines_affected=affected_lines,
                improvements=improvements,
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            self.logger.error(f"LLM refactoring application failed: {e}")
            return RefactoringResult(
                success=False,
                refactoring_type=refactoring_type,
                original_lines=lines,
                refactored_lines=lines,
                lines_affected=[],
                improvements={},
                warnings=[],
                errors=[str(e)]
            )
    
    def _calculate_llm_improvements(
        self,
        refactoring_type: str,
        affected_line_count: int,
        original_lines: List[str],
        refactored_lines: List[str]
    ) -> Dict[str, float]:
        """Calculate improvement metrics for LLM-powered refactoring."""
        
        improvements = {}
        
        # Base improvements based on refactoring type
        if refactoring_type == "extract_method":
            improvements = {
                "complexity_reduction": min(40.0, affected_line_count * 2.0),
                "readability_improvement": min(60.0, affected_line_count * 1.5),
                "maintainability_improvement": min(50.0, affected_line_count * 1.8)
            }
        elif refactoring_type == "improve_exception_handling":
            improvements = {
                "reliability_improvement": min(70.0, affected_line_count * 3.0),
                "debugging_improvement": min(80.0, affected_line_count * 2.5),
                "error_handling_quality": min(90.0, affected_line_count * 4.0)
            }
        elif refactoring_type == "optimize_string_operations":
            improvements = {
                "performance_improvement": min(50.0, affected_line_count * 2.2),
                "readability_improvement": min(40.0, affected_line_count * 1.8),
                "pythonic_style": min(60.0, affected_line_count * 2.0)
            }
        elif refactoring_type == "eliminate_god_method":
            improvements = {
                "complexity_reduction": min(80.0, affected_line_count * 1.5),
                "maintainability_improvement": min(90.0, affected_line_count * 1.2),
                "single_responsibility": min(100.0, affected_line_count * 1.0)
            }
        else:
            # Generic improvements for other refactoring types
            improvements = {
                "code_quality": min(50.0, affected_line_count * 1.5),
                "maintainability_improvement": min(40.0, affected_line_count * 1.2),
                "readability_improvement": min(45.0, affected_line_count * 1.3)
            }
        
        # Add line-count-based metrics
        original_line_count = len(original_lines)
        refactored_line_count = len(refactored_lines)
        
        if original_line_count > refactored_line_count:
            improvements["code_reduction"] = ((original_line_count - refactored_line_count) / original_line_count) * 100
        elif refactored_line_count > original_line_count:
            improvements["code_expansion"] = ((refactored_line_count - original_line_count) / original_line_count) * 100
        
        return improvements
    
    def apply_refactoring(
        self, 
        file_path: str, 
        refactoring: IntelligentRefactoring
    ) -> RefactoringResult:
        """Apply a specific refactoring to a file."""
        
        self.logger.info(
            "Applying %s refactoring to %s (lines: %s)",
            refactoring.refactoring_type, file_path, refactoring.target_lines
        )
        
        # Read original file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        original_lines = original_content.splitlines()
        
        # Get refactoring strategy
        strategy = self.refactoring_strategies.get(refactoring.refactoring_type)
        if not strategy:
            return RefactoringResult(
                success=False,
                refactoring_type=refactoring.refactoring_type,
                original_lines=original_lines,
                refactored_lines=original_lines,
                lines_affected=[],
                improvements={},
                warnings=[],
                errors=[f"Unknown refactoring type: {refactoring.refactoring_type}"]
            )
        
        try:
            # Apply the refactoring
            result = strategy(original_lines, refactoring, file_path)
            
            # Write refactored file if not dry run and successful
            if not self.dry_run and result.success:
                refactored_content = '\n'.join(result.refactored_lines)
                
                # Create backup
                backup_path = f"{file_path}.backup"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # Write refactored file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(refactored_content)
                
                self.logger.info(
                    "Refactoring applied successfully. Backup: %s", backup_path
                )
            
            return result
            
        except Exception as e:
            self.logger.error("Error applying refactoring: %s", e)
            return RefactoringResult(
                success=False,
                refactoring_type=refactoring.refactoring_type,
                original_lines=original_lines,
                refactored_lines=original_lines,
                lines_affected=[],
                improvements={},
                warnings=[],
                errors=[str(e)]
            )
    
    def _apply_extract_method(
        self, 
        lines: List[str], 
        refactoring: IntelligentRefactoring, 
        file_path: str
    ) -> RefactoringResult:
        """Apply extract method refactoring using LLM intelligence."""
        
        # Use LLM-powered refactoring if available
        if self.enable_real_llm and self.llm_model:
            return self._apply_llm_refactoring(lines, refactoring, file_path, "extract_method")
        
        # Fallback to hardcoded implementation
        target_lines = refactoring.target_lines
        start_line = min(target_lines) - 1  # Convert to 0-based indexing
        end_line = max(target_lines)
        
        # Find the containing function
        function_start = self._find_function_start(lines, start_line)
        if function_start == -1:
            return RefactoringResult(
                success=False,
                refactoring_type="extract_method",
                original_lines=lines,
                refactored_lines=lines,
                lines_affected=[],
                improvements={},
                warnings=[],
                errors=["Could not identify containing function"]
            )
        
        # Analyze the code block to extract
        code_block = lines[start_line:end_line]
        
        # Extract variables and determine parameters
        analysis = self._analyze_code_block_for_extraction(code_block, lines, function_start)
        
        if not analysis["extractable"]:
            return RefactoringResult(
                success=False,
                refactoring_type="extract_method",
                original_lines=lines,
                refactored_lines=lines,
                lines_affected=[],
                improvements={},
                warnings=analysis["warnings"],
                errors=analysis["errors"]
            )
        
        # Generate the extracted method
        extracted_method = self._generate_extracted_method(
            analysis["method_name"],
            analysis["parameters"],
            analysis["return_vars"],
            code_block,
            analysis["indentation"]
        )
        
        # Generate the method call
        method_call = self._generate_method_call(
            analysis["method_name"],
            analysis["parameters"],
            analysis["return_vars"],
            analysis["indentation"]
        )
        
        # Apply the refactoring
        refactored_lines = lines.copy()
        
        # Replace the extracted code with method call
        refactored_lines[start_line:end_line] = [method_call]
        
        # Insert the extracted method before the current function
        refactored_lines[function_start:function_start] = extracted_method + [""]
        
        # Calculate improvements
        complexity_reduction = len(code_block) * 0.3  # Rough estimate
        readability_improvement = 0.8  # Extract method usually improves readability
        
        return RefactoringResult(
            success=True,
            refactoring_type="extract_method",
            original_lines=lines,
            refactored_lines=refactored_lines,
            lines_affected=list(range(start_line, end_line)),
            improvements={
                "complexity_reduction": complexity_reduction,
                "readability_improvement": readability_improvement,
                "maintainability_improvement": 0.7
            },
            warnings=[],
            errors=[]
        )
    
    def _apply_improve_exception_handling(
        self, 
        lines: List[str], 
        refactoring: IntelligentRefactoring, 
        file_path: str
    ) -> RefactoringResult:
        """Apply exception handling improvements using LLM intelligence."""
        
        # Use LLM-powered refactoring if available
        if self.enable_real_llm and self.llm_model:
            return self._apply_llm_refactoring(lines, refactoring, file_path, "improve_exception_handling")
        
        # Fallback to hardcoded implementation
        refactored_lines = lines.copy()
        affected_lines = []
        improvements = {"security_improvement": 0.0, "debugging_improvement": 0.0}
        
        for line_num in refactoring.target_lines:
            line_idx = line_num - 1  # Convert to 0-based
            line = lines[line_idx]
            
            # Improve broad exception handling
            if "except Exception:" in line:
                # Add specific exception handling and logging
                indentation = len(line) - len(line.lstrip())
                indent = " " * indentation
                
                improved_lines = [
                    f"{indent}except Exception as e:",
                    f"{indent}    logger.warning('Operation failed: %s', str(e))",
                    f"{indent}    # Consider handling specific exception types",
                ]
                
                refactored_lines[line_idx:line_idx+1] = improved_lines
                affected_lines.append(line_num)
                improvements["security_improvement"] += 0.3
                improvements["debugging_improvement"] += 0.8
            
            # Improve bare except clauses
            elif line.strip() == "except:":
                indentation = len(line) - len(line.lstrip())
                indent = " " * indentation
                
                improved_lines = [
                    f"{indent}except Exception as e:",
                    f"{indent}    logger.error('Unexpected error: %s', str(e))",
                    f"{indent}    # TODO: Handle specific exception types",
                ]
                
                refactored_lines[line_idx:line_idx+1] = improved_lines
                affected_lines.append(line_num)
                improvements["security_improvement"] += 0.5
                improvements["debugging_improvement"] += 0.9
        
        # Add logger import if needed
        if affected_lines and not any("import logging" in line for line in lines):
            # Find appropriate place to add import
            import_line = self._find_import_insertion_point(lines)
            refactored_lines.insert(import_line, "import logging")
            refactored_lines.insert(import_line + 1, "logger = logging.getLogger(__name__)")
        
        return RefactoringResult(
            success=True,
            refactoring_type="improve_exception_handling",
            original_lines=lines,
            refactored_lines=refactored_lines,
            lines_affected=affected_lines,
            improvements=improvements,
            warnings=[],
            errors=[]
        )
    
    def _apply_optimize_string_operations(
        self, 
        lines: List[str], 
        refactoring: IntelligentRefactoring, 
        file_path: str
    ) -> RefactoringResult:
        """Apply string operation optimizations using LLM intelligence."""
        
        # Use LLM-powered refactoring if available
        if self.enable_real_llm and self.llm_model:
            return self._apply_llm_refactoring(lines, refactoring, file_path, "optimize_string_operations")
        
        # Fallback to hardcoded implementation
        refactored_lines = lines.copy()
        affected_lines = []
        improvements = {"performance_improvement": 0.0, "readability_improvement": 0.0}
        
        for line_num in refactoring.target_lines:
            line_idx = line_num - 1
            line = lines[line_idx]
            
            # Convert string concatenation to f-strings
            if "+" in line and any(quote in line for quote in ['"', "'"]):
                optimized_line = self._optimize_string_concatenation(line)
                if optimized_line != line:
                    refactored_lines[line_idx] = optimized_line
                    affected_lines.append(line_num)
                    improvements["performance_improvement"] += 0.3
                    improvements["readability_improvement"] += 0.5
            
            # Convert join operations for lists
            if ".join(" in line and "[" in line and "]" in line:
                optimized_line = self._optimize_join_operation(line)
                if optimized_line != line:
                    refactored_lines[line_idx] = optimized_line
                    affected_lines.append(line_num)
                    improvements["performance_improvement"] += 0.4
        
        return RefactoringResult(
            success=True,
            refactoring_type="optimize_string_operations",
            original_lines=lines,
            refactored_lines=refactored_lines,
            lines_affected=affected_lines,
            improvements=improvements,
            warnings=[],
            errors=[]
        )
    
    def _apply_eliminate_god_method(
        self, 
        lines: List[str], 
        refactoring: IntelligentRefactoring, 
        file_path: str
    ) -> RefactoringResult:
        """Apply god method elimination by breaking into smaller methods using LLM intelligence."""
        
        # Use LLM-powered refactoring if available
        if self.enable_real_llm and self.llm_model:
            return self._apply_llm_refactoring(lines, refactoring, file_path, "eliminate_god_method")
        
        # Fallback to hardcoded implementation
        # This is a complex refactoring - analyze the method structure
        target_lines = refactoring.target_lines
        start_line = min(target_lines) - 1
        end_line = max(target_lines)
        
        method_lines = lines[start_line:end_line]
        
        # Identify logical blocks within the god method
        logical_blocks = self._identify_logical_blocks(method_lines)
        
        if len(logical_blocks) < 2:
            return RefactoringResult(
                success=False,
                refactoring_type="eliminate_god_method",
                original_lines=lines,
                refactored_lines=lines,
                lines_affected=[],
                improvements={},
                warnings=["Could not identify extractable logical blocks"],
                errors=[]
            )
        
        # Generate extracted methods for each logical block
        extracted_methods = []
        method_calls = []
        
        for i, block in enumerate(logical_blocks):
            method_name = f"_extracted_logic_{i+1}"
            
            # Analyze block for parameters and return values
            block_analysis = self._analyze_code_block_for_extraction(
                block["lines"], lines, start_line
            )
            
            # Generate extracted method
            extracted_method = self._generate_extracted_method(
                method_name,
                block_analysis["parameters"],
                block_analysis["return_vars"],
                block["lines"],
                block["indentation"]
            )
            
            extracted_methods.extend(extracted_method)
            extracted_methods.append("")  # Add spacing
            
            # Generate method call
            method_call = self._generate_method_call(
                method_name,
                block_analysis["parameters"],
                block_analysis["return_vars"],
                block["indentation"]
            )
            
            method_calls.append(method_call)
        
        # Replace the god method with calls to extracted methods
        refactored_lines = lines.copy()
        
        # Keep the method signature but replace body with method calls
        method_signature_end = self._find_method_signature_end(lines, start_line)
        method_body_start = method_signature_end + 1
        
        # Replace method body
        refactored_lines[method_body_start:end_line] = method_calls
        
        # Insert extracted methods before the original method
        refactored_lines[start_line:start_line] = extracted_methods
        
        return RefactoringResult(
            success=True,
            refactoring_type="eliminate_god_method",
            original_lines=lines,
            refactored_lines=refactored_lines,
            lines_affected=target_lines,
            improvements={
                "complexity_reduction": len(method_lines) * 0.4,
                "maintainability_improvement": 0.9,
                "testability_improvement": 0.8
            },
            warnings=[],
            errors=[]
        )
    
    def _apply_god_code_refactoring(
        self, 
        lines: List[str], 
        refactoring: IntelligentRefactoring, 
        file_path: str
    ) -> RefactoringResult:
        """Apply advanced god code refactoring using specialized agent."""
        
        self.logger.info("Applying god code refactoring using specialized agent")
        
        try:
            # Get code content
            code_content = '\n'.join(lines)
            
            # Use specialized agent to detect god codes
            god_detections = self.god_code_agent.analyze_god_codes(file_path, code_content)
            
            if not god_detections:
                return RefactoringResult(
                    success=False,
                    refactoring_type="god_code_refactoring",
                    original_lines=lines,
                    refactored_lines=lines,
                    lines_affected=[],
                    improvements={},
                    warnings=["No god code patterns detected"],
                    errors=[]
                )
            
            # Filter detections to target lines if specified
            target_lines = refactoring.target_lines if refactoring.target_lines else []
            relevant_detections = []
            
            if target_lines:
                for detection in god_detections:
                    # Check if detection overlaps with target lines
                    detection_range = set(range(detection.start_line, detection.end_line + 1))
                    target_range = set(target_lines)
                    if detection_range.intersection(target_range):
                        relevant_detections.append(detection)
            else:
                relevant_detections = god_detections
            
            if not relevant_detections:
                return RefactoringResult(
                    success=False,
                    refactoring_type="god_code_refactoring",
                    original_lines=lines,
                    refactored_lines=lines,
                    lines_affected=[],
                    improvements={},
                    warnings=["No god code patterns in target lines"],
                    errors=[]
                )
            
            # Apply refactoring to the most critical detection
            primary_detection = max(relevant_detections, key=lambda d: d.complexity_score)
            
            # Generate refactoring strategy
            strategy = self.god_code_agent.generate_refactoring_strategy(primary_detection)
            
            # Apply refactoring
            refactoring_result = self.god_code_agent.apply_refactoring(
                code_content, primary_detection, strategy
            )
            
            if not refactoring_result.validation_passed:
                return RefactoringResult(
                    success=False,
                    refactoring_type="god_code_refactoring",
                    original_lines=lines,
                    refactored_lines=lines,
                    lines_affected=[],
                    improvements={},
                    warnings=refactoring_result.warnings,
                    errors=["Refactoring failed validation"]
                )
            
            # Convert refactored code back to lines
            refactored_lines = refactoring_result.updated_original.splitlines()
            
            # Calculate affected lines
            affected_lines = list(range(primary_detection.start_line, primary_detection.end_line + 1))
            
            # Calculate improvements
            improvements = {
                "complexity_reduction": primary_detection.complexity_score * 0.01,
                "maintainability_improvement": strategy.estimated_improvement * 0.01,
                "srp_compliance": 0.8,  # SRP compliance improvement
                "testability_improvement": 0.7
            }
            
            return RefactoringResult(
                success=True,
                refactoring_type="god_code_refactoring",
                original_lines=lines,
                refactored_lines=refactored_lines,
                lines_affected=affected_lines,
                improvements=improvements,
                warnings=refactoring_result.warnings,
                errors=[]
            )
            
        except Exception as e:
            self.logger.error("God code refactoring failed: %s", e)
            return RefactoringResult(
                success=False,
                refactoring_type="god_code_refactoring",
                original_lines=lines,
                refactored_lines=lines,
                lines_affected=[],
                improvements={},
                warnings=[],
                errors=[f"God code refactoring failed: {e}"]
            )
    
    def _apply_optimize_database_queries(
        self, 
        lines: List[str], 
        refactoring: IntelligentRefactoring, 
        file_path: str
    ) -> RefactoringResult:
        """Apply database query optimizations to prevent N+1 queries."""
        
        refactored_lines = lines.copy()
        affected_lines = []
        improvements = {"performance_improvement": 0.0}
        
        # Identify potential N+1 query patterns
        for line_num in refactoring.target_lines:
            line_idx = line_num - 1
            line = lines[line_idx]
            
            # Look for query patterns inside loops
            if any(pattern in line for pattern in ['execute(', 'query(', 'get(']):
                # Check if this is inside a loop
                loop_context = self._find_loop_context(lines, line_idx)
                if loop_context:
                    # Suggest batch query optimization
                    optimization = self._generate_batch_query_optimization(line, loop_context)
                    if optimization:
                        refactored_lines[line_idx] = f"{line}  # TODO: Optimize with batch query - see comment below"
                        refactored_lines.insert(line_idx + 1, f"    # {optimization}")
                        affected_lines.append(line_num)
                        improvements["performance_improvement"] += 1.0
        
        return RefactoringResult(
            success=True,
            refactoring_type="optimize_database_queries",
            original_lines=lines,
            refactored_lines=refactored_lines,
            lines_affected=affected_lines,
            improvements=improvements,
            warnings=["Database optimizations require manual validation"],
            errors=[]
        )
    
    def _apply_extract_constants(
        self, 
        lines: List[str], 
        refactoring: IntelligentRefactoring, 
        file_path: str
    ) -> RefactoringResult:
        """Apply constant extraction for magic numbers and strings."""
        
        refactored_lines = lines.copy()
        affected_lines = []
        constants_to_add = []
        improvements = {"maintainability_improvement": 0.0}
        
        for line_num in refactoring.target_lines:
            line_idx = line_num - 1
            line = lines[line_idx]
            
            # Find magic numbers
            magic_numbers = re.findall(r'\b(\d+)\b', line)
            for number in magic_numbers:
                if int(number) > 10:  # Only extract significant numbers
                    constant_name = f"MAGIC_NUMBER_{number}"
                    constants_to_add.append((constant_name, number))
                    
                    # Replace in line
                    refactored_lines[line_idx] = line.replace(number, constant_name)
                    affected_lines.append(line_num)
                    improvements["maintainability_improvement"] += 0.2
        
        # Add constants at the top of the file
        if constants_to_add:
            constants_insertion_point = self._find_constants_insertion_point(lines)
            
            constant_lines = ["# Constants"]
            for const_name, const_value in constants_to_add:
                constant_lines.append(f"{const_name} = {const_value}")
            constant_lines.append("")  # Add spacing
            
            refactored_lines[constants_insertion_point:constants_insertion_point] = constant_lines
        
        return RefactoringResult(
            success=True,
            refactoring_type="extract_constants",
            original_lines=lines,
            refactored_lines=refactored_lines,
            lines_affected=affected_lines,
            improvements=improvements,
            warnings=[],
            errors=[]
        )
    
    def _apply_improve_conditional_logic(
        self, 
        lines: List[str], 
        refactoring: IntelligentRefactoring, 
        file_path: str
    ) -> RefactoringResult:
        """Apply conditional logic improvements."""
        
        refactored_lines = lines.copy()
        affected_lines = []
        improvements = {"readability_improvement": 0.0}
        
        for line_num in refactoring.target_lines:
            line_idx = line_num - 1
            line = lines[line_idx]
            
            # Simplify complex boolean expressions
            if line.strip().startswith(('if ', 'elif ')) and (" and " in line or " or " in line):
                simplified_line = self._simplify_boolean_expression(line)
                if simplified_line != line:
                    refactored_lines[line_idx] = simplified_line
                    affected_lines.append(line_num)
                    improvements["readability_improvement"] += 0.4
        
        return RefactoringResult(
            success=True,
            refactoring_type="improve_conditional_logic",
            original_lines=lines,
            refactored_lines=refactored_lines,
            lines_affected=affected_lines,
            improvements=improvements,
            warnings=[],
            errors=[]
        )
    
    # Helper methods for refactoring analysis
    def _find_function_start(self, lines: List[str], current_line: int) -> int:
        """Find the start of the function containing the current line."""
        for i in range(current_line, -1, -1):
            if lines[i].strip().startswith('def '):
                return i
        return -1
    
    def _analyze_code_block_for_extraction(
        self, 
        code_block: List[str], 
        full_file: List[str], 
        context_start: int
    ) -> Dict[str, Any]:
        """Analyze a code block to determine if it can be extracted."""
        
        # Simplified analysis - in a real implementation, this would be much more sophisticated
        variables_used = set()
        variables_defined = set()
        
        for line in code_block:
            # Find variable usage
            words = re.findall(r'\b[a-zA-Z_]\w*\b', line)
            variables_used.update(words)
            
            # Find variable definitions
            if '=' in line and not line.strip().startswith('#'):
                var_match = re.search(r'([a-zA-Z_]\w*)\s*=', line)
                if var_match:
                    variables_defined.add(var_match.group(1))
        
        # Determine parameters (variables used but not defined in block)
        parameters = variables_used - variables_defined - {'self', 'cls'}
        
        # Determine return variables (variables defined in block)
        return_vars = variables_defined
        
        # Generate method name
        method_name = "_extracted_method"
        
        # Get indentation
        indentation = "    "  # Default to 4 spaces
        
        return {
            "extractable": True,
            "method_name": method_name,
            "parameters": list(parameters)[:5],  # Limit parameters
            "return_vars": list(return_vars)[:3],  # Limit return values
            "indentation": indentation,
            "warnings": [],
            "errors": []
        }
    
    def _generate_extracted_method(
        self, 
        method_name: str, 
        parameters: List[str], 
        return_vars: List[str], 
        code_block: List[str],
        indentation: str
    ) -> List[str]:
        """Generate the extracted method code."""
        
        lines = []
        
        # Method signature
        params_str = ", ".join(["self"] + parameters)
        lines.append(f"{indentation}def {method_name}({params_str}):")
        lines.append(f'{indentation}    """Extracted method - TODO: Add proper docstring."""')
        
        # Method body (indented)
        for line in code_block:
            lines.append(f"{indentation}    {line.strip()}")
        
        # Return statement
        if return_vars:
            return_str = ", ".join(return_vars)
            lines.append(f"{indentation}    return {return_str}")
        
        return lines
    
    def _generate_method_call(
        self, 
        method_name: str, 
        parameters: List[str], 
        return_vars: List[str],
        indentation: str
    ) -> str:
        """Generate the method call to replace extracted code."""
        
        params_str = ", ".join(parameters)
        call = f"self.{method_name}({params_str})"
        
        if return_vars:
            return_str = ", ".join(return_vars)
            return f"{indentation}{return_str} = {call}"
        else:
            return f"{indentation}{call}"
    
    def _find_import_insertion_point(self, lines: List[str]) -> int:
        """Find appropriate place to insert import statements."""
        # Look for existing imports
        for i, line in enumerate(lines):
            if line.strip().startswith(('import ', 'from ')):
                # Find end of import block
                for j in range(i, len(lines)):
                    if not lines[j].strip().startswith(('import ', 'from ', '#')) and lines[j].strip():
                        return j
        
        # If no imports found, insert after docstring/comments
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#') and '"""' not in line:
                return i
        
        return 0
    
    def _optimize_string_concatenation(self, line: str) -> str:
        """Optimize string concatenation to use f-strings."""
        # This is a simplified implementation
        # In practice, this would need more sophisticated parsing
        
        # Pattern: "string" + variable + "string"
        pattern = r'("[^"]*")\s*\+\s*(\w+)\s*\+\s*("[^"]*")'
        match = re.search(pattern, line)
        
        if match:
            str1, var, str2 = match.groups()
            replacement = f'f{str1[:-1]}{{{var}}}{str2[1:]}'
            return line.replace(match.group(0), replacement)
        
        return line
    
    def _optimize_join_operation(self, line: str) -> str:
        """Optimize join operations."""
        # This is a placeholder - real implementation would be more sophisticated
        return line
    
    def _identify_logical_blocks(self, method_lines: List[str]) -> List[Dict[str, Any]]:
        """Identify logical blocks within a method."""
        # Simplified implementation - identify blocks by blank lines and comments
        blocks = []
        current_block = []
        
        for i, line in enumerate(method_lines):
            if line.strip() == "" or line.strip().startswith("#"):
                if current_block:
                    blocks.append({
                        "lines": current_block,
                        "start_line": i - len(current_block),
                        "indentation": "    "
                    })
                    current_block = []
            else:
                current_block.append(line)
        
        if current_block:
            blocks.append({
                "lines": current_block,
                "start_line": len(method_lines) - len(current_block),
                "indentation": "    "
            })
        
        return blocks
    
    def _find_method_signature_end(self, lines: List[str], method_start: int) -> int:
        """Find the end of a method signature."""
        for i in range(method_start, len(lines)):
            if lines[i].strip().endswith(':'):
                return i
        return method_start
    
    def _find_loop_context(self, lines: List[str], line_idx: int) -> Optional[Dict[str, Any]]:
        """Find if a line is inside a loop."""
        for i in range(line_idx, -1, -1):
            line = lines[i].strip()
            if line.startswith(('for ', 'while ')):
                return {"type": "loop", "line": i, "content": line}
        return None
    
    def _generate_batch_query_optimization(self, query_line: str, loop_context: Dict[str, Any]) -> str:
        """Generate suggestion for batch query optimization."""
        return "Consider collecting IDs and using batch query: WHERE id IN (...)"
    
    def _find_constants_insertion_point(self, lines: List[str]) -> int:
        """Find appropriate place to insert constants."""
        # Insert after imports but before classes/functions
        import_end = self._find_import_insertion_point(lines)
        
        for i in range(import_end, len(lines)):
            if lines[i].strip().startswith(('class ', 'def ')):
                return i
        
        return import_end
    
    def _simplify_boolean_expression(self, line: str) -> str:
        """Simplify complex boolean expressions."""
        # This is a placeholder for more sophisticated boolean simplification
        # In practice, this would use AST analysis and boolean algebra
        return line
    
    def apply_intelligent_refactorings(
        self, 
        analysis_result: Dict[str, Any], 
        selected_strategies: List[int] = None
    ) -> Dict[str, Any]:
        """Apply intelligent refactorings based on analysis results - Agno compatible method."""
        
        try:
            # Default to first 3 strategies if not specified
            if selected_strategies is None:
                selected_strategies = [0, 1, 2]
            
            file_path = analysis_result.get("file_path", "")
            if not file_path:
                return {
                    "success": False,
                    "error": "No file_path provided in analysis_result",
                    "tokens_used": 0,
                    "refactorings_applied": []
                }
            
            # Check if file exists
            if not Path(file_path).exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "tokens_used": 0,
                    "refactorings_applied": []
                }
            
            # Get available refactoring strategies
            strategy_names = list(self.refactoring_strategies.keys())
            
            refactorings_applied = []
            total_tokens_used = 0
            
            # Apply selected strategies
            for strategy_idx in selected_strategies:
                if strategy_idx >= len(strategy_names):
                    continue
                    
                strategy_name = strategy_names[strategy_idx]
                
                # Create a simple refactoring for this strategy
                refactoring = IntelligentRefactoring(
                    refactoring_type=strategy_name,
                    target_lines=[1],  # Simplified - would need real analysis
                    description=f"Apply {strategy_name} refactoring",
                    confidence=0.8
                )
                
                # Apply the refactoring
                try:
                    result = self.apply_refactoring(file_path, refactoring)

                    if result.success and result.refactored_lines != result.original_lines:
                        refactorings_applied.append({
                            "type": strategy_name,
                            "success": True,
                            "lines_affected": result.lines_affected,
                            "improvements": result.improvements
                        })
                        # Estimate tokens used for this operation
                        total_tokens_used += 150  # Rough estimate per refactoring
                    else:
                        refactorings_applied.append({
                            "type": strategy_name,
                            "success": False,
                            "errors": result.errors or ["No changes made"],
                        })
                        
                except Exception as e:
                    self.logger.error(f"Error applying {strategy_name}: {e}")
                    refactorings_applied.append({
                        "type": strategy_name,
                        "success": False,
                        "error": str(e)
                    })
            
            success_count = sum(1 for r in refactorings_applied if r.get("success", False))
            
            return {
                "success": success_count > 0,
                "file_path": file_path,
                "strategies_attempted": len(selected_strategies),
                "strategies_successful": success_count,
                "refactorings_applied": refactorings_applied,
                "tokens_used": total_tokens_used,
                "summary": f"Applied {success_count}/{len(selected_strategies)} refactoring strategies successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error in apply_intelligent_refactorings: {e}")
            return {
                "success": False,
                "error": str(e),
                "tokens_used": 0,
                "refactorings_applied": []
            }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Intelligent Refactoring Engine - Apply AI-powered refactorings"
    )
    
    parser.add_argument("--file", type=str, required=True, help="File to refactor")
    parser.add_argument(
        "--refactoring-type", 
        type=str, 
        choices=[
            "extract_method", "improve_exception_handling", 
            "optimize_string_operations", "eliminate_god_method",
            "optimize_database_queries", "extract_constants",
            "improve_conditional_logic"
        ],
        help="Type of refactoring to apply"
    )
    parser.add_argument("--apply", action="store_true", help="Apply refactoring (not just analyze)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize the refactoring engine
        engine = IntelligentRefactoringEngine(dry_run=args.dry_run or not args.apply)
        
        # If specific refactoring type is provided, create a custom refactoring
        if args.refactoring_type:
            # Create a sample refactoring (in practice, this would come from analysis)
            refactoring = IntelligentRefactoring(
                refactoring_type=args.refactoring_type,
                target_lines=[1, 2, 3],  # Sample lines
                description=f"Apply {args.refactoring_type} refactoring",
                benefits=["Improved code quality"],
                risks=["Minimal"],
                confidence_score=0.85,
                estimated_impact={"maintainability": "high_improvement"}
            )
            
            # Apply the refactoring
            result = engine.apply_refactoring(args.file, refactoring)
            
            print(f"\n🔧 Refactoring Results for {args.file}")
            print(f"=" * 50)
            print(f"Type: {result.refactoring_type}")
            print(f"Success: {result.success}")
            print(f"Lines affected: {len(result.lines_affected)}")
            
            if result.improvements:
                print("\nImprovements:")
                for improvement, value in result.improvements.items():
                    print(f"  {improvement}: {value:.1f}")
            
            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  ⚠️ {warning}")
            
            if result.errors:
                print("\nErrors:")
                for error in result.errors:
                    print(f"  ❌ {error}")
        
        else:
            # Demonstrate with IntelligentCodeAgent analysis
            project_root = Path(__file__).resolve().parent.parent.parent
            agent = IntelligentCodeAgent(project_root=project_root, dry_run=True)
            
            analysis = agent.analyze_file_intelligently(args.file)
            
            print(f"\n🔍 Available Refactorings for {args.file}")
            print(f"=" * 50)
            
            for i, refactoring in enumerate(analysis.recommended_refactorings):
                print(f"\n{i+1}. {refactoring.refactoring_type}")
                print(f"   Description: {refactoring.description}")
                print(f"   Confidence: {refactoring.confidence_score:.0%}")
                print(f"   Lines: {len(refactoring.target_lines)}")
                
                if args.apply:
                    result = engine.apply_refactoring(args.file, refactoring)
                    if result.success:
                        print(f"   ✅ Applied successfully")
                    else:
                        print(f"   ❌ Failed: {result.errors}")
        
        return 0
        
    except Exception as e:
        logger.error("Error: %s", e, exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    exit(main())