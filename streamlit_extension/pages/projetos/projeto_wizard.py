# streamlit_extension/pages/projetos/projeto_wizard.py
"""
🧙‍♂️ Project Wizard - Multi-Step Implementation

This module implements a true multi-step wizard following official Streamlit patterns
as outlined in the taxonomia.txt instructions. It provides a "Third Way" approach
that combines both form and step-by-step modes for Product Vision creation.

Key Features:
    - Session state-based navigation
    - Multi-step wizard with Next/Back buttons  
    - Toggle between Form and Steps mode
    - Real-time summary sidebar
    - Integration with existing Clean Architecture
    - AI-powered refinement capabilities

Architecture:
    This wizard coordinates between UI layer and business logic while maintaining
    clean architecture principles. It uses the new _pv_state.py helpers for
    robust state management.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import streamlit as st

logger = logging.getLogger(__name__)


def _wiz_key(name: str, step: int | str = "global") -> str:
    """Gera chave única para elementos do wizard para evitar IDs duplicados."""
    session_id = st.session_state.get("session_id", "anon")
    return f"wiz::{session_id}::s{step}::{name}"

# --- Authentication layer ---
try:
    from streamlit_extension.auth.middleware import init_protected_page, require_auth
except ImportError:
    def init_protected_page(title: str, *, layout: str = "wide") -> None:
        st.set_page_config(page_title=title, layout=layout)

    def require_auth(role: Optional[str] = None):
        def _decorator(fn):
            def _inner(*args, **kwargs):
                return fn(*args, **kwargs)
            return _inner
        return _decorator

# --- Import Product Vision step implementation ---
from .steps.product_vision_step import render_product_vision_with_toggle
from .steps._pv_state import init_pv_state

# Wizard step definitions - Generic project structure
WIZARD_STEPS = {
    1: "roteiro",
    2: "capitulos", 
    3: "historias",
    4: "tarefas"
}

def get_step_name(step_num: int) -> str:
    """Get human-readable step name from step number."""
    step_key = WIZARD_STEPS.get(step_num, "unknown")
    
    # Mapeamento para macro fases genéricas
    step_names = {
        "roteiro": "Roteiro",
        "capitulos": "Capítulos", 
        "historias": "Histórias",
        "tarefas": "Tarefas"
    }
    
    return step_names.get(step_key, step_key)


def init_wizard_state() -> None:
    """Initialize wizard session state following official Streamlit pattern."""
    # Current step tracking (following official blog pattern)
    if 'wizard_current_step' not in st.session_state:
        st.session_state.wizard_current_step = 1
        
    # Initialize Product Vision state
    init_pv_state(st.session_state)


def set_wizard_step(action: str, step: Optional[int] = None) -> None:
    """
    Navigate between wizard steps following official Streamlit pattern.
    
    Args:
        action: 'Next', 'Back', or 'Jump'
        step: Target step number (only for 'Jump' action)
    """
    if action == 'Next':
        st.session_state.wizard_current_step += 1
    elif action == 'Back':
        st.session_state.wizard_current_step -= 1  
    elif action == 'Jump' and step is not None:
        st.session_state.wizard_current_step = step
    
    # Clamp to valid range
    max_step = max(WIZARD_STEPS.keys())
    min_step = min(WIZARD_STEPS.keys())
    st.session_state.wizard_current_step = max(min_step, min(st.session_state.wizard_current_step, max_step))


def render_wizard_header() -> None:
    """Render wizard header with step indicators."""
    # Título removido - já existe um título principal na página
    
    # Step indicators (visual progress)
    current_step = st.session_state.wizard_current_step
    max_steps = len(WIZARD_STEPS)
    
    # Progress bar
    progress = current_step / max_steps
    st.progress(progress)
    
    # Navigation by individual questions
    nav_cols = st.columns(max_steps)
    for i, (step_num, step_name) in enumerate(WIZARD_STEPS.items()):
        with nav_cols[i]:
            # Determine button state
            if step_num == current_step:
                button_type = "primary"
                is_disabled = False
            elif step_num < current_step:
                button_type = "secondary"
                is_disabled = False
            else:
                button_type = "secondary"
                is_disabled = True
            
            # Question as button label
            question_text = get_step_name(step_num)
            
            if st.button(
                question_text,
                type=button_type,
                disabled=is_disabled,
                key=_wiz_key(f"question_{step_num}", step_num),
                help=f"{'Pergunta atual' if step_num == current_step else 'Ir para esta pergunta' if not is_disabled else 'Pergunta não disponível'}",
                use_container_width=True
            ):
                if not is_disabled and step_num != current_step:
                    set_wizard_step('Jump', step_num)
                    st.rerun()


def render_wizard_navigation() -> None:
    """Render wizard navigation buttons (Back/Next)."""
    # Navigation removed - using only macro phase buttons


def render_current_step() -> None:
    """Render the current wizard step content."""
    current_step = st.session_state.wizard_current_step
    step_key = WIZARD_STEPS.get(current_step, "unknown")
    
    # Route to appropriate step renderer based on macro phases
    if step_key == "roteiro":
        # Phase 1: All 5 questions are handled by the product vision component
        render_product_vision_with_toggle()
    elif step_key == "capitulos":
        # Phase 2: Chapters/Epics (future)
        st.info("🚧 **Capítulos** - Estruturação em grandes blocos")
        st.markdown("Esta fase permitirá organizar seu projeto em capítulos ou módulos principais.")
        st.write("📚 Em desenvolvimento...")
    elif step_key == "historias":
        # Phase 3: Stories (future)
        st.info("🚧 **Histórias** - Detalhamento das funcionalidades")
        st.markdown("Esta fase permitirá criar narrativas detalhadas para cada funcionalidade.")
        st.write("📖 Em desenvolvimento...")
    elif step_key == "tarefas":
        # Phase 4: Tasks (future)
        st.info("🚧 **Tarefas** - Quebra operacional")
        st.markdown("Esta fase permitirá dividir o projeto em tarefas executáveis específicas.")
        st.write("✅ Em desenvolvimento...")
    else:
        # Placeholder for unknown steps
        step_name = get_step_name(current_step)
        st.info(f"🚧 Fase '{step_name}' em desenvolvimento")
        st.markdown(f"**Fase {current_step}:** {step_name}")


@require_auth()
def render_projeto_wizard_page() -> Dict[str, Any]:
    """
    Main wizard page renderer following official Streamlit multi-step pattern.
    
    This function implements the complete wizard workflow using session state
    for navigation and the "Third Way" approach for Product Vision input.
    
    Returns:
        Dict with page status and metadata
    """
    # Page configuration
    st.set_page_config(
        page_title="Assistente de Projetos", 
        layout="wide"
    )
    
    try:
        # Initialize wizard state
        init_wizard_state()
        
        # Protected page initialization
        init_protected_page("Assistente de Projetos")
        
        # Main wizard layout
        with st.container():
            # Header with step indicators
            render_wizard_header()
            
            # Current step content
            render_current_step()
            
            # Navigation controls
            render_wizard_navigation()
        
        # Debug info (only in development)
        with st.expander("🔧 Debug Info", expanded=False):
            st.json({
                "current_step": st.session_state.wizard_current_step,
                "step_name": get_step_name(st.session_state.wizard_current_step),
                "pv_mode": getattr(st.session_state, 'pv_mode', 'not_set'),
                "pv_step_idx": getattr(st.session_state, 'pv_step_idx', 'not_set'),
                "session_keys": list(st.session_state.keys())
            })
        
        logger.info(f"✅ Wizard page rendered successfully - Step {st.session_state.wizard_current_step}")
        return {
            "status": "success", 
            "page": "projeto_wizard",
            "current_step": st.session_state.wizard_current_step
        }
        
    except Exception as e:
        logger.error(f"❌ Error rendering wizard page: {e}")
        st.error("⚠️ Erro ao carregar assistente de projetos")
        st.exception(e)
        return {
            "status": "error", 
            "error": str(e), 
            "page": "projeto_wizard"
        }


# Support direct execution
if __name__ == "__main__":
    render_projeto_wizard_page()