#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tools Module - Agno-native refactoring tools.

This module provides Agno-compatible tools for intelligent code refactoring:
- BaseRefactoringTool: Base class for all refactoring tools
- ExtractMethodTool: Method extraction with AST analysis
- ExceptionHandlingTool: Exception handling improvement
- StringOptimizationTool: String operations optimization
- GodMethodEliminationTool: God method elimination
- DatabaseQueryOptimizationTool: Database query optimization
- ExtractConstantsTool: Magic number/string extraction
- ConditionalLogicTool: Complex conditional simplification
- GodCodeRefactoringTool: God code elimination
"""

from pathlib import Path

# Module information
__version__ = "1.0.0"
__author__ = "Intelligent Audit System - Agno Native"

# Check if tools are available
try:
    from .base_refactoring_tool import BaseRefactoringTool
    BASE_TOOL_AVAILABLE = True
except ImportError:
    BASE_TOOL_AVAILABLE = False
    BaseRefactoringTool = None

try:
    from .extract_method_tool import ExtractMethodTool
    EXTRACT_METHOD_AVAILABLE = True
except ImportError:
    EXTRACT_METHOD_AVAILABLE = False
    ExtractMethodTool = None

try:
    from .exception_handling_tool import ExceptionHandlingTool
    EXCEPTION_HANDLING_AVAILABLE = True
except ImportError:
    EXCEPTION_HANDLING_AVAILABLE = False
    ExceptionHandlingTool = None

try:
    from .string_optimization_tool import StringOptimizationTool
    STRING_OPTIMIZATION_AVAILABLE = True
except ImportError:
    STRING_OPTIMIZATION_AVAILABLE = False
    StringOptimizationTool = None

try:
    from .god_method_elimination_tool import GodMethodEliminationTool
    GOD_METHOD_AVAILABLE = True
except ImportError:
    GOD_METHOD_AVAILABLE = False
    GodMethodEliminationTool = None

try:
    from .database_query_optimization_tool import DatabaseQueryOptimizationTool
    DATABASE_OPTIMIZATION_AVAILABLE = True
except ImportError:
    DATABASE_OPTIMIZATION_AVAILABLE = False
    DatabaseQueryOptimizationTool = None

try:
    from .extract_constants_tool import ExtractConstantsTool
    EXTRACT_CONSTANTS_AVAILABLE = True
except ImportError:
    EXTRACT_CONSTANTS_AVAILABLE = False
    ExtractConstantsTool = None

try:
    from .conditional_logic_tool import ConditionalLogicTool
    CONDITIONAL_LOGIC_AVAILABLE = True
except ImportError:
    CONDITIONAL_LOGIC_AVAILABLE = False
    ConditionalLogicTool = None

try:
    from .god_code_refactoring_tool import GodCodeRefactoringTool
    GOD_CODE_AVAILABLE = True
except ImportError:
    GOD_CODE_AVAILABLE = False
    GodCodeRefactoringTool = None

# Analysis tools
try:
    from .complexity_analyzer_tool import ComplexityAnalyzerTool
    COMPLEXITY_ANALYZER_AVAILABLE = True
except ImportError:
    COMPLEXITY_ANALYZER_AVAILABLE = False
    ComplexityAnalyzerTool = None

try:
    from .pattern_detector_tool import PatternDetectorTool
    PATTERN_DETECTOR_AVAILABLE = True
except ImportError:
    PATTERN_DETECTOR_AVAILABLE = False
    PatternDetectorTool = None

try:
    from .dependency_analyzer_tool import DependencyAnalyzerTool
    DEPENDENCY_ANALYZER_AVAILABLE = True
except ImportError:
    DEPENDENCY_ANALYZER_AVAILABLE = False
    DependencyAnalyzerTool = None

try:
    from .method_analyzer_tool import MethodAnalyzerTool
    METHOD_ANALYZER_AVAILABLE = True
except ImportError:
    METHOD_ANALYZER_AVAILABLE = False
    MethodAnalyzerTool = None

# Validation tools
try:
    from .syntax_validator_tool import SyntaxValidatorTool
    SYNTAX_VALIDATOR_AVAILABLE = True
except ImportError:
    SYNTAX_VALIDATOR_AVAILABLE = False
    SyntaxValidatorTool = None

try:
    from .test_runner_tool import TestRunnerTool
    TEST_RUNNER_AVAILABLE = True
except ImportError:
    TEST_RUNNER_AVAILABLE = False
    TestRunnerTool = None

try:
    from .performance_benchmark_tool import PerformanceBenchmarkTool
    PERFORMANCE_BENCHMARK_AVAILABLE = True
except ImportError:
    PERFORMANCE_BENCHMARK_AVAILABLE = False
    PerformanceBenchmarkTool = None

try:
    from .security_scanner_tool import SecurityScannerTool
    SECURITY_SCANNER_AVAILABLE = True
except ImportError:
    SECURITY_SCANNER_AVAILABLE = False
    SecurityScannerTool = None

# Export available tools
__all__ = []

# Base tool
if BASE_TOOL_AVAILABLE:
    __all__.append("BaseRefactoringTool")

# Refactoring tools
if EXTRACT_METHOD_AVAILABLE:
    __all__.append("ExtractMethodTool")
if EXCEPTION_HANDLING_AVAILABLE:
    __all__.append("ExceptionHandlingTool")
if STRING_OPTIMIZATION_AVAILABLE:
    __all__.append("StringOptimizationTool")
if GOD_METHOD_AVAILABLE:
    __all__.append("GodMethodEliminationTool")
if DATABASE_OPTIMIZATION_AVAILABLE:
    __all__.append("DatabaseQueryOptimizationTool")
if EXTRACT_CONSTANTS_AVAILABLE:
    __all__.append("ExtractConstantsTool")
if CONDITIONAL_LOGIC_AVAILABLE:
    __all__.append("ConditionalLogicTool")
if GOD_CODE_AVAILABLE:
    __all__.append("GodCodeRefactoringTool")

# Analysis tools
if COMPLEXITY_ANALYZER_AVAILABLE:
    __all__.append("ComplexityAnalyzerTool")
if PATTERN_DETECTOR_AVAILABLE:
    __all__.append("PatternDetectorTool")
if DEPENDENCY_ANALYZER_AVAILABLE:
    __all__.append("DependencyAnalyzerTool")
if METHOD_ANALYZER_AVAILABLE:
    __all__.append("MethodAnalyzerTool")

# Validation tools
if SYNTAX_VALIDATOR_AVAILABLE:
    __all__.append("SyntaxValidatorTool")
if TEST_RUNNER_AVAILABLE:
    __all__.append("TestRunnerTool")
if PERFORMANCE_BENCHMARK_AVAILABLE:
    __all__.append("PerformanceBenchmarkTool")
if SECURITY_SCANNER_AVAILABLE:
    __all__.append("SecurityScannerTool")

# Tools status
REFACTORING_TOOLS_AVAILABLE = (EXTRACT_METHOD_AVAILABLE or EXCEPTION_HANDLING_AVAILABLE or 
                               STRING_OPTIMIZATION_AVAILABLE or GOD_METHOD_AVAILABLE or
                               DATABASE_OPTIMIZATION_AVAILABLE or EXTRACT_CONSTANTS_AVAILABLE or
                               CONDITIONAL_LOGIC_AVAILABLE or GOD_CODE_AVAILABLE)

ANALYSIS_TOOLS_AVAILABLE = (COMPLEXITY_ANALYZER_AVAILABLE or PATTERN_DETECTOR_AVAILABLE or
                           DEPENDENCY_ANALYZER_AVAILABLE or METHOD_ANALYZER_AVAILABLE)

VALIDATION_TOOLS_AVAILABLE = (SYNTAX_VALIDATOR_AVAILABLE or TEST_RUNNER_AVAILABLE or
                             PERFORMANCE_BENCHMARK_AVAILABLE or SECURITY_SCANNER_AVAILABLE)

TOOLS_AVAILABLE = REFACTORING_TOOLS_AVAILABLE or ANALYSIS_TOOLS_AVAILABLE or VALIDATION_TOOLS_AVAILABLE

def get_tools_status():
    """Get status of all tool categories."""
    return {
        "base_tool": BASE_TOOL_AVAILABLE,
        "refactoring_tools": {
            "extract_method": EXTRACT_METHOD_AVAILABLE,
            "exception_handling": EXCEPTION_HANDLING_AVAILABLE,
            "string_optimization": STRING_OPTIMIZATION_AVAILABLE,
            "god_method_elimination": GOD_METHOD_AVAILABLE,
            "database_optimization": DATABASE_OPTIMIZATION_AVAILABLE,
            "extract_constants": EXTRACT_CONSTANTS_AVAILABLE,
            "conditional_logic": CONDITIONAL_LOGIC_AVAILABLE,
            "god_code_refactoring": GOD_CODE_AVAILABLE,
            "overall": REFACTORING_TOOLS_AVAILABLE
        },
        "analysis_tools": {
            "complexity_analyzer": COMPLEXITY_ANALYZER_AVAILABLE,
            "pattern_detector": PATTERN_DETECTOR_AVAILABLE,
            "dependency_analyzer": DEPENDENCY_ANALYZER_AVAILABLE,
            "method_analyzer": METHOD_ANALYZER_AVAILABLE,
            "overall": ANALYSIS_TOOLS_AVAILABLE
        },
        "validation_tools": {
            "syntax_validator": SYNTAX_VALIDATOR_AVAILABLE,
            "test_runner": TEST_RUNNER_AVAILABLE,
            "performance_benchmark": PERFORMANCE_BENCHMARK_AVAILABLE,
            "security_scanner": SECURITY_SCANNER_AVAILABLE,
            "overall": VALIDATION_TOOLS_AVAILABLE
        },
        "overall": TOOLS_AVAILABLE
    }

def get_available_refactoring_tools():
    """Get list of available refactoring tools."""
    tools = []
    if EXTRACT_METHOD_AVAILABLE:
        tools.append(("extract_method", ExtractMethodTool))
    if EXCEPTION_HANDLING_AVAILABLE:
        tools.append(("exception_handling", ExceptionHandlingTool))
    if STRING_OPTIMIZATION_AVAILABLE:
        tools.append(("string_optimization", StringOptimizationTool))
    if GOD_METHOD_AVAILABLE:
        tools.append(("god_method_elimination", GodMethodEliminationTool))
    if DATABASE_OPTIMIZATION_AVAILABLE:
        tools.append(("database_optimization", DatabaseQueryOptimizationTool))
    if EXTRACT_CONSTANTS_AVAILABLE:
        tools.append(("extract_constants", ExtractConstantsTool))
    if CONDITIONAL_LOGIC_AVAILABLE:
        tools.append(("conditional_logic", ConditionalLogicTool))
    if GOD_CODE_AVAILABLE:
        tools.append(("god_code_refactoring", GodCodeRefactoringTool))
    return tools

def get_available_analysis_tools():
    """Get list of available analysis tools."""
    tools = []
    if COMPLEXITY_ANALYZER_AVAILABLE:
        tools.append(("complexity_analyzer", ComplexityAnalyzerTool))
    if PATTERN_DETECTOR_AVAILABLE:
        tools.append(("pattern_detector", PatternDetectorTool))
    if DEPENDENCY_ANALYZER_AVAILABLE:
        tools.append(("dependency_analyzer", DependencyAnalyzerTool))
    if METHOD_ANALYZER_AVAILABLE:
        tools.append(("method_analyzer", MethodAnalyzerTool))
    return tools

def get_available_validation_tools():
    """Get list of available validation tools."""
    tools = []
    if SYNTAX_VALIDATOR_AVAILABLE:
        tools.append(("syntax_validator", SyntaxValidatorTool))
    if TEST_RUNNER_AVAILABLE:
        tools.append(("test_runner", TestRunnerTool))
    if PERFORMANCE_BENCHMARK_AVAILABLE:
        tools.append(("performance_benchmark", PerformanceBenchmarkTool))
    if SECURITY_SCANNER_AVAILABLE:
        tools.append(("security_scanner", SecurityScannerTool))
    return tools