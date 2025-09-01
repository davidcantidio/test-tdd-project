# streamlit_extension/pages/projetos/steps/product_vision_step.py
from __future__ import annotations
import streamlit as st
from typing import Dict, Any, Optional

# Serviço de IA — Sistema real com fallback para mock
try:
    from src.ia.services.vision_refine_service import VisionRefineService as RealVisionService
    from src.ia.agents.agno_agent import VisionRefinerAgent, ProductVisionDTO
    
    # Criar instância do agente real com gpt-5-nano
    _agent = VisionRefinerAgent(model_id="gpt-5-nano")
    
    # Adapter para compatibilizar VisionRefinerAgent com VisionRefineService
    class AgentAdapter:
        def __init__(self, agent):
            self.agent = agent
        
        def run(self, payload):
            # VisionRefineService espera run(), mas VisionRefinerAgent tem refine()
            result = self.agent.refine(payload)
            
            # Agno retorna RunResponse, extrair o content
            if hasattr(result, 'content'):
                actual_result = result.content
                if isinstance(actual_result, ProductVisionDTO):
                    # Usar model_dump() em vez de dict() depreciado
                    return actual_result.model_dump()
                return actual_result
            
            # Fallback para compatibilidade
            if isinstance(result, ProductVisionDTO):
                return result.model_dump()
            return result
    
    # Criar adapter
    _adapted_agent = AgentAdapter(_agent)
    
    # Wrapper para compatibilidade com código existente
    class VisionRefineService:
        def __init__(self):
            self.service = RealVisionService(_adapted_agent)
        
        def refine(self, payload):
            return self.service.refine(payload)
    
    print("✅ Sistema real de IA ativado com gpt-5-nano")
    
except Exception as e:
    # Fallback para mock se houver problema com sistema real
    from .mock_refiner import MockVisionRefineService as VisionRefineService
    print(f"⚠️ Usando mock devido a: {e}")

# State helpers (ficam no MESMO pacote "steps")
from ._pv_state import (
    init_pv_state,
    PV_FIELDS,
    set_pv_mode,
    next_step,
    prev_step,
    constraints_to_text,
    constraints_from_text,
    is_review_step,
    total_steps,
)

# Backward-compat
FIELDS = [field[0] for field in PV_FIELDS]
LABELS = {field[0]: field[1] for field in PV_FIELDS}
HELP = {
    "constraints": "Ex.: orçamento limitado\natender LGPD\nlançar em 90 dias",
}


# -----------------------------
# Validadores simples
# -----------------------------
def _all_fields_filled(pv_data: Dict[str, Any]) -> bool:
    """Verifica se todos os campos do Product Vision estão preenchidos corretamente."""
    for field_key, _ in PV_FIELDS:
        v = pv_data.get(field_key)
        if field_key == "constraints":
            if not isinstance(v, list) or len([x for x in v if isinstance(x, str) and x.strip()]) == 0:
                return False
        else:
            if not isinstance(v, str) or not v.strip():
                return False
    return True


# -----------------------------
# Componente principal (render)
# -----------------------------
def render_product_vision_with_toggle(
    controller=None, project_id: Optional[int] = None
) -> None:
    """Renderiza o passo Product Vision com toggle (Third Way) e revisão final."""
    init_pv_state(st.session_state)

    st.subheader("🎯 Product Vision")

    # Toggle de modo (default já é steps via init_pv_state)
    col1, col2 = st.columns([3, 1])
    with col2:
        mode = st.radio(
            "Modo de preenchimento",
            options=["steps", "form"],  # coloca steps primeiro (reforça o default)
            index=0 if st.session_state.pv_mode == "steps" else 1,
            horizontal=False,
            format_func=lambda x: "👣 Passo a passo" if x == "steps" else "📝 Formulário",
            key="pv_mode_radio",
        )
        set_pv_mode(st.session_state, mode)

    # Área principal: conteúdo + resumo
    left_col, right_col = st.columns([2, 1])

    with left_col:
        if st.session_state.pv_mode == "form":
            _render_form_mode()  # IA global (“Refinar Tudo”)
        else:
            _render_steps_mode()  # IA por campo + revisão final com form

    with right_col:
        _render_summary()


