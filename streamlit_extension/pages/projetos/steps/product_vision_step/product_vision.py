"""
Etapa: Roteiro → Product Vision (modo assistido por IA)

Este módulo desenha a tela onde você descreve a visão do produto
de forma simples e guiada. Ele oferece dois jeitos de preencher:
- Passo a passo (uma pergunta por vez, com ajuda da IA em cada campo)
- Formulário completo (todas as perguntas de uma vez, com botão de "Refinar tudo")

Objetivo para pessoas leigas: ajudar você a escrever um texto claro,
curto e objetivo sobre o produto — o que é, para quem é e qual problema
resolve — sem exigir termos técnicos. A IA apenas melhora a redação do
que você já escreveu; ela não inventa fatos novos.
"""
from __future__ import annotations

from typing import Dict, Any, Optional
import json
import os
from pathlib import Path
import logging

import streamlit as st

# Logger de módulo para mensagens de depuração e diagnóstico
logger = logging.getLogger(__name__)


def _wiz_key(name: str, step: int | str = "pv") -> str:
    """Gera uma chave única e estável para componentes de tela.

    Em termos simples: o Streamlit precisa de uma "etiqueta" única para
    lembrar o estado de cada botão/campo. Esta função cria essa etiqueta
    usando o ID da sessão e o nome do componente.
    """
    session_id = st.session_state.get("session_id", "anon")
    return f"pv::{session_id}::s{step}::{name}"


def _widget_key(field_key: str) -> str:
    """Cria uma chave de widget estável, porém "atualizável" (passo a passo).

    Em português simples: quando a IA melhora um texto, precisamos que o
    campo na tela "recarregue" o valor. Fazemos isso aumentando um número
    de versão na chave do widget, sem quebrar as regras de unicidade do
    Streamlit.
    """
    ver_key = f"pv_widget_ver_{field_key}"
    version = int(st.session_state.get(ver_key, 0))
    return f"roteiro_{field_key}_v{version}"


def _form_widget_key(field_key: str) -> str:
    """Versão de chave para os widgets do formulário completo (revisão)."""
    ver_key = f"pv_form_widget_ver_{field_key}"
    version = int(st.session_state.get(ver_key, 0))
    return f"form_{field_key}_v{version}"

# Serviço de IA — Unified service com fallback automático (Real ↔ Mock)

def _ensure_ai_env_loaded() -> None:
    """Tenta carregar variáveis do arquivo .env para habilitar a IA.

    Em algumas execuções, a página pode rodar sem o carregador global
    de configuração. Aqui fazemos uma busca simples por um arquivo
    ".env" em pastas comuns do projeto para achar a chave `OPENAI_API_KEY`.
    """
    if os.getenv("OPENAI_API_KEY"):
        return
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return

    # Monta uma lista segura de caminhos candidatos (sem índices fora de faixa)
    candidates: list[Path] = []
    try:
        candidates.append(Path.cwd() / ".env")
        for parent in Path(__file__).resolve().parents:
            candidates.append(parent / ".env")
            candidates.append(parent / "streamlit_extension/.env")
            candidates.append(parent / "config/.env")
    except Exception:
        # Em último caso, tenta apenas no diretório atual
        candidates = [Path.cwd() / ".env"]

    seen: set[str] = set()
    for env_path in candidates:
        try:
            key = str(env_path.resolve())
            if key in seen:
                continue
            seen.add(key)
            if env_path.exists():
                load_dotenv(env_path)
                if os.getenv("OPENAI_API_KEY"):
                    logger.debug("OPENAI_API_KEY carregada de: %s", env_path)
                    break
        except Exception:
            # Ignora e tenta próximo candidato
            continue
