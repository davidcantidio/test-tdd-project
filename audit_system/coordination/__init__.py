#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coordination Module - Multi-agent orchestration and file management.

This module provides coordination capabilities for the intelligent audit system:
- MetaAgent: Master coordinator for multi-agent execution
- Orchestrator: Pipeline execution and parallelization
- FileCoordinationManager: Safe file modification and conflict prevention
"""

from pathlib import Path

# Module information
__version__ = "1.0.0"
__author__ = "Intelligent Audit System"

# Check if coordination components are available
try:
    from .meta_agent import MetaAgent
    META_AGENT_AVAILABLE = True
except ImportError:
    META_AGENT_AVAILABLE = False
    MetaAgent = None

try:
    from .orchestrator import Orchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    Orchestrator = None

try:
    from .file_coordination_manager import FileCoordinationManager
    FILE_MANAGER_AVAILABLE = True
except ImportError:
    FILE_MANAGER_AVAILABLE = False
    FileCoordinationManager = None

# Export available components
__all__ = []

if META_AGENT_AVAILABLE:
    __all__.append("MetaAgent")

if ORCHESTRATOR_AVAILABLE:
    __all__.append("Orchestrator")

if FILE_MANAGER_AVAILABLE:
    __all__.append("FileCoordinationManager")

# Coordination status
COORDINATION_AVAILABLE = META_AGENT_AVAILABLE or ORCHESTRATOR_AVAILABLE or FILE_MANAGER_AVAILABLE

def get_coordination_status():
    """Get status of coordination components."""
    return {
        "meta_agent": META_AGENT_AVAILABLE,
        "orchestrator": ORCHESTRATOR_AVAILABLE,
        "file_manager": FILE_MANAGER_AVAILABLE,
        "overall": COORDINATION_AVAILABLE
    }