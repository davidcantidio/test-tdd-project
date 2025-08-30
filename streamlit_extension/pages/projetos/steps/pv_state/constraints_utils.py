"""
constraints_utils
=================

Utilidades para (de)serializar o campo `constraints` entre **lista de strings**
e **texto multilinha**. Essas funções são puras e testáveis.
"""

from __future__ import annotations
from typing import List


def constraints_to_text(lst: List[str]) -> str:
    """
    Converte lista de *constraints* em texto multilinha.

    Regras:
    - Ignora entradas vazias/whitespace.
    - Mantém a ordem.

    Exemplo
    -------
    >>> constraints_to_text(["a", " ", "b"])
    'a\\nb'
    """
    return "\n".join([x for x in (lst or []) if isinstance(x, str) and x.strip()])


def constraints_from_text(txt: str) -> List[str]:
    """
    Converte texto multilinha em lista de *constraints*.

    Regras:
    - Faz `strip()` por linha.
    - Ignora linhas vazias.

    Exemplo
    -------
    >>> constraints_from_text(" a\\n\\n b ")
    ['a', 'b']
    """
    items = [line.strip() for line in (txt or "").splitlines()]
    return [x for x in items if x]