try:
    from streamlit_extension.services.vision_service import create_vision_service
    from src.ia.agents.agno_agent import SingleFieldAgent

    # Lazy init: criar serviços somente quando necessários (evita falha antes de carregar .env)
    class VisionRefineService:
        """Pequena fachada para chamar o serviço de IA real sob demanda.

        A instância real (cliente de IA) só é criada quando a primeira
        chamada de refino acontece, evitando erros de ambiente e melhorando
        o tempo de carregamento da página.
        """
        def __init__(self):
            self._vision: Any | None = None
            
        def refine(self, payload: Dict[str, Any]):
            """Envia todos os campos para a IA e retorna sugestões.

            Espera receber de volta um dicionário com os mesmos nomes de
            campos e textos melhorados. Em linguagem simples: você escreve,
            a IA dá um polimento e devolve o texto revisado.
            """
            if self._vision is None:
                # Garantir que OPENAI_API_KEY esteja carregada de .env quando necessário
                _ensure_ai_env_loaded()
                self._vision = create_vision_service(strict=True)
            return self._vision.refine(payload)

    class SingleFieldRefiner:
        """Refinador de campo individual (prompt dedicado com agente real)."""

        def __init__(self, agent: SingleFieldAgent):
            self.agent = agent

        def refine_field(self, field_key: str, field_value: Any, context: Dict[str, Any]) -> Any:
            # Construir prompt específico para reescrever apenas o campo, sem mudar significado
            field_labels = {
                "vision_statement": "Visão do Produto",
                "problem_statement": "Problema a Resolver", 
                "target_audience": "Público-Alvo",
                "value_proposition": "Proposta de Valor",
                "constraints": "Restrições"
            }

            label = field_labels.get(field_key, field_key)

            # Contexto textual enxuto
            ctx_lines = []
            for k, v in context.items():
                if k == field_key or not v:
                    continue
                if isinstance(v, list) and v:
                    ctx_lines.append(f"- {field_labels.get(k, k)}: {', '.join([str(x) for x in v])}")
                elif isinstance(v, str) and v.strip():
                    ctx_lines.append(f"- {field_labels.get(k, k)}: {v.strip()}")
            ctx_text = "\n".join(ctx_lines) if ctx_lines else "(sem contexto adicional)"

            current_text = str(field_value or "").strip()
            if not current_text:
                raise ValueError(f"Campo obrigatório '{field_key}' não preenchido")

            # Diretrizes específicas por campo, alinhadas a Product Vision do Scrum
            guidance_map = {
                "vision_statement": (
                    "- Foque no resultado para o usuário (user-centric).\n"
                    "- Valor de negócio claro; evite jargões.\n"
                    "- 1 a 2 frases, voz ativa, sem promessas vagas.\n"
                    "- Evite solução detalhada; descreva o propósito/resultado."
                ),
                "problem_statement": (
                    "- Descreva o problema do usuário de forma objetiva e mensurável.\n"
                    "- Evite soluções ou implementação; mantenha-se no 'quê/por quê'.\n"
                    "- Linguagem simples, foco na dor/necessidade prioritária."
                ),
                "target_audience": (
                    "- Defina a persona/segmento primário com clareza.\n"
                    "- Inclua contexto relevante (perfil, cenário de uso).\n"
                    "- Seja conciso (1 frase curta ou 2 no máximo)."
                ),
                "value_proposition": (
                    "- Expresse o valor entregue e o benefício principal.\n"
                    "- Diferenciação em relação a alternativas; foco em resultado.\n"
                    "- Evite detalhes técnicos; linguagem orientada a valor."
                ),
                "constraints": (
                    "- Liste apenas restrições essenciais (normas, prazos, limites).\n"
                    "- Formato claro e direto; sem expandir escopo."
                ),
            }

            guidance = guidance_map.get(field_key, "- Clareza, concisão e foco em valor para o usuário.")

            prompt = f"""Você é um Product Owner experiente em Scrum. Reescreva o campo "{label}" abaixo em português brasileiro, alinhado às melhores práticas de Product Vision do Scrum, com pertinência semântica e foco em valor.

Texto atual (entre marcadores):
<<BEGIN_TXT>>
{current_text}
<<END_TXT>>

Contexto do produto (entre marcadores):
<<BEGIN_CTX>>
{ctx_text}
<<END_CTX>>

Diretrizes específicas para "{label}":
{guidance}

Regras gerais:
- Reescreva o texto sem adicionar novas informações factuais.
- Seja claro, direto e profissional, em voz ativa.
- Evite repetir o texto original palavra por palavra; faça paráfrase natural.
- 1 a 2 frases para campos textuais; para restrições, mantenha concisão.
- Retorne APENAS o novo texto, sem comentários."""

            # Chamar agente real (resposta deve ser string)
            result = self.agent.refine_field(prompt)
            # O SingleFieldAgent já retorna string pura
            new_text = result.strip().strip('"') if result else ""
            return new_text or current_text

    def _get_single_field_refiner() -> "SingleFieldRefiner":
        """Obtém um refinador de campo único com cache em sessão.

        Para leigos: criamos um "ajudante de IA" específico para
        melhorar um campo por vez. Ele fica guardado em memória para
        ficar rápido nas próximas vezes.
        """
        # Guardar em session_state para não recriar a cada chamada
        key = "_pv_single_agent"
        if key not in st.session_state or not isinstance(st.session_state[key], SingleFieldAgent):
            _ensure_ai_env_loaded()
            st.session_state[key] = SingleFieldAgent(model_id="gpt-5-nano")
        return SingleFieldRefiner(st.session_state[key])

    logger.debug("Vision service pronto (lazy init, modo estrito)")

