# streamlit_extension/pages/projetos/steps/product_vision_step.py
from __future__ import annotations
import streamlit as st
from typing import Dict, Any, List, Optional
from src.ia.services.vision_refine_service import VisionRefineService

# Import the new state management helpers
from ._pv_state import (
    init_pv_state,
    PV_FIELDS,
    set_pv_mode,
    next_step,
    prev_step,
    constraints_to_text,
    constraints_from_text,
)

# Keep for backward compatibility with existing code
FIELDS = [field[0] for field in PV_FIELDS]
LABELS = {field[0]: field[1] for field in PV_FIELDS}
HELP = {
    "constraints": "Ex.: orçamento limitado\natender LGPD\nlançar em 90 dias",
}

def _all_fields_filled(pv_data: Dict[str, Any]) -> bool:
    """Check if all Product Vision fields are properly filled."""
    for field_key, _ in PV_FIELDS:
        v = pv_data.get(field_key)
        if field_key == "constraints":
            if not isinstance(v, list) or len([x for x in v if isinstance(x, str) and x.strip()]) == 0:
                return False
        else:
            if not isinstance(v, str) or not v.strip():
                return False
    return True


def render_product_vision_with_toggle(
    controller=None, project_id: Optional[int] = None
) -> None:
    """Render Product Vision step with form/steps toggle (Third Way approach)."""
    
    # Initialize state management
    init_pv_state(st.session_state)
    
    st.subheader("🎯 Product Vision")
    
    # Mode toggle (form vs steps)
    col1, col2 = st.columns([3, 1])
    with col2:
        mode = st.radio(
            "Modo de preenchimento",
            options=["form", "steps"],
            index=0 if st.session_state.pv_mode == "form" else 1,
            horizontal=False,
            format_func=lambda x: "📝 Formulário" if x == "form" else "👣 Passo a passo",
            key="pv_mode_radio",
        )
        set_pv_mode(st.session_state, mode)
    
    # Main content area with 2 columns
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        if st.session_state.pv_mode == "form":
            # Form mode: all fields at once
            _render_form_mode()
        else:
            # Steps mode: one field at a time
            _render_steps_mode()
    
    with right_col:
        _render_summary(controller)


def _render_form_mode() -> None:
    """Render all Product Vision fields in a single form."""
    with st.form("pv_form_mode", clear_on_submit=False):
        # Render all fields
        for field_key, field_label in PV_FIELDS:
            if field_key == "constraints":
                # Special handling for constraints (list)
                constraints_text = st.text_area(
                    field_label,
                    constraints_to_text(st.session_state.pv.get(field_key, [])),
                    height=100,
                    help=HELP.get(field_key),
                    key=f"form_{field_key}",
                )
                st.session_state.pv[field_key] = constraints_from_text(constraints_text)
            elif field_key in ["problem_statement", "value_proposition"]:
                # Text areas for longer fields
                st.session_state.pv[field_key] = st.text_area(
                    field_label,
                    st.session_state.pv.get(field_key, ""),
                    height=100,
                    key=f"form_{field_key}",
                )
            else:
                # Text inputs for shorter fields
                st.session_state.pv[field_key] = st.text_input(
                    field_label,
                    st.session_state.pv.get(field_key, ""),
                    key=f"form_{field_key}",
                )
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            refine_all = st.form_submit_button("✨ Refinar Tudo", use_container_width=True)
        with col2:
            save_draft = st.form_submit_button("💾 Salvar Rascunho", use_container_width=True)
        with col3:
            validate_form = st.form_submit_button("✅ Validar", use_container_width=True)
    
    # Handle button actions
    if refine_all:
        _handle_refine_all()
    if save_draft:
        st.info("💾 Rascunho salvo no estado da sessão")
    if validate_form:
        if _all_fields_filled(st.session_state.pv):
            st.success("✅ Todos os campos estão preenchidos corretamente!")
        else:
            st.warning("⚠️ Por favor, preencha todos os campos obrigatórios.")


def _render_steps_mode() -> None:
    """Render one Product Vision field at a time with navigation."""
    idx = st.session_state.pv_step_idx
    field_key, field_label = PV_FIELDS[idx]
    
    # Progress indicator
    st.progress((idx + 1) / len(PV_FIELDS))
    st.caption(f"Passo {idx + 1} de {len(PV_FIELDS)}")
    
    # Render current field
    if field_key == "constraints":
        # Special handling for constraints
        constraints_text = st.text_area(
            field_label,
            constraints_to_text(st.session_state.pv.get(field_key, [])),
            height=150,
            help=HELP.get(field_key),
            key=f"step_{field_key}",
        )
        st.session_state.pv[field_key] = constraints_from_text(constraints_text)
    elif field_key in ["problem_statement", "value_proposition"]:
        # Text areas for longer fields
        st.session_state.pv[field_key] = st.text_area(
            field_label,
            st.session_state.pv.get(field_key, ""),
            height=150,
            key=f"step_{field_key}",
        )
    else:
        # Text inputs for shorter fields
        st.session_state.pv[field_key] = st.text_input(
            field_label,
            st.session_state.pv.get(field_key, ""),
            key=f"step_{field_key}",
        )
    
    # Navigation buttons
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button("⬅ Anterior", disabled=(idx == 0), use_container_width=True):
            prev_step(st.session_state)
            st.rerun()
    with nav_col2:
        if st.button("Próximo ➡", disabled=(idx >= len(PV_FIELDS) - 1), use_container_width=True):
            next_step(st.session_state)
            st.rerun()
    with nav_col3:
        if st.button("✨ Refinar este campo", use_container_width=True):
            _handle_refine_field(field_key)


