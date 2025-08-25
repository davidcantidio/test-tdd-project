from __future__ import annotations
from typing import Dict, Any, Tuple

WIZ_KEY = "projeto_wizard"

DEFAULT_DRAFT: Dict[str, Any] = {
    "name": "",
    # Campos de Product Vision na taxonomia do banco (rascunho em memória)
    "vision_statement": "",
    "problem_statement": "",
    "target_audience": "",
    "value_proposition": "",
    "constraints": [],  # list[str]
}

def init_wizard_state(session_state: Dict[str, Any]) -> None:
    """Garante estrutura do wizard no session_state-like dict."""
    if WIZ_KEY not in session_state:
        session_state[WIZ_KEY] = {
            "current_step": "project_name",
            "project_draft": dict(DEFAULT_DRAFT),
        }
    else:
        wiz = session_state[WIZ_KEY]
        wiz.setdefault("current_step", "project_name")
        wiz.setdefault("project_draft", dict(DEFAULT_DRAFT))
        # garante todas as chaves do draft (sem perder dados existentes)
        for k, v in DEFAULT_DRAFT.items():
            wiz["project_draft"].setdefault(k, v)

def current_step(session_state: Dict[str, Any]) -> str:
    return session_state[WIZ_KEY]["current_step"]

def move_to(session_state: Dict[str, Any], step: str) -> None:
    session_state[WIZ_KEY]["current_step"] = step

def validate_project_name(name: str) -> Tuple[bool, str | None]:
    """Regras simples: obrigatório e >= 3 chars (desconsiderando espaços)."""
    if name is None or not isinstance(name, str):
        return False, "Nome inválido."
    trimmed = name.strip()
    if len(trimmed) < 3:
        return False, "Informe um nome com pelo menos 3 caracteres."
    return True, None

def advance_from_name(session_state: Dict[str, Any], name: str) -> Tuple[bool, str | None]:
    """Ação do botão 'Continuar' no passo 0: valida e avança para product_vision."""
    ok, msg = validate_project_name(name)
    if not ok:
        return False, msg
    session_state[WIZ_KEY]["project_draft"]["name"] = name.strip()
    move_to(session_state, "product_vision")
    return True, None
