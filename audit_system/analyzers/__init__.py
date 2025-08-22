#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyzers Module - Code analysis and pattern detection.

This module provides specialized analyzers for the intelligent audit system:
- MethodAnalyzer: Method-level analysis and complexity scoring
- ComplexityAnalyzer: Cyclomatic and cognitive complexity analysis
- PatternDetector: Code smell and anti-pattern detection
- DependencyAnalyzer: Dependency graph and coupling analysis
"""

from pathlib import Path

# Module information
__version__ = "1.0.0"
__author__ = "Intelligent Audit System"

# Check if analyzer components are available
try:
    from .method_analyzer import MethodAnalyzer
    METHOD_ANALYZER_AVAILABLE = True
except ImportError:
    METHOD_ANALYZER_AVAILABLE = False
    MethodAnalyzer = None

try:
    from .complexity_analyzer import ComplexityAnalyzer
    COMPLEXITY_ANALYZER_AVAILABLE = True
except ImportError:
    COMPLEXITY_ANALYZER_AVAILABLE = False
    ComplexityAnalyzer = None

try:
    from .pattern_detector import PatternDetector
    PATTERN_DETECTOR_AVAILABLE = True
except ImportError:
    PATTERN_DETECTOR_AVAILABLE = False
    PatternDetector = None

try:
    from .dependency_analyzer import DependencyAnalyzer
    DEPENDENCY_ANALYZER_AVAILABLE = True
except ImportError:
    DEPENDENCY_ANALYZER_AVAILABLE = False
    DependencyAnalyzer = None

# Export available components
__all__ = []

if METHOD_ANALYZER_AVAILABLE:
    __all__.append("MethodAnalyzer")

if COMPLEXITY_ANALYZER_AVAILABLE:
    __all__.append("ComplexityAnalyzer")

if PATTERN_DETECTOR_AVAILABLE:
    __all__.append("PatternDetector")

if DEPENDENCY_ANALYZER_AVAILABLE:
    __all__.append("DependencyAnalyzer")

# Analyzers status
ANALYZERS_AVAILABLE = (METHOD_ANALYZER_AVAILABLE or COMPLEXITY_ANALYZER_AVAILABLE or 
                       PATTERN_DETECTOR_AVAILABLE or DEPENDENCY_ANALYZER_AVAILABLE)

def get_analyzers_status():
    """Get status of analyzer components."""
    return {
        "method_analyzer": METHOD_ANALYZER_AVAILABLE,
        "complexity_analyzer": COMPLEXITY_ANALYZER_AVAILABLE,
        "pattern_detector": PATTERN_DETECTOR_AVAILABLE,
        "dependency_analyzer": DEPENDENCY_ANALYZER_AVAILABLE,
        "overall": ANALYZERS_AVAILABLE
    }