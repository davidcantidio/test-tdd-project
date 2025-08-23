#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 COMPONENTS - Projeto Wizard (Lazy Exports + Safe Init)

Módulo de fachada para o sistema de wizard de criação de projetos.

Principais melhorias:
- 🔁 Lazy loading (PEP 562) para evitar custo de import desnecessário
- 🔒 __all__ imutável (tupla) e superfície de API explícita
- 🧪 Função auxiliar opcional `ensure_wizard_ready()` para inicialização segura
- 🏷️ Metadados do módulo (__version__, __docformat__)

Uso (compatível com a versão anterior):
    from streamlit_extension.components.projeto_wizard import (
        render_projeto_wizard,
        WizardState,
        initialize_wizard_state,
    )
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, Dict, Tuple

__docformat__ = "restructuredtext"
__version__ = "1.1.0"

# Superfície pública da API (imutável)
__all__: Tuple[str, ...] = (
    # Main render function
    "render_projeto_wizard",

    # Navigation functions
    "set_wizard_step",
    "set_wizard_view",

    # State management
    "WizardState",
    "initialize_wizard_state",
    "get_wizard_state",
    "save_wizard_draft",
    "load_wizard_draft",

    # Utilitário auxiliar
    "ensure_wizard_ready",
    "is_wizard_available",
)

# Mapa de exports para lazy loading
# name -> (module_path, attribute_name)
_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    # Frame / navegação
    "render_projeto_wizard": (".wizard_frame", "render_projeto_wizard"),
    "set_wizard_step": (".wizard_frame", "set_wizard_step"),
    "set_wizard_view": (".wizard_frame", "set_wizard_view"),
    # Estado
    "WizardState": (".state_manager", "WizardState"),
    "initialize_wizard_state": (".state_manager", "initialize_wizard_state"),
    "get_wizard_state": (".state_manager", "get_wizard_state"),
    "save_wizard_draft": (".state_manager", "save_wizard_draft"),
    "load_wizard_draft": (".state_manager", "load_wizard_draft"),
}

def __getattr__(name: str) -> Any:  # PEP 562 – lazy attribute access em módulos
    target = _LAZY_EXPORTS.get(name)
    if not target:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_path, attr = target
    mod: ModuleType = import_module(module_path, package=__package__)
    value = getattr(mod, attr)
    globals()[name] = value  # cache em módulo para futuras chamadas
    return value

def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(__all__))

# ---------- Utilidades opcionais e seguras ----------

def is_wizard_available() -> bool:
    """
    Verifica se os submódulos essenciais do wizard podem ser importados.

    Returns:
        bool: True se imports críticos forem bem-sucedidos, False caso contrário.
    """
    try:
        # Força resolução uma única vez (cacheado em globals)
        _ = render_projeto_wizard  # noqa: F401
        _ = WizardState  # noqa: F401
        return True
    except Exception:
        return False

def ensure_wizard_ready() -> None:
    """
    Garante que o estado do wizard esteja inicializado com segurança.

    Idempotente: pode ser chamado múltiplas vezes sem efeitos colaterais.
    Levanta exceções originais dos submódulos se algo impedir a inicialização.
    """
    # Importa sob demanda (permite interceptar erros reais da camada de estado)
    state_getter = __getattr__("get_wizard_state")
    state_init = __getattr__("initialize_wizard_state")

    state = state_getter()
    if state is None:
        state_init()
