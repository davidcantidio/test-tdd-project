"""🔧 Configuration Package

Centraliza configuração e *constants* para o TDD Framework.
"""

from .streamlit_config import StreamlitConfig, load_config, create_streamlit_config_file
from .constants import (
    StatusValues as GeneralStatus,
    TDDPhases as TDDPhase,
    CompanySizes as CompanySize,
    ErrorMessages,
    FormFields, CacheConfig, FilterOptions, ValidationRules
)

__all__ = [
    "StreamlitConfig", "load_config", "create_streamlit_config_file",
    'GeneralStatus', 'TDDPhase', 'CompanySize',
    'ErrorMessages',
    'FormFields', 'CacheConfig', 'FilterOptions', 'ValidationRules'
]