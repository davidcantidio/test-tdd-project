"""
product_vision_step (pacote)
============================

Este pacote substitui o antigo módulo único `product_vision_step.py`.

Objetivo
--------
Manter compatibilidade com os imports existentes **enquanto** migramos,
expondo as mesmas funções públicas:

- render_product_vision_with_toggle
- render_step
- validate
- get_summary

Estratégia
----------
1) Primeiro tentamos reexportar **implementações novas** (quando os módulos
   `form_mode`, `steps_mode`, `summary`, `ai_refine`, `legacy_api` já estiverem completos).
2) Enquanto a migração está em curso, fazemos **fallback** para `_legacy.py`.

Assim, os testes e páginas que importam do caminho antigo continuam funcionando:

    from streamlit_extension.pages.projetos.steps.product_vision_step import (
        render_product_vision_with_toggle,
        render_step, validate, get_summary,
    )
"""

from __future__ import annotations

# Fallbacks do legacy garantem compat imediata
try:
    # Preferencialmente reexporte a implementação finalizada quando existir
    # (descomente/ajuste quando os módulos forem preenchidos)
    # from .legacy_api import render_step, validate, get_summary
    # from .steps_mode import render_product_vision_with_toggle
    raise ImportError  # força fallback por enquanto
except Exception:
    from ._legacy import (
        render_product_vision_with_toggle,
        render_step,
        validate,
        get_summary,
    )

__all__ = [
    "render_product_vision_with_toggle",
    "render_step",
    "validate",
    "get_summary",
]