except Exception as e:
    # Strict: não realizar fallback; levanta erro nas chamadas
    class VisionRefineService:
        def refine(self, payload: Dict[str, Any]):
            raise RuntimeError(f"Vision service unavailable: {e}")

    class SingleFieldRefiner:
        def refine_field(self, field_key: str, field_value: Any, context: Dict[str, Any]) -> Any:
            raise RuntimeError(f"Vision service unavailable: {e}")

    def _get_single_field_refiner() -> "SingleFieldRefiner":
        return SingleFieldRefiner()
    logger.warning("Vision service indisponível (modo estrito)")

# State helpers
from .._pv_state import (
    init_pv_state,
    PV_FIELDS,
    set_pv_mode,
    next_step,
    prev_step,
    is_review_step,
    total_steps,
)

# ---------------------------------------------
# Utilidades locais (robustez e reutilização)
# ---------------------------------------------
def _get_refine_service() -> VisionRefineService:
    """Obtém uma instância única do serviço de IA (com cache na sessão).

    Para leigos: criamos o "motor de IA" uma vez e reaproveitamos
    durante a navegação, evitando atrasos e erros repetidos.
    """
    key = "_pv_refine_service"
    if key not in st.session_state:
        st.session_state[key] = VisionRefineService()
    return st.session_state[key]


def _status_ctx(label: str, expanded: bool = True):
    """Mostra uma caixa de status durante ações da IA."""
    return st.status(label, expanded=expanded)


def _preview(v: Any, max_len: int = 120) -> str:
    """Gera um texto curtinho para logs/diagnóstico (sem quebrar a tela)."""
    try:
        if isinstance(v, (dict, list)):
            s = json.dumps(v, ensure_ascii=False)  # type: ignore[arg-type]
        else:
            s = str(v)
    except Exception:
        s = str(v)
    s = s.strip().replace("\n", " ")
    return (s[:max_len] + "…") if len(s) > max_len else s


def _is_nonempty_str(x: Any) -> bool:
    """Confere se é uma string com algum conteúdo (ignorando espaços)."""
    return isinstance(x, str) and x.strip() != ""


# _sanitize_constraints removed - constraints now work as regular string field


