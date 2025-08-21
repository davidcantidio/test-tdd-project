"""🔧 Configuration Package

Centraliza configuração e *constants* para o TDD Framework.
"""

from .streamlit_config import StreamlitConfig, load_config, create_streamlit_config_file
from .constants import (
    StatusValues as GeneralStatus,
    TDDPhases as TDDPhase,
    ClientTiers as ClientTier,
    CompanySizes as CompanySize,
    ErrorMessages,
    FormFields, CacheConfig, FilterOptions, ValidationRules
)

__all__ = [
    "StreamlitConfig", "load_config", "create_streamlit_config_file",
    'GeneralStatus', 'TDDPhase', 'ClientTier', 'CompanySize',
    'ErrorMessages',
    'FormFields', 'CacheConfig', 'FilterOptions', 'ValidationRules'
]