# -----------------------------
# Formulário completo (IA global)
# -----------------------------
def _render_form_mode() -> None:
    """Renderiza todos os campos de uma vez (formulário completo)."""
    with st.form("pv_form_mode", clear_on_submit=False):
        for field_key, field_label in PV_FIELDS:
            if field_key == "constraints":
                constraints_text = st.text_area(
                    field_label,
                    constraints_to_text(st.session_state.pv.get(field_key, [])),
                    height=100,
                    help=HELP.get(field_key),
                    key=f"form_{field_key}",
                )
                st.session_state.pv[field_key] = constraints_from_text(constraints_text)
            elif field_key in ["problem_statement", "value_proposition"]:
                st.session_state.pv[field_key] = st.text_area(
                    field_label,
                    st.session_state.pv.get(field_key, ""),
                    height=100,
                    key=f"form_{field_key}",
                )
            else:
                st.session_state.pv[field_key] = st.text_input(
                    field_label,
                    st.session_state.pv.get(field_key, ""),
                    key=f"form_{field_key}",
                )

        col1, col2, col3 = st.columns(3)
        with col1:
            refine_all = st.form_submit_button("✨ Refinar Tudo", use_container_width=True)
        with col2:
            save_draft = st.form_submit_button("💾 Salvar Rascunho", use_container_width=True)
        with col3:
            validate_form = st.form_submit_button("✅ Validar", use_container_width=True)

    if refine_all:
        _handle_refine_all()
    if save_draft:
        st.info("💾 Rascunho salvo no estado da sessão")
    if validate_form:
        if _all_fields_filled(st.session_state.pv):
            st.success("✅ Todos os campos estão preenchidos corretamente!")
        else:
            st.warning("⚠️ Por favor, preencha todos os campos obrigatórios.")


# -----------------------------
# Step-by-step (IA por campo) + revisão final
# -----------------------------
def _render_steps_mode() -> None:
    """Renderiza um campo por vez; último passo = revisão final (form completo)."""
    idx = st.session_state.pv_step_idx
    total = total_steps()  # len(PV_FIELDS) + 1 (revisão final)

    st.progress((idx + 1) / total)
    st.caption(f"Passo {idx + 1} de {total}")

    # Passo extra de revisão: formulário completo (com IA global)
    if is_review_step(st.session_state):
        st.markdown("### 🧾 Revisão final — formulário completo")
        _render_form_mode()

        nav_col1, nav_col2 = st.columns([1, 1])
        with nav_col1:
            if st.button("⬅ Anterior", use_container_width=True):
                prev_step(st.session_state)
                st.rerun()
        with nav_col2:
            st.success("Pronto! Revise o formulário completo. Você pode voltar, salvar/validar ou alternar para ‘Formulário’.")
        return

    # Campo atual no fluxo step-by-step
    field_key, field_label = PV_FIELDS[idx]

    if field_key == "constraints":
        constraints_text = st.text_area(
            field_label,
            constraints_to_text(st.session_state.pv.get(field_key, [])),
            height=150,
            help=HELP.get(field_key),
            key=f"step_{field_key}",
        )
        st.session_state.pv[field_key] = constraints_from_text(constraints_text)
    elif field_key in ["problem_statement", "value_proposition"]:
        st.session_state.pv[field_key] = st.text_area(
            field_label,
            st.session_state.pv.get(field_key, ""),
            height=150,
            key=f"step_{field_key}",
        )
    else:
        st.session_state.pv[field_key] = st.text_input(
            field_label,
            st.session_state.pv.get(field_key, ""),
            key=f"step_{field_key}",
        )

    # Navegação + refino por campo
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button("⬅ Anterior", disabled=(idx == 0), use_container_width=True):
            prev_step(st.session_state)
            st.rerun()
    with nav_col2:
        if st.button("Próximo ➡", use_container_width=True):
            next_step(st.session_state)
            st.rerun()
    with nav_col3:
        if st.button("✨ Refinar este campo", use_container_width=True):
            _handle_refine_field(field_key)


# -----------------------------
# Resumo lateral
# -----------------------------
def _render_summary() -> None:
    """Renderiza o resumo do Product Vision."""
    st.subheader("📋 Resumo")

    is_complete = _all_fields_filled(st.session_state.pv)
    if is_complete:
        st.success("✅ Completo")
    else:
        st.warning("⏳ Em progresso")

    for field_key, field_label in PV_FIELDS:
        value = st.session_state.pv.get(field_key, "")
        if field_key == "constraints":
            if value:
                st.markdown(f"**{field_label}:**")
                for constraint in value:
                    st.markdown(f"• {constraint}")
            else:
                st.markdown(f"**{field_label}:** _vazio_")
        else:
            display_value = value if value else "_vazio_"
            s = str(display_value)
            if len(s) > 160:
                s = s[:160] + "…"
            st.markdown(f"**{field_label}:** {s}")