# ---------------------------------------------
# Validadores simples
# ---------------------------------------------
def _all_fields_filled(pv_data: Dict[str, Any]) -> bool:
    """Verifica se todos os campos da visão do produto foram preenchidos.

    Em termos simples: impede chamar a IA global antes de completar os
    campos obrigatórios, evitando resultados ruins.
    """
    for field_key, _ in PV_FIELDS:
        v = pv_data.get(field_key)
        if not _is_nonempty_str(v):
            return False
    return True


# ---------------------------------------------
# Componente principal (render)
# ---------------------------------------------
def render_product_vision_with_toggle(
    controller=None, project_id: Optional[int] = None
) -> None:
    """Desenha a etapa de Product Vision com dois modos de uso.

    - Passo a passo: responde uma pergunta por vez e pode refinar cada
      campo com IA.
    - Formulário completo: vê tudo junto e pode refinar tudo de uma vez.

    Observação: os parâmetros `controller` e `project_id` estão reservados
    para integrações futuras e hoje não alteram o comportamento da tela.
    """
    init_pv_state(st.session_state)

    # Dynamic title for current macro phase (avoid circular import)
    current_wizard_step = getattr(st.session_state, 'wizard_current_step', 1)
    step_names = {1: "Roteiro", 2: "Capítulos", 3: "Histórias", 4: "Tarefas"}
    macro_phase = step_names.get(current_wizard_step, "Roteiro")
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
    """Mostra todas as perguntas em um único formulário simples.

    Ideal para quem prefere preencher tudo de uma vez e depois pedir para
    a IA revisar o texto completo.
    """
    with st.form("pv_form_mode", clear_on_submit=False):
        # Coletar valores dos widgets sem sobrescrever o session_state durante renderização
        form_values = {}
        
        for field_key, field_label in PV_FIELDS:
            if field_key == "constraints":
                form_values[field_key] = st.text_area(
                    field_label,
                    st.session_state.pv.get(field_key, ""),
                    height=100,
                    help="Ex.: orçamento limitado\natender LGPD\nlançar em 90 dias",
                    key=_form_widget_key(field_key),
                )
            elif field_key in {"problem_statement", "value_proposition"}:
                form_values[field_key] = st.text_area(
                    field_label,
                    st.session_state.pv.get(field_key, ""),
                    height=120,  # Mais vertical
                    key=_form_widget_key(field_key),
                )

            else:
                form_values[field_key] = st.text_area(
                    field_label,
                    st.session_state.pv.get(field_key, ""),
                    height=80,  # Transformar text_input em text_area para ser mais vertical
                    key=_form_widget_key(field_key),
                )

        col1, col2, col3 = st.columns(3)
        with col1:
            refine_all = st.form_submit_button(
                "✨ Refinar Tudo", use_container_width=True, key=_wiz_key("form_refinar_tudo")
            )
        with col2:
            save_draft = st.form_submit_button(
                "💾 Salvar Rascunho", use_container_width=True, key=_wiz_key("form_salvar_rascunho")
            )
        with col3:
            validate_form = st.form_submit_button(
                "✅ Validar", use_container_width=True, key=_wiz_key("form_validar")
            )

    # Processar ações do formulário
    if refine_all or save_draft or validate_form:
        # Inicializar flag se não existir
        if 'refinement_in_progress' not in st.session_state:
            st.session_state.refinement_in_progress = False
            
        # Atualizar session_state apenas quando não está refinando
        if not st.session_state.refinement_in_progress:
            for field_key in form_values:
                st.session_state.pv[field_key] = form_values[field_key]
    
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
    """Mostra as perguntas uma a uma, com barra de progresso.

    Ao final, há uma tela de revisão com o formulário completo.
    """
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
            if st.button(
                "⬅ Anterior",
                use_container_width=True,
                key=_wiz_key("btn_anterior_review", "review"),
            ):
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

    if field_key in {"problem_statement", "value_proposition", "constraints"}:
        height = 150 if field_key == "constraints" else 200
        help_text = "Ex.: orçamento limitado\natender LGPD\nlançar em 90 dias" if field_key == "constraints" else None
        st.session_state.pv[field_key] = st.text_area(
            field_label,
            st.session_state.pv.get(field_key, ""),
            height=height,
            help=help_text,
            key=_widget_key(field_key),
        )

    else:
        st.session_state.pv[field_key] = st.text_area(
            field_label,
            st.session_state.pv.get(field_key, ""),
            height=120,  # Transformar text_input em text_area para ser mais vertical
            key=_widget_key(field_key),
        )

    # Navegação + refino por campo
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button(
            "⬅ Anterior",
            disabled=(idx == 0),
            use_container_width=True,
            key=_wiz_key("btn_anterior", idx),
        ):
            prev_step(st.session_state)
            st.rerun()
    with nav_col2:
        if st.button(
            "Próximo ➡",
            use_container_width=True,
            key=_wiz_key("btn_proximo", idx),
        ):
            next_step(st.session_state)
            st.rerun()
    with nav_col3:
        if st.button(
            "✨ Refinar este campo",
            use_container_width=True,
            key=_wiz_key("btn_refinar", idx),
        ):
            _handle_refine_field(field_key)


