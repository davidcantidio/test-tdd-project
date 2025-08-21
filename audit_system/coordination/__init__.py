#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 Audit System - Coordination Layer

Sistema de coordenação inteligente para execução segura de agentes:
- MetaAgent: Coordenação inteligente de agentes especializados
- FileCoordinationManager: Coordenação segura de modificações em arquivos
"""

from audit_system.coordination.meta_agent import (
    MetaAgent,
    TaskType,
    AgentType,
    Priority,
    FileComplexity,
    FileAnalysis,
    AgentRecommendation,
    TaskExecution,
    ExecutionResult,
    run_meta_agent_analysis
)

from audit_system.coordination.file_coordination_manager import (
    FileCoordinationManager,
    get_coordination_manager,
    safe_file_modification,
    LockType
)

__all__ = [
    # MetaAgent
    "MetaAgent",
    "TaskType",
    "AgentType", 
    "Priority",
    "FileComplexity",
    "FileAnalysis",
    "AgentRecommendation",
    "TaskExecution",
    "ExecutionResult",
    "run_meta_agent_analysis",
    
    # FileCoordinationManager
    "FileCoordinationManager",
    "get_coordination_manager", 
    "safe_file_modification",
    "LockType"
]