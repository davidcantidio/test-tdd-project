#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Audit System - Agno-Based Intelligent Code Analysis

Sistema simplificado de auditoria usando apenas agentes Agno:
- Análise semântica real com LLM
- Refatoração inteligente baseada em contexto
- Detecção e eliminação de god codes
- Workflow TDD otimizado para TDAH

Arquitetura Agno-Only:
- agents/: Agentes inteligentes Agno-compatible
- context/: Contexto do projeto para análise semântica
- core/: Rate limiting e backends LLM
- utils/: Utilitários básicos

Uso Direto:
    from audit_system.agents.intelligent_code_agent import IntelligentCodeAgent
    from audit_system.agents.intelligent_refactoring_engine import IntelligentRefactoringEngine
"""

__version__ = "2.0.0-agno"
__author__ = "Claude + David (Agno-based)"

# Agno-only exports
try:
    from audit_system.agents.intelligent_code_agent import (
        IntelligentCodeAgent,
        AnalysisDepth,
        SemanticMode,
    )
    from audit_system.agents.intelligent_refactoring_engine import (
        IntelligentRefactoringEngine,
    )
    from audit_system.agents.god_code_refactoring_agent import (
        GodCodeRefactoringAgent,
        run_god_code_analysis,
    )
    from audit_system.agents.tdd_intelligent_workflow_agent import (
        TDDIntelligentWorkflowAgent,
    )
except Exception as e:  # pragma: no cover - graceful degradation
    # Keep module importable even with missing dependencies
    IntelligentCodeAgent = AnalysisDepth = SemanticMode = None
    IntelligentRefactoringEngine = None
    GodCodeRefactoringAgent = run_god_code_analysis = None
    TDDIntelligentWorkflowAgent = None

__all__ = [
    "IntelligentCodeAgent",
    "AnalysisDepth",
    "SemanticMode", 
    "IntelligentRefactoringEngine",
    "GodCodeRefactoringAgent",
    "run_god_code_analysis",
    "TDDIntelligentWorkflowAgent",
]