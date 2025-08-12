"""
🚀 Streamlit Extension for TDD Framework

Interactive, gamified interface for TDD workflow with:
- Timer integration
- Analytics dashboards  
- Task management
- GitHub sync
- TDAH support
"""

__version__ = "1.0.0"
__author__ = "TDD Framework"

# Graceful imports for optional dependencies
try:
    import streamlit
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    import sqlalchemy
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

try:
    import gql
    GQL_AVAILABLE = True
except ImportError:
    GQL_AVAILABLE = False

try:
    import dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

def check_dependencies():
    """Check if all required dependencies are available."""
    missing = []
    
    if not STREAMLIT_AVAILABLE:
        missing.append("streamlit")
    if not SQLALCHEMY_AVAILABLE:
        missing.append("sqlalchemy")
    if not GQL_AVAILABLE:
        missing.append("gql")
    if not DOTENV_AVAILABLE:
        missing.append("python-dotenv")
    
    return missing

def is_ready():
    """Check if streamlit extension is ready to use."""
    return len(check_dependencies()) == 0