# ---------------------------------------------
# Resumo lateral
# ---------------------------------------------
def _render_summary() -> None:
    """Apresenta um resumo claro do que já foi preenchido."""
    st.subheader("📋 Resumo")

    if _all_fields_filled(st.session_state.pv):
        st.success("✅ Completo")
    else:
        st.warning("⏳ Em progresso")

    for field_key, field_label in PV_FIELDS:
        value = st.session_state.pv.get(field_key, "")
        if field_key == "constraints":
            # Tratar constraints como texto multilinhas e exibir em bullets
            if _is_nonempty_str(value):
                lines = [line.strip() for line in value.split('\n') if line.strip()]
                if lines:
                    st.markdown(f"**{field_label}:**")
                    for line in lines:
                        st.markdown(f"- {line}")
                else:
                    st.markdown(f"**{field_label}:** _vazio_")
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
    """Pede para a IA polir todos os campos de uma só vez.

    Só funciona quando todos os campos estiverem preenchidos — assim a
    IA consegue manter coerência e não inventa informação.
    """
    if not _all_fields_filled(st.session_state.pv):
        st.warning("⚠️ Para refinar com IA, preencha todos os campos primeiro.")
        return

    # Inicializar flag de refinamento se não existir
    if 'refinement_in_progress' not in st.session_state:
        st.session_state.refinement_in_progress = False
    
    # Prevenir múltiplas execuções simultâneas
    if st.session_state.refinement_in_progress:
        return
    
    # Set flag para prevenir ciclo vicioso
    st.session_state.refinement_in_progress = True

    service = _get_refine_service()
    with _status_ctx("🤖 Refinando com IA...", expanded=True) as status:
        try:
            # Etapas (se st.status disponível, o .update fará efeito)
            status.update(label="📋 Validando campos...", state="running")
            status.update(label="🔧 Preparando dados para IA...", state="running")

            try:
                logger.info(
                    "PV refine_all | payload: %s",
                    {k: _preview(v) for k, v in st.session_state.pv.items()},
                )
            except Exception:
                pass

            status.update(label="✨ Refinando conteúdo...", state="running")
            result = service.refine(st.session_state.pv)

            # Robustez: o serviço deve devolver um dicionário
            if not isinstance(result, dict):
                status.update(label="⚠️ Resposta inesperada da IA. Tente novamente.", state="error")
                logger.error("PV refine_all | resultado inesperado do serviço: %s", type(result).__name__)
                # Reset flag antes de retornar, para não travar o fluxo
                st.session_state.refinement_in_progress = False
                return

            status.update(label="📝 Aplicando melhorias...", state="running")
            fields_updated = 0

            try:
                logger.info(
                    "PV refine_all | result_type=%s | result_keys=%s",
                    type(result).__name__,
                    list(result.keys()) if isinstance(result, dict) else "n/a",
                )
            except Exception:
                pass

            for field_key, _ in PV_FIELDS:
                if field_key not in result:
                    continue

                raw_val = result[field_key]
                new_text: str = ""
                if field_key == "constraints":
                    # Contrato atual: string; manter suporte defensivo a lista
                    if isinstance(raw_val, str):
                        new_text = raw_val.strip()
                    elif isinstance(raw_val, list):
                        parts = [str(x).strip() for x in raw_val if str(x).strip()]
                        new_text = "\n".join(parts)
                else:
                    if isinstance(raw_val, str):
                        new_text = raw_val.strip()
                    else:
                        # fallback defensivo
                        new_text = str(raw_val).strip()

                old_text = str(st.session_state.pv.get(field_key, "") or "").strip()
                if _is_nonempty_str(new_text):
                    st.session_state.pv[field_key] = new_text
                    # Forçar refresh dos widgets (formulário e steps)
                    form_ver_key = f"pv_form_widget_ver_{field_key}"
                    st.session_state[form_ver_key] = int(st.session_state.get(form_ver_key, 0)) + 1
                    step_ver_key = f"pv_widget_ver_{field_key}"
                    st.session_state[step_ver_key] = int(st.session_state.get(step_ver_key, 0)) + 1
                    fields_updated += 1

                    try:
                        logger.info(
                            "PV refine_all | field=%s | old_len=%d | new_len=%d | changed=%s | prev=%s | next=%s",
                            field_key,
                            len(old_text),
                            len(new_text),
                            old_text != new_text,
                            _preview(old_text),
                            _preview(new_text),
                        )
                    except Exception:
                        pass

            status.update(
                label=f"✅ Refinamento concluído! {fields_updated} campos aprimorados.",
                state="complete",
            )
            st.success(f"✨ {fields_updated} campos foram refinados com sucesso!")
            try:
                logger.info(
                    "PV refine_all | fields_updated=%d | versions_form=%s | versions_steps=%s | pv=%s",
                    fields_updated,
                    {f: int(st.session_state.get(f"pv_form_widget_ver_{f}", 0)) for f, _ in PV_FIELDS},
                    {f: int(st.session_state.get(f"pv_widget_ver_{f}", 0)) for f, _ in PV_FIELDS},
                    {k: _preview(v) for k, v in st.session_state.pv.items()},
                )
            except Exception:
                pass
            
            # Reset flag antes de rerun
            st.session_state.refinement_in_progress = False
            st.rerun()
        except Exception as e:  # pragma: no cover - apenas UI
            status.update(label="❌ Erro no refinamento", state="error")
            st.error(f"❌ Erro ao refinar: {e}")
            # Reset flag em caso de erro
            st.session_state.refinement_in_progress = False