# -----------------------------
# Handlers de IA
# -----------------------------
def _handle_refine_all() -> None:
    """Refina todos os campos (IA global). Requer todos os campos preenchidos."""
    if not _all_fields_filled(st.session_state.pv):
        st.warning("⚠️ Para refinar com IA, preencha todos os campos primeiro.")
        return

    with st.status("🤖 Refinando com IA...", expanded=True) as status:
        try:
            status.update(label="📋 Validando campos...", state="running")
            status.update(label="🔧 Preparando dados para IA...", state="running")
            service = VisionRefineService()

            status.update(label="✨ Refinando conteúdo...", state="running")
            result = service.refine(st.session_state.pv)

            status.update(label="📝 Aplicando melhorias...", state="running")
            fields_updated = 0

            for field_key, _ in PV_FIELDS:
                if field_key in result:
                    if field_key == "constraints" and isinstance(result[field_key], list):
                        st.session_state.pv[field_key] = [
                            c for c in result[field_key]
                            if isinstance(c, str) and c.strip()
                        ]
                        fields_updated += 1
                    elif isinstance(result[field_key], str) and result[field_key].strip():
                        st.session_state.pv[field_key] = result[field_key].strip()
                        fields_updated += 1

            status.update(
                label=f"✅ Refinamento concluído! {fields_updated} campos aprimorados.",
                state="complete"
            )
            st.success(f"✨ {fields_updated} campos foram refinados com sucesso!")
            st.rerun()
        except Exception as e:
            status.update(label="❌ Erro no refinamento", state="error")
            st.error(f"❌ Erro ao refinar: {e}")


def _handle_refine_field(field_key: str) -> None:
    """Refina apenas um campo (IA por campo) com contexto completo."""
    current_value = st.session_state.pv.get(field_key)

    if field_key == "constraints":
        if not current_value:
            st.warning("⚠️ Preencha o campo antes de refinar.")
            return
    elif not current_value or not str(current_value).strip():
        st.warning("⚠️ Preencha o campo antes de refinar.")
        return

    field_label = next((label for key, label in PV_FIELDS if key == field_key), field_key)

    with st.status(f"🤖 Refinando campo: {field_label}", expanded=True) as status:
        try:
            status.update(label=f"📋 Analisando {field_label}...", state="running")

            # Payload completo para fornecer contexto ao refiner
            full_payload: Dict[str, Any] = {}
            for key, _ in PV_FIELDS:
                value = st.session_state.pv.get(key)
                if key == "constraints":
                    full_payload[key] = value if value else []
                else:
                    full_payload[key] = value if value else ""

            status.update(label=f"✨ Aplicando IA ao campo {field_label}...", state="running")
            service = VisionRefineService()
            result = service.refine(full_payload)

            status.update(label=f"📝 Atualizando {field_label}...", state="running")

            if field_key in result:
                old_value = st.session_state.pv[field_key]

                if field_key == "constraints" and isinstance(result[field_key], list):
                    new_value = [
                        c for c in result[field_key]
                        if isinstance(c, str) and c.strip()
                    ]
                    st.session_state.pv[field_key] = new_value
                    changed = old_value != new_value
                elif isinstance(result[field_key], str) and result[field_key].strip():
                    new_value = result[field_key].strip()
                    st.session_state.pv[field_key] = new_value
                    changed = old_value != new_value
                else:
                    changed = False

                if changed:
                    status.update(
                        label=f"✅ Campo {field_label} refinado com sucesso!",
                        state="complete"
                    )
                    st.success(f"✨ {field_label} foi aprimorado!")
                    st.rerun()
                else:
                    status.update(
                        label=f"ℹ️ Campo {field_label} já está otimizado",
                        state="complete"
                    )
                    st.info("ℹ️ O campo já está em sua melhor forma.")
            else:
                status.update(
                    label=f"ℹ️ Sem sugestões para {field_label}",
                    state="complete"
                )
                st.info("ℹ️ Nenhuma sugestão de refinamento disponível.")
        except Exception as e:
            status.update(label=f"❌ Erro ao refinar {field_label}", state="error")
            st.error(f"❌ Erro ao refinar: {e}")


# -----------------------------
# API legado (compat)
# -----------------------------
def render_step(ctx: Dict[str, Any]) -> None:
    """API legada para compatibilidade."""
    if "data" in ctx and "product_vision" in ctx["data"]:
        old_data = ctx["data"]["product_vision"]
        init_pv_state(st.session_state)
        for key in old_data:
            if key in [field[0] for field in PV_FIELDS]:
                st.session_state.pv[key] = old_data[key]
    render_product_vision_with_toggle()


def validate(ctx: Dict[str, Any]) -> tuple[bool, str | None]:
    """Validação legada (compat)."""
    if hasattr(st, "session_state") and "pv" in st.session_state:
        if not _all_fields_filled(st.session_state.pv):
            return False, "Todos os campos são obrigatórios para a Product Vision."
        return True, None

    if "data" in ctx and "product_vision" in ctx["data"]:
        step = ctx["data"]["product_vision"]
        if not _all_fields_filled(step):
            return False, "Todos os campos são obrigatórios para a Product Vision."
    return True, None


def get_summary(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Resumo legada (compat)."""
    if hasattr(st, "session_state") and "pv" in st.session_state:
        return {
            field_label: st.session_state.pv.get(field_key, "" if field_key != "constraints" else [])
            for field_key, field_label in PV_FIELDS
        }

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


__all__ = [
    "render_product_vision_with_toggle",
    "render_step",
    "validate",
    "get_summary",
]
