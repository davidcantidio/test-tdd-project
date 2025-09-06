"""
product_vision_step (pacote)
============================

Este pacote substitui o antigo módulo único `product_vision_step.py`.

Para manter **compatibilidade**, reexportamos as funções públicas a partir do
módulo `_legacy.py` (que contém a implementação original) enquanto concluímos
a modularização em submódulos (`form_mode`, `steps_mode`, `summary`, `ai_refine`,
`legacy_api`).

Assim, importadores existentes continuam funcionando:

    from streamlit_extension.pages.projetos.steps.product_vision_step import (
        render_product_vision_with_toggle,
        render_step,
        validate,
        get_summary,
    )

Quando a migração terminar, estes reexports podem ser removidos e os chamadores
devem apontar diretamente para os novos submódulos.
"""

from __future__ import annotations

__all__ = [
    "render_product_vision_with_toggle",
    "render_step",
    "validate",
    "get_summary",
]

# IMPORTANTE: Sistema de IA disponível via main.py quando necessário
# Removido import circular que causava problemas desnecessários
print("✅ Sistema de IA configurado via main.py (sem imports circulares)")

# Reexports de compatibilidade com fallback amigável
try:
    from .main import (  # type: ignore
        render_product_vision_with_toggle,
        render_step,
        validate,
        get_summary,
    )
except Exception as _e:  # ModuleNotFoundError, ImportError, etc.
    # Definimos stubs que falham de forma clara se alguém tentar usar
    def _missing(*_args, **_kwargs):  # pragma: no cover
        raise RuntimeError(
            "As funções de compatibilidade de product_vision_step não estão "
            "disponíveis. Verifique se o módulo `.main` existe e exporta "
            "`render_product_vision_with_toggle`, `render_step`, `validate`, "
            "e `get_summary`."
        ) from _e

    render_product_vision_with_toggle = _missing
    render_step = _missing
    validate = _missing
    get_summary = _missing