def _handle_refine_field(field_key: str) -> None:
    """Pede para a IA melhorar apenas um campo, usando o contexto.

    Em linguagem simples: a IA lê as outras respostas (se existirem)
    para manter o mesmo tom e sentido, mas só reescreve o campo escolhido.
    """
    current_value = st.session_state.pv.get(field_key)

    if not _is_nonempty_str(current_value):
        st.warning("⚠️ Preencha o campo antes de refinar.")
        return

    field_label = next((label for key, label in PV_FIELDS if key == field_key), field_key)

    # Monta contexto completo (outros campos podem estar vazios)
    context: Dict[str, Any] = {}
    for key, _ in PV_FIELDS:
        context[key] = st.session_state.pv.get(key, "")
    # Garantir que o campo alvo vai com o valor atual
    context[field_key] = (current_value or "").strip()

    # Variável para controlar se precisa fazer rerun (fora do context manager)
    needs_rerun = False
    refined_str = None
    
    with _status_ctx(f"🤖 Refinando campo: {field_label}", expanded=True) as status:
        try:
            status.update(label=f"📋 Analisando {field_label}...", state="running")
            status.update(label=f"✨ Aplicando IA ao campo {field_label}...", state="running")
            
            # Usar refinamento individual (não exige todos os campos preenchidos)
            refined_value = _get_single_field_refiner().refine_field(field_key, current_value, context)
            logger.info(
                "PV refine_field result | field=%s | before_len=%s | after_len=%s",
                field_key,
                len(str(current_value or "")),
                len(str(refined_value or "")),
            )

            status.update(label=f"📝 Atualizando {field_label}...", state="running")

            # Log do valor refinado para debug
            logger.debug(f"Campo {field_key}: valor original='{current_value}', refinado='{refined_value}'")
            
            # Mostrar sugestão recebida para transparência
            st.expander("🔎 Sugestão da IA (pré-visualização)", expanded=False).write(str(refined_value or ""))

            # Aplicar valor refinado sempre que houver um resultado válido
            old_value = st.session_state.pv.get(field_key, "")
            
            # Normalizar valores para comparação
            refined_str = str(refined_value or "").strip()
            old_str = str(old_value or "").strip()
            
            # Aplicar o valor refinado ao session state (sempre)
            if refined_str:  # Se há conteúdo refinado
                # Atualizar tanto o session_state quanto o widget key para forçar refresh
                st.session_state.pv[field_key] = refined_str
                
                # Forçar refresh visual do widget: bump da versão de key
                ver_key = f"pv_widget_ver_{field_key}"
                st.session_state[ver_key] = int(st.session_state.get(ver_key, 0)) + 1
                
                logger.info(f"Valor aplicado ao campo {field_key}: '{refined_str[:50]}...'")
                
                # Verificar se houve mudança real
                if refined_str != old_str:
                    status.update(label=f"✅ Campo {field_label} refinado com sucesso!", state="complete")
                    logger.info(f"Campo {field_key} atualizado: {len(old_str)} → {len(refined_str)} chars")
                    needs_rerun = True
                else:
                    status.update(label=f"ℹ️ IA manteve o conteúdo otimizado de {field_label}", state="complete")
                    logger.info("IA confirmou que o texto já está otimizado")
                    
            else:  # Se a IA não retornou conteúdo válido
                status.update(label=f"⚠️ IA não gerou conteúdo para {field_label}", state="error")
                logger.warning(f"Campo {field_key}: IA retornou valor vazio ou inválido")
                
        except Exception as e:  # pragma: no cover - apenas UI
            status.update(label=f"❌ Erro ao refinar {field_label}", state="error")
            logger.error(f"Erro ao refinar campo {field_key}: {e}")
    
    # Fazer rerun FORA do context manager para evitar conflitos
    if needs_rerun:
        st.success(f"✨ {field_label} foi aprimorado!")
        st.rerun()
    elif refined_str and refined_str == str(st.session_state.pv.get(field_key, "")):
        st.info("ℹ️ A IA confirmou que o texto já está em sua melhor forma.")
    else:
        st.warning("⚠️ A IA não conseguiu gerar uma sugestão válida para este campo.")


# ---------------------------------------------
# API legada (compat)
# ---------------------------------------------
def render_step(ctx: Dict[str, Any]) -> None:
    """Ponto de entrada antigo mantido por compatibilidade.

    Aceita um dicionário com dados prévios e renderiza a tela atual.
    """
    if "data" in ctx and "product_vision" in ctx["data"]:
        old = ctx["data"]["product_vision"]
        init_pv_state(st.session_state)
        for key in old:
            if any(key == k for k, _ in PV_FIELDS):
                st.session_state.pv[key] = old[key]
    render_product_vision_with_toggle()


def validate(ctx: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validação rápida dos campos (modo legado).

    Retorna (True, None) quando está tudo ok, ou (False, mensagem) quando
    falta preencher algo importante.
    """
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
    """Gera um resumo simples no formato de dicionário (modo legado)."""
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
            "Restrições": step.get("constraints", ""),
        }

    return {}
