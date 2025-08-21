#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Audit System - Intelligent Agents

Agentes especializados de análise e refatoração de código:
- IntelligentCodeAgent: Análise semântica linha-por-linha com IA
- GodCodeRefactoringAgent: Detecção e refatoração de god codes
- IntelligentRefactoringEngine: Engine de refatoração com 7 estratégias
- TDDIntelligentWorkflowAgent: Otimização de workflow TDD com recursos TDAH
"""

from audit_system.agents.intelligent_code_agent import (
    IntelligentCodeAgent,
    AnalysisDepth,
    SemanticMode,
    FileSemanticAnalysis,
    IntelligentRefactoring
)

from audit_system.agents.god_code_refactoring_agent import (
    GodCodeRefactoringAgent,
    run_god_code_analysis,
    GodCodeDetection,
    RefactoringStrategy,
    RefactoringResult
)

from audit_system.agents.intelligent_refactoring_engine import (
    IntelligentRefactoringEngine
)

from audit_system.agents.tdd_intelligent_workflow_agent import (
    TDDIntelligentWorkflowAgent,
    TDDPhase,
    TDAHEnergyLevel
)

__all__ = [
    # IntelligentCodeAgent
    "IntelligentCodeAgent",
    "AnalysisDepth", 
    "SemanticMode",
    "FileSemanticAnalysis",
    "IntelligentRefactoring",
    
    # GodCodeRefactoringAgent
    "GodCodeRefactoringAgent",
    "run_god_code_analysis",
    "GodCodeDetection",
    "RefactoringStrategy", 
    "RefactoringResult",
    
    # IntelligentRefactoringEngine
    "IntelligentRefactoringEngine",
    
    # TDDIntelligentWorkflowAgent
    "TDDIntelligentWorkflowAgent",
    "TDDPhase",
    "TDAHEnergyLevel"
]