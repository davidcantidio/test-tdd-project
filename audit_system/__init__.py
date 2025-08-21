#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ Audit System - Enterprise Code Analysis and Intelligent Refactoring

Sistema completo de auditoria de código com agentes de IA especializados para:
- Análise semântica avançada de código
- Detecção e refatoração de god codes
- Otimizações inteligentes de performance
- Coordenação segura de modificações em arquivos
- Workflow TDD com recursos TDAH

Arquitetura:
- agents/: Agentes especializados de análise e refatoração
- coordination/: Meta-agente e coordenação de arquivos
- core/: Sistema base de auditoria
- cli/: Interface de linha de comando
- utils/: Utilitários compartilhados

Uso:
    from audit_system.coordination.meta_agent import MetaAgent
    from audit_system.agents.god_code_refactoring_agent import GodCodeRefactoringAgent
"""

__version__ = "1.0.0"
__author__ = "Claude + David"

# Main exports for easy access
try:
    from audit_system.coordination.meta_agent import (
        MetaAgent,
        TaskType,
        run_meta_agent_analysis,
    )
    from audit_system.agents.intelligent_code_agent import (
        IntelligentCodeAgent,
        AnalysisDepth,
        SemanticMode,
    )
    from audit_system.agents.god_code_refactoring_agent import (
        GodCodeRefactoringAgent,
        run_god_code_analysis,
    )
    from audit_system.coordination.file_coordination_manager import (
        FileCoordinationManager,
        get_coordination_manager,
    )
except Exception as e:  # pragma: no cover - optional deps may be missing
    # Keep module importable even if optional dependencies (e.g., streamlit) are absent
    MetaAgent = TaskType = run_meta_agent_analysis = None
    IntelligentCodeAgent = AnalysisDepth = SemanticMode = None
    GodCodeRefactoringAgent = run_god_code_analysis = None
    FileCoordinationManager = get_coordination_manager = None

__all__ = [
    "MetaAgent",
    "TaskType", 
    "run_meta_agent_analysis",
    "IntelligentCodeAgent",
    "AnalysisDepth",
    "SemanticMode", 
    "GodCodeRefactoringAgent",
    "run_god_code_analysis",
    "FileCoordinationManager",
    "get_coordination_manager"
]