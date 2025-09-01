# streamlit_extension/pages/projetos/steps/product_vision_step.py
from __future__ import annotations

from typing import Dict, Any, Optional

import streamlit as st


def _wiz_key(name: str, step: int | str = "pv") -> str:
    """Gera chave única para elementos do product vision para evitar IDs duplicados."""
    session_id = st.session_state.get("session_id", "anon")
    return f"pv::{session_id}::s{step}::{name}"

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
    
    # Refinador para campo individual com IA real
    class SingleFieldRealRefiner:
        """Refinador de campo individual para IA real."""
        
        def __init__(self, vision_agent):
            self.vision_agent = vision_agent
        
        def refine_field(self, field_key: str, field_value: Any, context: Dict[str, Any]) -> Any:
            """
            Refina um campo específico usando IA real.
            
            Args:
                field_key: chave do campo a refinar
                field_value: valor atual do campo  
                context: payload completo com demais campos (podem estar vazios)
                
            Returns:
                Valor refinado do campo
            """
            try:
                # Prompt especializado para refinamento individual
                field_labels = {
                    "vision_statement": "Visão do Produto",
                    "problem_statement": "Problema a Resolver", 
                    "target_audience": "Público-Alvo",
                    "value_proposition": "Proposta de Valor",
                    "constraints": "Restrições"
                }
                
                field_label = field_labels.get(field_key, field_key)
                
                # Preparar contexto disponível
                context_info = []
                for key, value in context.items():
                    if key != field_key and value:
                        if isinstance(value, list) and value:
                            context_info.append(f"- {field_labels.get(key, key)}: {', '.join(value)}")
                        elif isinstance(value, str) and value.strip():
                            context_info.append(f"- {field_labels.get(key, key)}: {value.strip()}")
                
                context_text = "\\n".join(context_info) if context_info else "Nenhum contexto adicional disponível."
                
                # Prompt focado no campo específico
                prompt = f'''Você é um especialista em Product Management.

Preciso que você refine o campo "{field_label}" de um produto.

Valor atual do campo: "{field_value}"

Contexto disponível:
{context_text}

Por favor, melhore APENAS o campo "{field_label}", mantendo o significado original mas tornando-o mais claro, profissional e impactante.

IMPORTANTE: 
- Retorne APENAS o valor refinado do campo, sem explicações
- Mantenha o escopo original 
- Se o campo já estiver bom, pode retornar o mesmo valor
- Use português brasileiro'''

                # Usar agente Agno diretamente (bypassa validação do VisionRefinerAgent)
                result = self.vision_agent.agent.run(prompt)
                
                # Extrair conteúdo da resposta
                if hasattr(result, 'content'):
                    content = result.content
                    
                    # Se o content for um ProductVisionDTO, é porque o agente ainda está usando o response_model
                    if hasattr(content, field_key):
                        # Extrair o campo específico do DTO
                        refined_content = getattr(content, field_key, field_value)
                    else:
                        # Content é string direta
                        refined_content = str(content).strip()
                        
                    # Limpar formatação
                    if isinstance(refined_content, str):
                        refined_content = refined_content.strip()
                        if refined_content.startswith('"') and refined_content.endswith('"'):
                            refined_content = refined_content[1:-1]
                            
                    return refined_content if refined_content else field_value
                
                return field_value
                
            except Exception as e:
                print(f"Erro no refinamento individual: {e}")
                return field_value
    
    # Criar refinador individual
    _single_field_refiner = SingleFieldRealRefiner(_agent)
    
    print("✅ Sistema real de IA ativado em main.py com gpt-5-nano")
    
except Exception as e:
    # Fallback para mock se houver problema com sistema real  
    from .mock_refiner import MockVisionRefineService as VisionRefineService, SingleFieldMockRefiner
    
    # Usar SingleFieldMockRefiner para compatibilidade
    _single_field_refiner = SingleFieldMockRefiner()
    
    print(f"⚠️ main.py usando mock devido a: {e}")

