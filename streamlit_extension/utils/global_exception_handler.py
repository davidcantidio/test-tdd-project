"""
Global Exception Handler for Streamlit Application
Prevents raw error messages from reaching users
"""

import os
import hashlib
import logging
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

# Safe imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/application_errors.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ExceptionCategory:
    """Exception categories for user-friendly messages"""
    
    DATABASE_ERROR = "database"
    VALIDATION_ERROR = "validation"
    AUTHENTICATION_ERROR = "auth"
    PERMISSION_ERROR = "permission"
    NETWORK_ERROR = "network"
    FILE_ERROR = "file"
    UNKNOWN_ERROR = "unknown"

class UserFriendlyMessages:
    """User-friendly error messages by category"""
    
    MESSAGES = {
        ExceptionCategory.DATABASE_ERROR: {
            "title": "🗄️ Erro de Banco de Dados",
            "message": "Não foi possível conectar ao banco de dados. Tente novamente em alguns minutos.",
            "action": "Se o problema persistir, entre em contato com o suporte."
        },
        ExceptionCategory.VALIDATION_ERROR: {
            "title": "✏️ Dados Inválidos",
            "message": "Alguns campos não foram preenchidos corretamente.",
            "action": "Verifique os dados informados e tente novamente."
        },
        ExceptionCategory.AUTHENTICATION_ERROR: {
            "title": "🔐 Erro de Autenticação",
            "message": "Sua sessão expirou ou você não tem permissão para esta ação.",
            "action": "Faça login novamente."
        },
        ExceptionCategory.PERMISSION_ERROR: {
            "title": "🚫 Acesso Negado", 
            "message": "Você não tem permissão para executar esta ação.",
            "action": "Entre em contato com o administrador se necessário."
        },
        ExceptionCategory.NETWORK_ERROR: {
            "title": "🌐 Erro de Conexão",
            "message": "Problema de conectividade detectado.",
            "action": "Verifique sua conexão e tente novamente."
        },
        ExceptionCategory.FILE_ERROR: {
            "title": "📁 Erro de Arquivo",
            "message": "Não foi possível processar o arquivo.",
            "action": "Verifique se o arquivo não está corrompido."
        },
        ExceptionCategory.UNKNOWN_ERROR: {
            "title": "⚠️ Erro Inesperado",
            "message": "Algo deu errado. Nossa equipe foi notificada.",
            "action": "Tente novamente ou entre em contato com o suporte."
        }
    }

class GlobalExceptionHandler:
    """Global exception handler for Streamlit apps"""
    
    def __init__(self):
        self.error_counts = {}
        
    def categorize_exception(self, exception: Exception) -> str:
        """Categorize exception type"""
        
        exception_name = type(exception).__name__.lower()
        exception_message = str(exception).lower()
        
        # Database related
        if any(keyword in exception_name for keyword in ['sqlite', 'database', 'sql', 'connection']):
            return ExceptionCategory.DATABASE_ERROR
            
        if any(keyword in exception_message for keyword in ['database', 'connection', 'sqlite']):
            return ExceptionCategory.DATABASE_ERROR
            
        # Validation related
        if any(keyword in exception_name for keyword in ['validation', 'value', 'type', 'attribute']):
            return ExceptionCategory.VALIDATION_ERROR
            
        # Authentication related
        if any(keyword in exception_name for keyword in ['auth', 'permission', 'unauthorized']):
            return ExceptionCategory.AUTHENTICATION_ERROR
            
        # File related
        if any(keyword in exception_name for keyword in ['file', 'io', 'path']):
            return ExceptionCategory.FILE_ERROR
            
        # Network related
        if any(keyword in exception_name for keyword in ['connection', 'timeout', 'network']):
            return ExceptionCategory.NETWORK_ERROR
            
        return ExceptionCategory.UNKNOWN_ERROR
    
    def generate_error_id(self, exception: Exception) -> str:
        """Generate unique error ID for tracking"""
        error_content = f"{type(exception).__name__}:{str(exception)[:100]}"
        return hashlib.md5(error_content.encode()).hexdigest()[:8]
    
    def log_exception(self, exception: Exception, context: Dict[str, Any] = None):
        """Log exception with context"""
        error_id = self.generate_error_id(exception)
        category = self.categorize_exception(exception)
        
        log_data = {
            "error_id": error_id,
            "category": category,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        # Track error frequency
        self.error_counts[error_id] = self.error_counts.get(error_id, 0) + 1
        log_data["occurrence_count"] = self.error_counts[error_id]
        
        logger.error(f"Application Error: {log_data}")
        
        return error_id, category
    
    def show_user_error(self, category: str, error_id: str, context: Dict[str, Any] = None):
        """Show user-friendly error message"""
        
        if not STREAMLIT_AVAILABLE or not st:
            return
            
        message_config = UserFriendlyMessages.MESSAGES.get(
            category, 
            UserFriendlyMessages.MESSAGES[ExceptionCategory.UNKNOWN_ERROR]
        )
        
        with st.container():
            st.error(f"""
            **{message_config['title']}**
            
            {message_config['message']}
            
            *{message_config['action']}*
            
            🔍 **ID do Erro:** `{error_id}`
            """)
            
            # Show additional context in expander
            if context and hasattr(st, 'session_state') and st.session_state.get('show_debug', False):
                with st.expander("🔧 Detalhes Técnicos (Debug)"):
                    st.json(context)

def handle_exceptions(func: Callable = None, *, context: Dict[str, Any] = None, show_in_ui: bool = True):
    """
    Decorator to handle exceptions globally
    
    Args:
        func: Function to wrap
        context: Additional context for logging
        show_in_ui: Whether to show error in Streamlit UI
    """
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                handler = GlobalExceptionHandler()
                
                # Prepare context
                error_context = {
                    "function_name": f.__name__,
                    "args_count": len(args),
                    "kwargs": list(kwargs.keys()),
                    **(context or {})
                }
                
                # Log exception
                error_id, category = handler.log_exception(e, error_context)
                
                # Show in UI if requested
                if show_in_ui:
                    handler.show_user_error(category, error_id, error_context)
                    return None
                else:
                    # Re-raise for programmatic handling
                    raise
                    
        return wrapper
    
    # Support both @handle_exceptions and @handle_exceptions()
    if func is None:
        return decorator
    else:
        return decorator(func)

# Global handler instance
global_handler = GlobalExceptionHandler()

def setup_streamlit_exception_handling():
    """Setup global exception handling for Streamlit"""
    
    if not STREAMLIT_AVAILABLE or not st:
        return
    
    # Enable debug mode with query parameter
    try:
