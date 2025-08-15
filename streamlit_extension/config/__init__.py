"""
🔧 Configuration Package

Centralized configuration and constants for the TDD Framework.
Addresses report.md requirement: "Centralize hard-coded strings in enums/config"

This package provides:
- Application constants and enums
- Configuration management  
- Validation rules and patterns
"""

from .streamlit_config import StreamlitConfig, load_config, create_streamlit_config_file
from .constants import (
    TaskStatus, EpicStatus, ProjectStatus, GeneralStatus, TDDPhase,
    ClientTier, CompanySize, Priority, TableNames, FieldNames,
    UIConstants, FormFields, CacheConfig, FilterOptions, ValidationRules
)

__all__ = [
    "StreamlitConfig", "load_config", "create_streamlit_config_file",
    'TaskStatus', 'EpicStatus', 'ProjectStatus', 'GeneralStatus', 'TDDPhase',
    'ClientTier', 'CompanySize', 'Priority', 'TableNames', 'FieldNames',
    'UIConstants', 'FormFields', 'CacheConfig', 'FilterOptions', 'ValidationRules'
]