"""Product Vision Step — API pública consolidada.

Este pacote expõe a API do passo "Product Vision" do assistente de projetos.
A implementação atual está consolidada em `main.py` (UI + handlers + IA),
evitando importações circulares e mantendo um ponto único de manutenção.

Funções exportadas (estáveis):
    - ``render_product_vision_with_toggle()``: renderiza a fase Roteiro (steps
      e revisão final), com integração de IA.
    - ``render_step(ctx)``: compat legada para renderização baseada em contexto.
    - ``validate(ctx)``: validação legada do passo.
    - ``get_summary(ctx)``: resumo legada dos campos preenchidos.

Notas de arquitetura:
    - O estado e a ordem dos campos vêm de ``steps/_pv_state.py``.
    - O serviço de IA é criado via ``create_vision_service(strict=True)``.
    - Todos os campos (incluindo ``constraints``) são tratados como strings.
"""

from __future__ import annotations

__all__ = [
    "render_product_vision_with_toggle",
    "render_step",
    "validate",
    "get_summary",
]

# IMPORTANTE: Sistema de IA configurado via main.py quando necessário
# Mantemos import mínimo aqui para evitar efeitos colaterais desnecessários
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
    _IMPORT_ERROR = _e  # preserve original exception outside 'except' scope

    # Log detalhado da causa para facilitar diagnóstico
    try:
        import traceback as _tb  # local import to avoid global side-effects
        print("❌ Falha ao importar product_vision_step.main:\n" + _tb.format_exc())
    except Exception:
        pass

    def _missing(*_args, **_kwargs):  # pragma: no cover
        raise RuntimeError(
            "Product Vision Step indisponível. Verifique se `product_vision_step/main.py` "
            "existe e exporta: render_product_vision_with_toggle, render_step, "
            "validate e get_summary."
        ) from _IMPORT_ERROR

    render_product_vision_with_toggle = _missing
    render_step = _missing
    validate = _missing
    get_summary = _missing
