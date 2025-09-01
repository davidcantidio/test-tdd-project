#!/usr/bin/env bash
set -euo pipefail

BASE="streamlit_extension/pages/projetos/steps/product_vision_step"

# Garante que a pasta exista
mkdir -p "$BASE"

# Se o arquivo antigo .py ainda existe fora do pacote, mova para dentro como _legacy.py
if [ -f "streamlit_extension/pages/projetos/steps/product_vision_step.py" ]; then
  git mv "streamlit_extension/pages/projetos/steps/product_vision_step.py" "$BASE/_legacy.py"
  echo "✔️  Movido: product_vision_step.py ➜ $BASE/_legacy.py"
fi

# (Re)cria __init__.py com reexports do legacy
cat > "$BASE/__init__.py" <<'PY'
"""
product_vision_step (pacote)
============================

Este pacote substitui o antigo módulo único `product_vision_step.py`.

Para manter **compatibilidade**, reexportamos as funções públicas do arquivo
`_legacy.py` (que contém a implementação original) até concluirmos a
modularização completa (form_mode, steps_mode, summary, ai_refine, legacy_api).

Assim, importadores existentes continuam funcionando:

    from streamlit_extension.pages.projetos.steps.product_vision_step import (
        render_product_vision_with_toggle,
        render_step, validate, get_summary,
    )
"""

# Reexports de compatibilidade
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
PY

echo "✔️  Atualizado: $BASE/__init__.py (reexports do _legacy.py)"

echo "✅ Pronto. Agora os imports existentes voltam a funcionar."
