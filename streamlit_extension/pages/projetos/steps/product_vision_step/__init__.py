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

# IMPORTANTE: Reexportar o VisionRefineService para garantir que o sistema real seja usado
try:
    import sys
    import os
    # Importar o módulo .py diretamente, não o pacote
    sys.path.insert(0, os.path.dirname(__file__))
    from product_vision_step import VisionRefineService as RealVisionRefineService
    VisionRefineService = RealVisionRefineService
    print("✅ Sistema real importado via __init__.py")
except Exception as import_error:
    print(f"⚠️ Falha ao importar sistema real via __init__.py: {import_error}")
    VisionRefineService = None

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
