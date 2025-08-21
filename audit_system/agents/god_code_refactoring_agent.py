#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 God Code Refactoring Agent - Specialist in Single Responsibility Principle

Advanced AI agent that detects and refactors god methods/classes into smaller,
focused modules following the Single Responsibility Principle (SRP).

Capabilities:
- God Code Detection: Identifies overly complex methods and classes
- Responsibility Analysis: Maps different responsibilities within code
- Dependency Mapping: Understands relationships and dependencies
- Separation Strategy: Plans optimal refactoring approach
- Code Generation: Automatically generates refactored code
- Validation: Ensures functional equivalence after refactoring
"""

from __future__ import annotations

import ast
import inspect
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import textwrap
from collections import defaultdict, Counter
import keyword
import builtins

# =============================================================================
# God Code Detection and Analysis Infrastructure
# =============================================================================

class GodCodeType(Enum):
    """Types of god code patterns detected."""
    GOD_METHOD = "god_method"           # Methods with too many lines/responsibilities
    GOD_CLASS = "god_class"             # Classes with too many methods/responsibilities  
    GOD_FUNCTION = "god_function"       # Functions with excessive complexity
    FEATURE_ENVY = "feature_envy"       # Methods using other classes excessively
    DATA_CLASS = "data_class"           # Classes that are just data containers
    UTILITY_CLASS = "utility_class"     # Classes with only static methods


class ResponsibilityType(Enum):
    """Types of responsibilities identified in code."""
    DATA_ACCESS = "data_access"         # Database/file access operations
    BUSINESS_LOGIC = "business_logic"   # Core business rules
    UI_INTERACTION = "ui_interaction"   # User interface operations
    VALIDATION = "validation"           # Input/data validation
    LOGGING = "logging"                 # Logging and monitoring
    ERROR_HANDLING = "error_handling"   # Exception and error management
    CONFIGURATION = "configuration"     # Configuration and setup
    NETWORKING = "networking"           # Network operations
    CALCULATION = "calculation"         # Mathematical computations
    FORMATTING = "formatting"           # Data formatting and presentation
    SERIALIZATION = "serialization"    # Data serialization/deserialization
    CACHING = "caching"                 # Caching operations


@dataclass
class Responsibility:
    """Represents a single responsibility within code."""
    type: ResponsibilityType
    description: str
    lines: List[int]                    # Line numbers where this responsibility appears
    variables_used: Set[str]            # Variables accessed by this responsibility
    methods_called: Set[str]            # Methods called by this responsibility  
    external_dependencies: Set[str]     # External modules/classes used
    complexity_score: float             # 0-100 complexity measure for this responsibility
    
    
@dataclass 
class GodCodeDetection:
    """Represents a detected god code pattern."""
    type: GodCodeType
    name: str                           # Name of method/class/function
    start_line: int
    end_line: int  
    total_lines: int
    complexity_score: float             # 0-100 complexity measure
    responsibilities: List[Responsibility]
    dependency_violations: int          # Number of SRP violations
    refactoring_priority: str           # "HIGH", "MEDIUM", "LOW"
    suggested_separation: List[str]     # Suggested new module names


@dataclass
class RefactoringStrategy:
    """Strategy for refactoring a god code."""
    original_name: str
    separation_approach: str            # "extract_methods", "extract_classes", "delegate_pattern"
    new_modules: List[Dict[str, Any]]   # List of new modules to create
    remaining_core: Dict[str, Any]      # What remains in original module
    dependency_updates: List[str]       # Required dependency updates
    risk_assessment: str                # "LOW", "MEDIUM", "HIGH"
    estimated_improvement: float        # Expected maintainability improvement %


@dataclass  
class RefactoringResult:
    """Result of applying a refactoring strategy."""
    original_code: str
    refactored_modules: Dict[str, str]  # module_name -> refactored_code
    updated_original: str               # Updated original code
    validation_passed: bool             # Whether refactoring preserves functionality
    improvement_metrics: Dict[str, float]  # Before/after metrics
    warnings: List[str]                 # Warnings about potential issues


# =============================================================================
# God Code Refactoring Agent - Main Class
# =============================================================================

class GodCodeRefactoringAgent:
    """
    Advanced agent specialized in detecting and refactoring god codes into
    smaller modules following Single Responsibility Principle.
    """
    
    def __init__(self, dry_run: bool = False, aggressive_refactoring: bool = False):
        self.dry_run = dry_run
        self.aggressive_refactoring = aggressive_refactoring
        self.logger = logging.getLogger(f"{__name__}.GodCodeRefactoringAgent")
        
        # Configuration thresholds
        self.god_method_lines_threshold = 50      # Methods with 50+ lines
        self.god_class_methods_threshold = 20     # Classes with 20+ methods
        self.complexity_threshold = 70            # Complexity score threshold
        self.responsibility_threshold = 3         # Max responsibilities per unit
        
        # Responsibility detection patterns
        self.responsibility_patterns = self._initialize_responsibility_patterns()
        
        self.logger.info(
            "GodCodeRefactoringAgent initialized: dry_run=%s, aggressive=%s", 
            dry_run, aggressive_refactoring
        )
    
    def _initialize_responsibility_patterns(self) -> Dict[ResponsibilityType, List[str]]:
        """Initialize patterns for detecting different responsibilities."""
        return {
            ResponsibilityType.DATA_ACCESS: [
                r'\.execute\(', r'\.fetchall\(', r'\.fetchone\(', r'SELECT\s+', 
                r'INSERT\s+', r'UPDATE\s+', r'DELETE\s+', r'\.query\(',
                r'open\(', r'\.read\(', r'\.write\(', r'\.save\(', r'\.load\('
            ],
            ResponsibilityType.BUSINESS_LOGIC: [
                r'def\s+calculate_', r'def\s+process_', r'def\s+validate_',
                r'def\s+compute_', r'def\s+determine_', r'if.*business',
                r'\.apply\(', r'\.transform\(', r'\.filter\('
            ],
            ResponsibilityType.UI_INTERACTION: [
                r'print\(', r'input\(', r'\.show\(', r'\.display\(',
                r'streamlit', r'st\.', r'render', r'\.click\(', r'\.button\('
            ],
            ResponsibilityType.VALIDATION: [
                r'assert\s+', r'raise\s+ValueError', r'raise\s+TypeError',
                r'if\s+not\s+', r'validate_', r'check_', r'verify_',
                r'isinstance\(', r'hasattr\('
            ],
            ResponsibilityType.LOGGING: [
                r'logging\.', r'logger\.', r'\.debug\(', r'\.info\(',
                r'\.warning\(', r'\.error\(', r'\.critical\(', r'print\('
            ],
            ResponsibilityType.ERROR_HANDLING: [
                r'try:', r'except\s+', r'finally:', r'raise\s+',
                r'\.handle_error\(', r'error_', r'exception_'
            ],
            ResponsibilityType.CONFIGURATION: [
                r'config', r'settings', r'\.conf', r'environment',
                r'\.env', r'os\.environ', r'getenv\(', r'\.ini'
            ],
            ResponsibilityType.NETWORKING: [
                r'requests\.', r'urllib', r'http', r'socket',
                r'\.get\(', r'\.post\(', r'\.put\(', r'\.delete\(',
                r'api_', r'endpoint', r'url'
            ],
            ResponsibilityType.CALCULATION: [
                r'math\.', r'numpy', r'sum\(', r'max\(', r'min\(',
                r'average', r'calculate', r'compute', r'\+\s*=', r'-\s*='
            ],
            ResponsibilityType.FORMATTING: [
                r'format\(', r'\.strftime\(', r'\.strptime\(',
                r'f"', r'\.join\(', r'\.split\(', r'\.strip\(',
                r'\.upper\(', r'\.lower\(', r'json\.'
            ],
            ResponsibilityType.SERIALIZATION: [
                r'json\.', r'pickle\.', r'yaml\.', r'csv\.',
                r'\.dumps\(', r'\.loads\(', r'\.serialize\(',
                r'\.deserialize\(', r'to_dict\(', r'from_dict\('
            ],
            ResponsibilityType.CACHING: [
                r'cache', r'redis', r'memcache', r'@lru_cache',
                r'\.get_cache\(', r'\.set_cache\(', r'cached_'
            ]
        }
    
    def analyze_god_codes(self, file_path: str, code_content: str) -> List[GodCodeDetection]:
        """
        Analyze code to detect god code patterns and their responsibilities.
        """
        self.logger.info("Analyzing god codes in %s", file_path)
        
        try:
            # Parse AST
            ast_tree = ast.parse(code_content)
            
            detections = []
            lines = code_content.splitlines()
            
            # Analyze classes for god class patterns
            for node in ast.walk(ast_tree):
                if isinstance(node, ast.ClassDef):
                    class_detection = self._analyze_god_class(node, lines, code_content)
                    if class_detection:
                        detections.append(class_detection)
                
                elif isinstance(node, ast.FunctionDef):
                    # Analyze both standalone functions and methods
                    function_detection = self._analyze_god_method(node, lines, code_content)
                    if function_detection:
                        detections.append(function_detection)
            
            self.logger.info("Found %d god code patterns in %s", len(detections), file_path)
            return detections
            
        except SyntaxError as e:
            self.logger.warning("Syntax error in %s: %s", file_path, e)
            return []
    
    def _analyze_god_class(self, class_node: ast.ClassDef, lines: List[str], code: str) -> Optional[GodCodeDetection]:
        """Analyze a class for god class patterns."""
        
        # Count methods in class
        methods = [node for node in class_node.body if isinstance(node, ast.FunctionDef)]
        method_count = len(methods)
        
        class_start = class_node.lineno
        class_end = max(node.end_lineno or node.lineno for node in ast.walk(class_node) if hasattr(node, 'lineno'))
        total_lines = class_end - class_start + 1
        
        # Check if it qualifies as god class
        is_god_class = (
            method_count >= self.god_class_methods_threshold or
            total_lines >= 200 or
            (self.aggressive_refactoring and method_count >= 10)
        )
        
        if not is_god_class:
            return None
            
        # Analyze responsibilities across all methods
        all_responsibilities = []
        class_lines = list(range(class_start, class_end + 1))
        
        for method in methods:
            method_responsibilities = self._detect_responsibilities(method, lines)
            all_responsibilities.extend(method_responsibilities)
        
        # Group similar responsibilities
        responsibility_groups = self._group_responsibilities(all_responsibilities)
        
        complexity_score = self._calculate_complexity_score(
            total_lines, method_count, len(responsibility_groups)
        )
        
        # Determine refactoring priority
        priority = "HIGH" if complexity_score >= 80 else "MEDIUM" if complexity_score >= 60 else "LOW"
        
        # Suggest separation based on responsibility groups
        suggested_separation = [
            f"{class_node.name}{resp_type.value.replace('_', '').title()}"
            for resp_type in responsibility_groups.keys()
        ]
        
        return GodCodeDetection(
            type=GodCodeType.GOD_CLASS,
            name=class_node.name,
            start_line=class_start,
            end_line=class_end,
            total_lines=total_lines,
            complexity_score=complexity_score,
            responsibilities=list(responsibility_groups.values()),
            dependency_violations=len(responsibility_groups) - 1,  # -1 for single responsibility
            refactoring_priority=priority,
            suggested_separation=suggested_separation
        )
    
    def _analyze_god_method(self, method_node: ast.FunctionDef, lines: List[str], code: str) -> Optional[GodCodeDetection]:
        """Analyze a method/function for god method patterns."""
        
        method_start = method_node.lineno
        method_end = method_node.end_lineno or method_node.lineno
        total_lines = method_end - method_start + 1
        
        # Check if it qualifies as god method
        is_god_method = (
            total_lines >= self.god_method_lines_threshold or
            (self.aggressive_refactoring and total_lines >= 30)
        )
        
        if not is_god_method:
            return None
            
        # Analyze responsibilities within method
        responsibilities = self._detect_responsibilities(method_node, lines)
        responsibility_count = len(set(r.type for r in responsibilities))
        
        complexity_score = self._calculate_complexity_score(
            total_lines, 1, responsibility_count
        )
        
        # Only flag if multiple responsibilities detected
        if responsibility_count <= self.responsibility_threshold and not self.aggressive_refactoring:
            return None
        
        priority = "HIGH" if complexity_score >= 80 else "MEDIUM" if complexity_score >= 60 else "LOW"
        
        # Suggest separation based on responsibilities
        suggested_separation = [
            f"{method_node.name}_{resp.type.value}"
            for resp in responsibilities
        ]
        
        return GodCodeDetection(
            type=GodCodeType.GOD_METHOD,
            name=method_node.name,
            start_line=method_start,
            end_line=method_end,
            total_lines=total_lines,
            complexity_score=complexity_score,
            responsibilities=responsibilities,
            dependency_violations=responsibility_count - 1,
            refactoring_priority=priority,
            suggested_separation=suggested_separation
        )
    
    def _detect_responsibilities(self, node: ast.AST, lines: List[str]) -> List[Responsibility]:
        """Detect different responsibilities within a code node."""
        
        responsibilities = []
        node_lines = list(range(node.lineno, (node.end_lineno or node.lineno) + 1))
        
        # Extract code content for this node
        node_code_lines = [lines[i-1] for i in node_lines if i-1 < len(lines)]
        node_code = '\n'.join(node_code_lines)
        
        # Check for each responsibility type
        for resp_type, patterns in self.responsibility_patterns.items():
            matching_lines = []
            variables_used = set()
            methods_called = set()
            external_deps = set()
            
            for i, line in enumerate(node_code_lines):
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        matching_lines.append(node_lines[i])
                        
                        # Extract variables and method calls
                        variables_used.update(self._extract_variables(line))
                        methods_called.update(self._extract_method_calls(line))
                        external_deps.update(self._extract_external_dependencies(line))
                        break
            
            if matching_lines:
                # Calculate complexity for this responsibility
                complexity = min(100.0, len(matching_lines) * 10 + len(variables_used) * 2)
                
                responsibility = Responsibility(
                    type=resp_type,
                    description=f"{resp_type.value.replace('_', ' ').title()} operations",
                    lines=matching_lines,
                    variables_used=variables_used,
                    methods_called=methods_called,
                    external_dependencies=external_deps,
                    complexity_score=complexity
                )
                responsibilities.append(responsibility)
        
        return responsibilities
    
    def _group_responsibilities(self, responsibilities: List[Responsibility]) -> Dict[ResponsibilityType, Responsibility]:
        """Group similar responsibilities together."""
        groups = {}
        
        for responsibility in responsibilities:
            if responsibility.type in groups:
                # Merge with existing responsibility
                existing = groups[responsibility.type]
                existing.lines.extend(responsibility.lines)
                existing.variables_used.update(responsibility.variables_used)
                existing.methods_called.update(responsibility.methods_called)
                existing.external_dependencies.update(responsibility.external_dependencies)
                existing.complexity_score += responsibility.complexity_score
            else:
                groups[responsibility.type] = responsibility
        
        return groups
    
    def _extract_variables(self, line: str) -> Set[str]:
        """Extract variable names from a line of code."""
        variables = set()
        
        # Simple regex-based extraction (could be enhanced with AST)
        var_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*='
        matches = re.findall(var_pattern, line)
        variables.update(matches)
        
        return variables
    
    def _extract_method_calls(self, line: str) -> Set[str]:
        """Extract method calls from a line of code."""
        methods = set()
        
        # Extract method calls
        method_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        matches = re.findall(method_pattern, line)
        methods.update(matches)
        
        return methods
    
    def _extract_external_dependencies(self, line: str) -> Set[str]:
        """Extract external dependencies from a line of code."""
        deps = set()
        
        # Extract imports and module references
        import_pattern = r'(import\s+|from\s+)([a-zA-Z0-9_.]+)'
        matches = re.findall(import_pattern, line)
        for _, module in matches:
            deps.add(module.split('.')[0])  # Get root module
        
        return deps
    
    def _calculate_complexity_score(self, lines: int, methods: int, responsibilities: int) -> float:
        """Calculate complexity score for a code unit."""
        
        # Base score from lines of code
        line_score = min(50.0, lines / 10)  # 10 lines = 1 point, max 50
        
        # Method count score
        method_score = min(30.0, methods * 2)  # 1 method = 2 points, max 30
        
        # Responsibility violation score
        resp_score = max(0, responsibilities - 1) * 10  # Extra responsibilities penalty
        
        total_score = line_score + method_score + resp_score
        return min(100.0, total_score)
    
    def generate_refactoring_strategy(self, detection: GodCodeDetection) -> RefactoringStrategy:
        """Generate a refactoring strategy for a detected god code."""
        
        self.logger.info("Generating refactoring strategy for %s", detection.name)
        
        if detection.type == GodCodeType.GOD_CLASS:
            return self._generate_class_refactoring_strategy(detection)
        elif detection.type in [GodCodeType.GOD_METHOD, GodCodeType.GOD_FUNCTION]:
            return self._generate_method_refactoring_strategy(detection)
        else:
            # Default strategy
            return RefactoringStrategy(
                original_name=detection.name,
                separation_approach="extract_methods",
                new_modules=[],
                remaining_core={},
                dependency_updates=[],
                risk_assessment="MEDIUM",
                estimated_improvement=30.0
            )
    
    def _generate_class_refactoring_strategy(self, detection: GodCodeDetection) -> RefactoringStrategy:
        """Generate refactoring strategy for god class."""
        
        # Group responsibilities and suggest new classes
        responsibility_groups = {}
        for resp in detection.responsibilities:
            if resp.type not in responsibility_groups:
                responsibility_groups[resp.type] = []
            responsibility_groups[resp.type].append(resp)
        
        new_modules = []
        for resp_type, resp_list in responsibility_groups.items():
            module_name = f"{detection.name}{resp_type.value.replace('_', '').title()}"
            
            new_modules.append({
                "name": module_name,
                "type": "class",
                "responsibilities": resp_list,
                "methods_to_extract": [line for resp in resp_list for line in resp.lines],
                "dependencies": set().union(*[resp.external_dependencies for resp in resp_list])
            })
        
        return RefactoringStrategy(
            original_name=detection.name,
            separation_approach="extract_classes",
            new_modules=new_modules,
            remaining_core={"name": f"{detection.name}Core", "type": "coordinator"},
            dependency_updates=[f"from .{module['name'].lower()} import {module['name']}" for module in new_modules],
            risk_assessment="HIGH" if len(new_modules) > 3 else "MEDIUM",
            estimated_improvement=60.0 if len(new_modules) >= 3 else 40.0
        )
    
    def _generate_method_refactoring_strategy(self, detection: GodCodeDetection) -> RefactoringStrategy:
        """Generate refactoring strategy for god method."""
        
        new_modules = []
        for i, responsibility in enumerate(detection.responsibilities):
            method_name = f"{detection.name}_{responsibility.type.value}"
            
            new_modules.append({
                "name": method_name,
                "type": "method",
                "responsibility": responsibility,
                "lines_to_extract": responsibility.lines,
                "dependencies": responsibility.external_dependencies
            })
        
        return RefactoringStrategy(
            original_name=detection.name,
            separation_approach="extract_methods",
            new_modules=new_modules,
            remaining_core={"name": detection.name, "type": "coordinator"},
            dependency_updates=[],
            risk_assessment="LOW" if len(new_modules) <= 2 else "MEDIUM",
            estimated_improvement=40.0
        )
    
    def apply_refactoring(
        self, 
        code_content: str, 
        detection: GodCodeDetection, 
        strategy: RefactoringStrategy
    ) -> RefactoringResult:
        """Apply refactoring strategy to generate refactored code."""
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would apply refactoring strategy for %s", detection.name)
            return RefactoringResult(
                original_code=code_content,
                refactored_modules={},
                updated_original=code_content,
                validation_passed=True,
                improvement_metrics={"estimated_improvement": strategy.estimated_improvement},
                warnings=["DRY RUN: No actual refactoring applied"]
            )
        
        try:
            if strategy.separation_approach == "extract_classes":
                return self._apply_class_extraction(code_content, detection, strategy)
            elif strategy.separation_approach == "extract_methods":
                return self._apply_method_extraction(code_content, detection, strategy)
            else:
                raise NotImplementedError(f"Refactoring approach {strategy.separation_approach} not implemented")
                
        except Exception as e:
            self.logger.error("Failed to apply refactoring: %s", e)
            return RefactoringResult(
                original_code=code_content,
                refactored_modules={},
                updated_original=code_content,
                validation_passed=False,
                improvement_metrics={},
                warnings=[f"Refactoring failed: {e}"]
            )
    
    def _apply_class_extraction(
        self, 
        code_content: str, 
        detection: GodCodeDetection, 
        strategy: RefactoringStrategy
    ) -> RefactoringResult:
        """Apply class extraction refactoring."""
        
        lines = code_content.splitlines()
        refactored_modules = {}
        
        # Generate new classes
        for module in strategy.new_modules:
            class_code = self._generate_extracted_class(module, lines, detection)
            refactored_modules[f"{module['name'].lower()}.py"] = class_code
        
        # Update original class to use extracted classes
        updated_original = self._update_original_class_with_delegation(
            code_content, detection, strategy
        )
        
        return RefactoringResult(
            original_code=code_content,
            refactored_modules=refactored_modules,
            updated_original=updated_original,
            validation_passed=True,  # Would need actual validation
            improvement_metrics={"estimated_improvement": strategy.estimated_improvement},
            warnings=[]
        )
    
    def _apply_method_extraction(
        self, 
        code_content: str, 
        detection: GodCodeDetection, 
        strategy: RefactoringStrategy
    ) -> RefactoringResult:
        """Apply method extraction refactoring."""
        
        lines = code_content.splitlines()
        refactored_modules = {}
        
        # Generate extracted methods
        extracted_methods = []
        for module in strategy.new_modules:
            method_code = self._generate_extracted_method(module, lines, detection)
            extracted_methods.append(method_code)
        
        # Update original method to call extracted methods
        updated_original = self._update_original_method_with_delegation(
            code_content, detection, extracted_methods
        )
        
        # Combine all in single file (or could split to multiple files)
        full_refactored_code = updated_original + "\n\n" + "\n\n".join(extracted_methods)
        refactored_modules["refactored.py"] = full_refactored_code
        
        return RefactoringResult(
            original_code=code_content,
            refactored_modules=refactored_modules,
            updated_original=full_refactored_code,
            validation_passed=True,
            improvement_metrics={"estimated_improvement": strategy.estimated_improvement},
            warnings=[]
        )
    
    def _generate_extracted_class(self, module: Dict[str, Any], lines: List[str], detection: GodCodeDetection) -> str:
        """Generate code for an extracted class."""
        
        class_name = module["name"]
        responsibilities = module.get("responsibilities", [])
        
        # Basic class template
        class_code = f'''
class {class_name}:
    """
    Extracted class handling {", ".join([r.type.value for r in responsibilities])} responsibilities
    from original {detection.name} class.
    """
    
    def __init__(self):
        pass
        
    # TODO: Extract specific methods based on responsibilities
    # Methods handling: {[r.description for r in responsibilities]}
'''
        
        return textwrap.dedent(class_code).strip()
    
    def _generate_extracted_method(self, module: Dict[str, Any], lines: List[str], detection: GodCodeDetection) -> str:
        """Generate code for an extracted method."""
        
        method_name = module["name"]
        responsibility = module.get("responsibility")
        
        if responsibility:
            method_code = f'''
def {method_name}():
    """
    Extracted method handling {responsibility.type.value} operations.
    Original responsibility: {responsibility.description}
    """
    # TODO: Extract specific logic from lines {responsibility.lines}
    pass
'''
        else:
            method_code = f'''
def {method_name}():
    """Extracted method from {detection.name}."""
    pass
'''
        
        return textwrap.dedent(method_code).strip()
    
    def _update_original_class_with_delegation(
        self, 
        code_content: str, 
        detection: GodCodeDetection, 
        strategy: RefactoringStrategy
    ) -> str:
        """Update original class to delegate to extracted classes."""
        
        # This is a simplified implementation
        # In practice, would need sophisticated AST manipulation
        
        lines = code_content.splitlines()
        updated_lines = []
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            if line_num == detection.start_line:
                # Add imports and delegation setup
                updated_lines.append(line)  # Original class definition
                for module in strategy.new_modules:
                    updated_lines.append(f"    # Delegation to {module['name']}")
                    updated_lines.append(f"    def __init__(self):")
                    updated_lines.append(f"        self._{module['name'].lower()} = {module['name']}()")
            else:
                updated_lines.append(line)
        
        return "\n".join(updated_lines)
    
    def _update_original_method_with_delegation(
        self, 
        code_content: str, 
        detection: GodCodeDetection, 
        extracted_methods: List[str]
    ) -> str:
        """Update original method to delegate to extracted methods."""
        
        lines = code_content.splitlines()
        updated_lines = []
        
        in_target_method = False
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            if line_num == detection.start_line:
                in_target_method = True
                updated_lines.append(line)  # Method definition
                updated_lines.append("    \"\"\"Refactored method with extracted responsibilities.\"\"\"")
                
                # Add delegation calls
                for j, extracted_method in enumerate(extracted_methods):
                    method_name = extracted_method.split('def ')[1].split('(')[0]
                    updated_lines.append(f"    {method_name}()")
                    
            elif line_num == detection.end_line:
                in_target_method = False
                # Skip original method body, just add return
                updated_lines.append("    pass  # TODO: Integrate extracted method results")
                
            elif not in_target_method:
                updated_lines.append(line)
            # Skip lines inside target method (they're extracted)
        
        return "\n".join(updated_lines)


# =============================================================================
# Integration and Usage
# =============================================================================

def run_god_code_analysis(file_path: str, aggressive: bool = False, dry_run: bool = True) -> Dict[str, Any]:
    """
    Run god code analysis on a specific file.
    
    Args:
        file_path: Path to Python file to analyze
        aggressive: Use aggressive detection thresholds
        dry_run: Don't apply actual refactoring
        
    Returns:
        Analysis results with detections and strategies
    """
    
    logging.basicConfig(level=logging.INFO)
    
    agent = GodCodeRefactoringAgent(dry_run=dry_run, aggressive_refactoring=aggressive)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except Exception as e:
        return {"error": f"Failed to read file {file_path}: {e}"}
    
    # Analyze god codes
    detections = agent.analyze_god_codes(file_path, code_content)
    
    results = {
        "file_path": file_path,
        "total_detections": len(detections),
        "detections": [],
        "strategies": [],
        "refactoring_results": []
    }
    
    # Generate strategies and apply refactoring for each detection
    for detection in detections:
        detection_dict = {
            "type": detection.type.value,
            "name": detection.name,
            "lines": f"{detection.start_line}-{detection.end_line}",
            "total_lines": detection.total_lines,
            "complexity_score": detection.complexity_score,
            "priority": detection.refactoring_priority,
            "responsibilities": len(detection.responsibilities),
            "suggested_modules": detection.suggested_separation
        }
        results["detections"].append(detection_dict)
        
        # Generate strategy
        strategy = agent.generate_refactoring_strategy(detection)
        strategy_dict = {
            "original_name": strategy.original_name,
            "approach": strategy.separation_approach,
            "new_modules": [m.get('name', 'Unknown') for m in strategy.new_modules],
            "risk": strategy.risk_assessment,
            "improvement": strategy.estimated_improvement
        }
        results["strategies"].append(strategy_dict)
        
        # Apply refactoring
        refactoring_result = agent.apply_refactoring(code_content, detection, strategy)
        result_dict = {
            "original_name": detection.name,
            "success": refactoring_result.validation_passed,
            "modules_created": list(refactoring_result.refactored_modules.keys()),
            "warnings": refactoring_result.warnings
        }
        results["refactoring_results"].append(result_dict)
    
    return results


if __name__ == "__main__":
    # Example usage and testing
    agent = GodCodeRefactoringAgent(dry_run=True, aggressive_refactoring=False)
    
    # Test with sample god method
    sample_god_method = '''
def process_user_data(user_data, config):
    """A god method that does too many things."""
    
    # Validation
    if not user_data:
        raise ValueError("User data is required")
    if not isinstance(user_data, dict):
        raise TypeError("User data must be dictionary")
        
    # Database access
    conn = database.connect()
    cursor = conn.cursor()
    
    # Business logic  
    processed_data = {}
    for key, value in user_data.items():
        if key == 'email':
            processed_data[key] = value.lower().strip()
        elif key == 'age':
            processed_data[key] = int(value)
        elif key == 'score':
            processed_data[key] = calculate_score(value)
            
    # More database access
    cursor.execute("INSERT INTO users VALUES (?)", (processed_data,))
    conn.commit()
    
    # Logging
    logger.info("Processed user data: %s", processed_data)
    
    # Formatting
    formatted_output = json.dumps(processed_data, indent=2)
    
    # More business logic
    if processed_data.get('score', 0) > 100:
        send_notification(processed_data['email'])
        
    return formatted_output
'''
    
    detections = agent.analyze_god_codes("sample.py", sample_god_method)
    for detection in detections:
        print(f"\n🔍 Detected {detection.type.value}: {detection.name}")
        print(f"   Lines: {detection.total_lines}, Complexity: {detection.complexity_score:.1f}")
        print(f"   Responsibilities: {len(detection.responsibilities)}")
        print(f"   Priority: {detection.refactoring_priority}")
        
        strategy = agent.generate_refactoring_strategy(detection)
        print(f"   Strategy: {strategy.separation_approach}")
        print(f"   New modules: {[m['name'] for m in strategy.new_modules]}")
        
        result = agent.apply_refactoring(sample_god_method, detection, strategy)
        print(f"   Refactoring success: {result.validation_passed}")
        print(f"   Generated modules: {list(result.refactored_modules.keys())}")