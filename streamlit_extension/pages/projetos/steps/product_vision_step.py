# streamlit_extension/pages/projetos/steps/product_vision_step.py
from __future__ import annotations
import streamlit as st
from typing import Dict, Any, List
from src.ia.services.vision_refine_service import VisionRefineService

FIELDS = [
    "vision_statement",
    "problem_statement",
    "target_audience",
    "value_proposition",
    "constraints",
]

LABELS = {
    "vision_statement": "Declaração de Visão",
    "problem_statement": "Problema a Resolver",
    "target_audience": "Público-alvo",
    "value_proposition": "Proposta de Valor",
    "constraints": "Restrições (uma por linha)",
}

HELP = {
    "constraints": "Ex.: orçamento limitado\natender LGPD\nlançar em 90 dias",
}

DEFAULTS = {
    "vision_statement": "",
    "problem_statement": "",
    "target_audience": "",
    "value_proposition": "",
    "constraints": [],  # lista de strings
}

def _ensure_step_dict(ctx: Dict[str, Any]) -> Dict[str, Any]:
    data = ctx["data"]
    step = data.setdefault("product_vision", {})
    for k, v in DEFAULTS.items():
        step.setdefault(k, v if not isinstance(v, list) else list(v))
    return step

def _constraints_to_text(lst: List[str]) -> str:
    return "\n".join([x for x in lst if isinstance(x, str)])

def _constraints_from_text(txt: str) -> List[str]:
    items = [line.strip() for line in (txt or "").splitlines()]
    return [x for x in items if x]

def _all_fields_filled(step: Dict[str, Any]) -> bool:
    for k in FIELDS:
        v = step.get(k)
        if isinstance(v, str) and not v.strip():
            return False
        if isinstance(v, list) and len([x for x in v if isinstance(x, str) and x.strip()]) == 0:
            return False
        if not isinstance(v, (str, list)):
            return False
    return True

# ========== API esperada pelo roteador ==========
def render_step(ctx: Dict[str, Any]) -> None:
    step = _ensure_step_dict(ctx)

    st.subheader("🎯 Product Vision")
    with st.form("pv_form"):
        step["vision_statement"] = st.text_input(
            LABELS["vision_statement"], step.get("vision_statement", "")
        )
        step["target_audience"] = st.text_input(
            LABELS["target_audience"], step.get("target_audience", "")
        )
        step["problem_statement"] = st.text_area(
            LABELS["problem_statement"], step.get("problem_statement", ""), height=120
        )
        step["value_proposition"] = st.text_area(
            LABELS["value_proposition"], step.get("value_proposition", ""), height=120
        )

        constraints_text = st.text_area(
            LABELS["constraints"],
            _constraints_to_text(step.get("constraints", [])),
            height=120,
            help=HELP.get("constraints"),
        )

        col1, col2, col3 = st.columns([1, 1, 2])
        refine_clicked = col1.form_submit_button("Refinar com IA ✨")
        apply_clicked = col2.form_submit_button("Aplicar & Continuar ✅")

        # Atualiza lista a partir do textarea
        step["constraints"] = _constraints_from_text(constraints_text)

    if refine_clicked:
        if not _all_fields_filled(step):
            st.warning("Para refinar com IA, preencha todos os campos.")
        else:
            with st.spinner("Refinando com IA…"):
                try:
                    result = VisionRefineService().refine(step)  # espera as mesmas chaves
                    # aplica resultado mantendo o shape
                    for k in ["vision_statement", "problem_statement", "target_audience", "value_proposition"]:
                        val = result.get(k)
                        if isinstance(val, str) and val.strip():
                            step[k] = val.strip()
                    cons = result.get("constraints")
                    if isinstance(cons, list) and cons:
                        step["constraints"] = [c for c in cons if isinstance(c, str) and c.strip()]
                    st.success("Sugestões aplicadas. Você pode editar manualmente antes de avançar.")
                except Exception as e:
                    st.error(f"Falha ao refinar com IA: {e}")

    if apply_clicked:
        ok, msg = validate(ctx)
        if ok:
            st.success("Etapa válida. Você pode clicar em ‘Avançar’ na barra lateral.")
        else:
            st.warning(msg or "Preencha corretamente a etapa.")

def validate(ctx: Dict[str, Any]) -> tuple[bool, str | None]:
    step = _ensure_step_dict(ctx)
    if not _all_fields_filled(step):
        return False, "Todos os campos são obrigatórios para a Product Vision."
    return True, None

def get_summary(ctx: Dict[str, Any]):
    step = _ensure_step_dict(ctx)
    return {
        "Declaração de Visão": step.get("vision_statement", ""),
        "Problema": step.get("problem_statement", ""),
        "Público-alvo": step.get("target_audience", ""),
        "Proposta de Valor": step.get("value_proposition", ""),
        "Restrições": step.get("constraints", []),
    }
