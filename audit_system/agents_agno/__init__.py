#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agno Native Agents - Real Agno-powered intelligent code agents.

This module provides Agno-native agents for intelligent code analysis and refactoring:
- CodeAnalyzerAgent: Deep code analysis with LLM understanding
- RefactoringSpecialistAgent: Semantic-aware refactoring application  
- ValidationAgent: Comprehensive validation and testing
- RefactoringTeam: Coordinated multi-agent refactoring workflow
"""

from pathlib import Path

# Module information
__version__ = "1.0.0"
__author__ = "Intelligent Audit System - Agno Native"

# Check if Agno is available
try:
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    Agent = None
    OpenAIChat = None

# Check if agents are available
try:
    from .code_analyzer_agent import CodeAnalyzerAgent
    CODE_ANALYZER_AVAILABLE = True
except ImportError:
    CODE_ANALYZER_AVAILABLE = False
    CodeAnalyzerAgent = None

try:
    from .refactoring_specialist_agent import RefactoringSpecialistAgent
    REFACTORING_SPECIALIST_AVAILABLE = True
except ImportError:
    REFACTORING_SPECIALIST_AVAILABLE = False
    RefactoringSpecialistAgent = None

try:
    from .validation_agent import ValidationAgent
    VALIDATION_AGENT_AVAILABLE = True
except ImportError:
    VALIDATION_AGENT_AVAILABLE = False
    ValidationAgent = None

try:
    from .refactoring_team import RefactoringTeam
    REFACTORING_TEAM_AVAILABLE = True
except ImportError:
    REFACTORING_TEAM_AVAILABLE = False
    RefactoringTeam = None

# Export available components
__all__ = []

if CODE_ANALYZER_AVAILABLE:
    __all__.append("CodeAnalyzerAgent")

if REFACTORING_SPECIALIST_AVAILABLE:
    __all__.append("RefactoringSpecialistAgent")

if VALIDATION_AGENT_AVAILABLE:
    __all__.append("ValidationAgent")

if REFACTORING_TEAM_AVAILABLE:
    __all__.append("RefactoringTeam")

# Agent status
AGENTS_AVAILABLE = (CODE_ANALYZER_AVAILABLE or REFACTORING_SPECIALIST_AVAILABLE or 
                   VALIDATION_AGENT_AVAILABLE or REFACTORING_TEAM_AVAILABLE)

def get_agents_status():
    """Get status of Agno native agents."""
    return {
        "agno_available": AGNO_AVAILABLE,
        "code_analyzer": CODE_ANALYZER_AVAILABLE,
        "refactoring_specialist": REFACTORING_SPECIALIST_AVAILABLE,
        "validation_agent": VALIDATION_AGENT_AVAILABLE,
        "refactoring_team": REFACTORING_TEAM_AVAILABLE,
        "overall": AGENTS_AVAILABLE and AGNO_AVAILABLE
    }

def create_refactoring_workflow():
    """Create a complete refactoring workflow with all agents."""
    if not (AGNO_AVAILABLE and REFACTORING_TEAM_AVAILABLE):
        raise ImportError("Agno and RefactoringTeam are required for workflow creation")
    
    return RefactoringTeam()

# Environment check
if not AGNO_AVAILABLE:
    import warnings
    warnings.warn(
        "Agno is not available. Please install with: pip install agno",
        ImportWarning
    )