# State helpers
from .._pv_state import (
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

# ---------------------------------------------
# Utilidades locais (robustez e reutilização)
# ---------------------------------------------
def _get_refine_service() -> VisionRefineService:
    """Instancia única do serviço de refino (cache em session_state)."""
    key = "_pv_refine_service"
    if key not in st.session_state:
        st.session_state[key] = VisionRefineService()
    return st.session_state[key]


class _NoStatus:
    """Fallback quando st.status não existir (ex.: versões antigas/ambiente de teste)."""
    def update(self, **kwargs):  # compatibilidade com .update(label=..., state=...)
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _status_ctx(label: str, expanded: bool = True):
    """Context manager que usa st.status quando disponível, senão _NoStatus()."""
    if hasattr(st, "status"):
        return st.status(label, expanded=expanded)  # type: ignore[attr-defined]
    return _NoStatus()


def _is_nonempty_str(x: Any) -> bool:
    return isinstance(x, str) and x.strip() != ""


def _sanitize_constraints(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    for c in value:
        if isinstance(c, str):
            s = c.strip()
            if s:
                cleaned.append(s)
    return cleaned


# ---------------------------------------------
# Validadores simples
# ---------------------------------------------
def _all_fields_filled(pv_data: Dict[str, Any]) -> bool:
    """Verifica se todos os campos do Product Vision estão preenchidos corretamente."""
    for field_key, _ in PV_FIELDS:
        v = pv_data.get(field_key)
        if field_key == "constraints":
            if len(_sanitize_constraints(v)) == 0:
                return False
        else:
            if not _is_nonempty_str(v):
                return False
    return True


# ---------------------------------------------
# Componente principal (render)
# ---------------------------------------------
def render_product_vision_with_toggle(
    controller=None, project_id: Optional[int] = None
) -> None:
    """
    Renderiza o passo Product Vision com o “Third Way”:
      - Modo steps (um campo por vez + revisão final)
      - Modo formulário (todos os campos)
    """
    init_pv_state(st.session_state)

    # Dynamic title for current macro phase
    current_wizard_step = getattr(st.session_state, 'wizard_current_step', 1)
    from ...projeto_wizard import get_step_name
    macro_phase = get_step_name(current_wizard_step)
    st.subheader(f"{current_wizard_step}. {macro_phase}")

    # Forçar fluxo: primeiro steps, depois form na revisão final
    set_pv_mode(st.session_state, "steps")

    # Área principal: conteúdo + resumo
    left_col, right_col = st.columns([2, 1])

    with left_col:
        if st.session_state.pv_mode == "form":
            _render_form_mode()   # IA global (“Refinar Tudo”)
        else:
            _render_steps_mode()  # IA por campo + revisão final

    with right_col:
        _render_summary()


# ---------------------------------------------
# Formulário completo (IA global)
# ---------------------------------------------
def _render_form_mode() -> None:
    """Renderiza todos os campos de uma vez (formulário completo)."""
    with st.form("pv_form_mode", clear_on_submit=False):
        for field_key, field_label in PV_FIELDS:
            if field_key == "constraints":
                constraints_text = st.text_area(
                    field_label,
                    constraints_to_text(st.session_state.pv.get(field_key, [])),
                    height=100,
                    help="Ex.: orçamento limitado\natender LGPD\nlançar em 90 dias",
                    key=f"form_{field_key}",
                )
                st.session_state.pv[field_key] = constraints_from_text(constraints_text)

            elif field_key in {"problem_statement", "value_proposition"}:
                st.session_state.pv[field_key] = st.text_area(
                    field_label,
                    st.session_state.pv.get(field_key, ""),
                    height=120,  # Mais vertical
                    key=f"form_{field_key}",
                )

            else:
                st.session_state.pv[field_key] = st.text_area(
                    field_label,
                    st.session_state.pv.get(field_key, ""),
                    height=80,  # Transformar text_input em text_area para ser mais vertical
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
        st.info("💾 Rascunho salvo no estado da sessão (memória).")

    if validate_form:
        if _all_fields_filled(st.session_state.pv):
            st.success("✅ Todos os campos estão preenchidos corretamente!")
        else:
            st.warning("⚠️ Por favor, preencha todos os campos obrigatórios.")


# ---------------------------------------------
# Step-by-step (IA por campo) + revisão final
# ---------------------------------------------
def _render_steps_mode() -> None:
    """Renderiza um campo por vez das 5 perguntas dentro da fase Roteiro."""
    idx = st.session_state.pv_step_idx
    total = total_steps()  # len(PV_FIELDS) + 1 (revisão final)

    st.progress((idx + 1) / total)
    st.caption(f"Pergunta {idx + 1} de {total}")

    # Passo extra de revisão: formulário completo (com IA global)
    if is_review_step(st.session_state):
        st.markdown("### 🧾 Revisão final — formulário completo")
        _render_form_mode()

        nav_col1, nav_col2 = st.columns([1, 1])
        with nav_col1:
            if st.button("⬅ Anterior", 
                        use_container_width=True,
                        key=_wiz_key("btn_anterior_review", "review")):
                prev_step(st.session_state)
                st.rerun()
        with nav_col2:
            st.success(
                "Revise o formulário completo. "
                "Você pode voltar, salvar/validar ou prosseguir para próxima fase."
            )
        return

    # Campo atual no fluxo step-by-step das 5 perguntas
    field_key, field_label = PV_FIELDS[idx]

    if field_key == "constraints":
        constraints_text = st.text_area(
            field_label,
            constraints_to_text(st.session_state.pv.get(field_key, [])),
            height=150,
            help="Ex.: orçamento limitado\natender LGPD\nlançar em 90 dias",
            key=f"roteiro_{field_key}",
        )
        st.session_state.pv[field_key] = constraints_from_text(constraints_text)

    elif field_key in {"problem_statement", "value_proposition"}:
        st.session_state.pv[field_key] = st.text_area(
            field_label,
            st.session_state.pv.get(field_key, ""),
            height=200,  # Mais vertical
            key=f"roteiro_{field_key}",
        )

    else:
        st.session_state.pv[field_key] = st.text_area(
            field_label,
            st.session_state.pv.get(field_key, ""),
            height=120,  # Transformar text_input em text_area para ser mais vertical
            key=f"roteiro_{field_key}",
        )

    # Navegação + refino por campo
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button("⬅ Anterior", 
                    disabled=(idx == 0), 
                    use_container_width=True,
                    key=_wiz_key("btn_anterior", idx)):
            prev_step(st.session_state)
            st.rerun()
    with nav_col2:
        if st.button("Próximo ➡", 
                    use_container_width=True,
                    key=_wiz_key("btn_proximo", idx)):
            next_step(st.session_state)
            st.rerun()
    with nav_col3:
        if st.button("✨ Refinar este campo", 
                    use_container_width=True,
                    key=_wiz_key("btn_refinar", idx)):
            _handle_refine_field(field_key)


# ---------------------------------------------
# Resumo lateral
# ---------------------------------------------
def _render_summary() -> None:
    """Renderiza o resumo do Product Vision."""
    st.subheader("📋 Resumo")

    if _all_fields_filled(st.session_state.pv):
        st.success("✅ Completo")
    else:
        st.warning("⏳ Em progresso")

    for field_key, field_label in PV_FIELDS:
        value = st.session_state.pv.get(field_key, "")
        if field_key == "constraints":
            items = _sanitize_constraints(value)
            if items:
                st.markdown(f"**{field_label}:**")
                for constraint in items:
                    st.markdown(f"- {constraint}")
            else:
                st.markdown(f"**{field_label}:** _vazio_")
        else:
            if _is_nonempty_str(value):
                # Mostrar texto completo, sem truncar
                st.markdown(f"**{field_label}:**")
                st.markdown(f"{value}")
            else:
                st.markdown(f"**{field_label}:** _vazio_")


# ---------------------------------------------
# Handlers de IA
# ---------------------------------------------
def _handle_refine_all() -> None:
    """Refina todos os campos (IA global). Requer todos os campos preenchidos."""
    if not _all_fields_filled(st.session_state.pv):
        st.warning("⚠️ Para refinar com IA, preencha todos os campos primeiro.")
        return

    service = _get_refine_service()
    with _status_ctx("🤖 Refinando com IA...", expanded=True) as status:
        try:
            # Etapas (se st.status disponível, o .update fará efeito)
            status.update(label="📋 Validando campos...", state="running")
            status.update(label="🔧 Preparando dados para IA...", state="running")

            status.update(label="✨ Refinando conteúdo...", state="running")
            result = service.refine(st.session_state.pv)

            status.update(label="📝 Aplicando melhorias...", state="running")
            fields_updated = 0

            for field_key, _ in PV_FIELDS:
                if field_key not in result:
                    continue

                if field_key == "constraints" and isinstance(result[field_key], list):
                    new_value = _sanitize_constraints(result[field_key])
                    st.session_state.pv[field_key] = new_value
                    fields_updated += 1
                elif _is_nonempty_str(result[field_key]):
                    st.session_state.pv[field_key] = result[field_key].strip()
                    fields_updated += 1

            status.update(
                label=f"✅ Refinamento concluído! {fields_updated} campos aprimorados.",
                state="complete",
            )
            st.success(f"✨ {fields_updated} campos foram refinados com sucesso!")
            st.rerun()
        except Exception as e:  # pragma: no cover - apenas UI
            status.update(label="❌ Erro no refinamento", state="error")
            st.error(f"❌ Erro ao refinar: {e}")


def _handle_refine_field(field_key: str) -> None:
    """Refina apenas um campo (IA por campo) com contexto completo."""
    current_value = st.session_state.pv.get(field_key)

    if field_key == "constraints":
        if len(_sanitize_constraints(current_value)) == 0:
            st.warning("⚠️ Preencha o campo antes de refinar.")
            return
    elif not _is_nonempty_str(current_value):
        st.warning("⚠️ Preencha o campo antes de refinar.")
        return

    field_label = next((label for key, label in PV_FIELDS if key == field_key), field_key)

    # Monta contexto completo (outros campos podem estar vazios)
    context: Dict[str, Any] = {}
    for key, _ in PV_FIELDS:
        if key == "constraints":
            context[key] = _sanitize_constraints(st.session_state.pv.get(key, []))
        else:
            context[key] = st.session_state.pv.get(key, "")

    with _status_ctx(f"🤖 Refinando campo: {field_label}", expanded=True) as status:
        try:
            status.update(label=f"📋 Analisando {field_label}...", state="running")
            status.update(label=f"✨ Aplicando IA ao campo {field_label}...", state="running")
            
            # Usar refinamento individual (não exige todos os campos preenchidos)
            refined_value = _single_field_refiner.refine_field(field_key, current_value, context)

            status.update(label=f"📝 Atualizando {field_label}...", state="running")

            if not refined_value or refined_value == current_value:
                status.update(label=f"ℹ️ Sem sugestões para {field_label}", state="complete")
                st.info("ℹ️ Nenhuma sugestão de refinamento disponível.")
                return

            old_value = st.session_state.pv.get(field_key)

            # Aplicar valor refinado
            changed = False
            if field_key == "constraints" and isinstance(refined_value, list):
                new_value = _sanitize_constraints(refined_value)
                st.session_state.pv[field_key] = new_value
                changed = new_value != _sanitize_constraints(old_value)
            elif _is_nonempty_str(refined_value):
                new_value = refined_value.strip()
                st.session_state.pv[field_key] = new_value
                changed = new_value != (old_value or "")

            if changed:
                status.update(label=f"✅ Campo {field_label} refinado com sucesso!", state="complete")
                st.success(f"✨ {field_label} foi aprimorado!")
                st.rerun()
            else:
                status.update(label=f"ℹ️ Campo {field_label} já está otimizado", state="complete")
                st.info("ℹ️ O campo já está em sua melhor forma.")
        except Exception as e:  # pragma: no cover - apenas UI
            status.update(label=f"❌ Erro ao refinar {field_label}", state="error")
            st.error(f"❌ Erro ao refinar: {e}")


# ---------------------------------------------
# API legada (compat)
# ---------------------------------------------
def render_step(ctx: Dict[str, Any]) -> None:
    """API legada para compatibilidade com chamadas antigas."""
    if "data" in ctx and "product_vision" in ctx["data"]:
        old = ctx["data"]["product_vision"]
        init_pv_state(st.session_state)
        for key in old:
            if any(key == k for k, _ in PV_FIELDS):
                st.session_state.pv[key] = old[key]
    render_product_vision_with_toggle()


def validate(ctx: Dict[str, Any]) -> tuple[bool, Optional[str]]:
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
    """Resumo legado (compat)."""
    if hasattr(st, "session_state") and "pv" in st.session_state:
        return {
            label: (st.session_state.pv.get(key, [] if key == "constraints" else ""))
            for key, label in PV_FIELDS
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
