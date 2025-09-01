"""
legacy_api
==========

Shim temporário que delega para a implementação consolidada em `_legacy.py`.
Substitua por implementação modular quando os módulos estiverem completos.
"""

from __future__ import annotations
from typing import Any, Dict, Tuple

from ._legacy import render_step as _legacy_render_step
from ._legacy import validate as _legacy_validate
from ._legacy import get_summary as _legacy_get_summary


def render_step(ctx: Dict[str, Any]) -> None:
    return _legacy_render_step(ctx)


def validate(ctx: Dict[str, Any]) -> Tuple[bool, str | None]:
    return _legacy_validate(ctx)


def get_summary(ctx: Dict[str, Any]) -> Dict[str, Any]:
    return _legacy_get_summary(ctx)