def _render_summary(controller) -> None:
    """Render Product Vision summary in the sidebar."""
    st.subheader("📋 Resumo")
    
    # Check completion status
    is_complete = _all_fields_filled(st.session_state.pv)
    if is_complete:
        st.success("✅ Completo")
    else:
        st.warning("⏳ Em progresso")
    
    # Display summary
    for field_key, field_label in PV_FIELDS:
        value = st.session_state.pv.get(field_key, "")
        if field_key == "constraints":
            if value:
                st.markdown(f"**{field_label}:**")
                for constraint in value:
                    st.markdown(f"  • {constraint}")
            else:
                st.markdown(f"**{field_label}:** _vazio_")
        else:
            display_value = value if value else "_vazio_"
            if len(str(display_value)) > 100:
                display_value = str(display_value)[:100] + "..."
            st.markdown(f"**{field_label}:** {display_value}")


def _handle_refine_all() -> None:
    """Handle refinement of all Product Vision fields."""
    if not _all_fields_filled(st.session_state.pv):
        st.warning("⚠️ Para refinar com IA, preencha todos os campos primeiro.")
        return
    
    with st.spinner("🤖 Refinando com IA..."):
        try:
            service = VisionRefineService()
            result = service.refine(st.session_state.pv)
            
            # Apply refinements
            for field_key, _ in PV_FIELDS:
                if field_key in result:
                    if field_key == "constraints" and isinstance(result[field_key], list):
                        st.session_state.pv[field_key] = [
                            c for c in result[field_key] 
                            if isinstance(c, str) and c.strip()
                        ]
                    elif isinstance(result[field_key], str) and result[field_key].strip():
                        st.session_state.pv[field_key] = result[field_key].strip()
            
            st.success("✨ Refinamento aplicado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao refinar: {e}")


def _handle_refine_field(field_key: str) -> None:
    """Handle refinement of a single Product Vision field."""
    current_value = st.session_state.pv.get(field_key)
    
    # Check if field has content
    if field_key == "constraints":
        if not current_value:
            st.warning(f"⚠️ Preencha o campo antes de refinar.")
            return
    elif not current_value or not str(current_value).strip():
        st.warning(f"⚠️ Preencha o campo antes de refinar.")
        return
    
    with st.spinner(f"🤖 Refinando {PV_FIELDS[st.session_state.pv_step_idx][1]}..."):
        try:
            service = VisionRefineService()
            # Create partial payload with only this field
            partial_payload = {field_key: current_value}
            result = service.refine(partial_payload)
            
            if field_key in result:
                if field_key == "constraints" and isinstance(result[field_key], list):
                    st.session_state.pv[field_key] = [
                        c for c in result[field_key]
                        if isinstance(c, str) and c.strip()
                    ]
                elif isinstance(result[field_key], str) and result[field_key].strip():
                    st.session_state.pv[field_key] = result[field_key].strip()
                
                st.success(f"✨ Campo refinado!")
                st.rerun()
            else:
                st.info("ℹ️ Nenhuma sugestão de refinamento disponível.")
        except Exception as e:
            st.error(f"❌ Erro ao refinar: {e}")


# ========== Backward compatibility API ==========
def render_step(ctx: Dict[str, Any]) -> None:
    """Legacy API for backward compatibility."""
    # Map old context to new session state
    if "data" in ctx and "product_vision" in ctx["data"]:
        old_data = ctx["data"]["product_vision"]
        # Initialize session state if needed
        init_pv_state(st.session_state)
        # Copy old data to session state
        for key in old_data:
            if key in [field[0] for field in PV_FIELDS]:
                st.session_state.pv[key] = old_data[key]
    
    # Render using new approach
    render_product_vision_with_toggle()


def validate(ctx: Dict[str, Any]) -> tuple[bool, str | None]:
    """Legacy validation API for backward compatibility."""
    # Use session state if available
    if hasattr(st, 'session_state') and 'pv' in st.session_state:
        if not _all_fields_filled(st.session_state.pv):
            return False, "Todos os campos são obrigatórios para a Product Vision."
        return True, None
    
    # Fallback to old context
    if "data" in ctx and "product_vision" in ctx["data"]:
        step = ctx["data"]["product_vision"]
        if not _all_fields_filled(step):
            return False, "Todos os campos são obrigatórios para a Product Vision."
    return True, None


def get_summary(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy summary API for backward compatibility."""
    # Use session state if available
    if hasattr(st, 'session_state') and 'pv' in st.session_state:
        return {
            field_label: st.session_state.pv.get(field_key, "" if field_key != "constraints" else [])
            for field_key, field_label in PV_FIELDS
        }
    
    # Fallback to old context
    if "data" in ctx and "product_vision" in ctx["data"]:
        step = ctx["data"]["product_vision"]
        return {
            "Declaração de Visão": step.get("vision_statement", ""),
            "Problema a Resolver": step.get("problem_statement", ""),
            "Público-alvo": step.get("target_audience", ""),
            "Proposta de Valor": step.get("value_proposition", ""),
            "Restrições": step.get("constraints", []),
        }
    
    return {}