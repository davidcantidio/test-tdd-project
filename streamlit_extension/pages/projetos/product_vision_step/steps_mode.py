"""
steps_mode
==========

Shim temporário para expor uma função compatível.
Por ora delega para `_legacy.render_product_vision_with_toggle`.
No futuro: separar renderização passo-a-passo aqui.
"""

from __future__ import annotations
from ._legacy import render_product_vision_with_toggle as _legacy_render


def render_product_vision_with_toggle(*args, **kwargs) -> None:
    return _legacy_render(*args, **kwargs)
