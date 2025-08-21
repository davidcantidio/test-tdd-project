#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI do auditor sistemático pós-refactor:
- Usa DI container para montar orquestrador e serviços
- Mantém compatibilidade via comando único
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from audit_system.core.container import build_default_auditor
from audit_system.core.contracts import FileFinding


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Systematic file audit (refactor: DI + orchestrator)")
    ap.add_argument("--root", type=Path, default=Path.cwd(), help="Raiz do projeto (default: cwd)")
    ap.add_argument("--db", type=Path, default=None, help="Caminho do DB SQLite de sessões (opcional)")
    ap.add_argument("targets", nargs="*", type=Path, help="Arquivos/diretórios específicos a auditar (opcional)")
    return ap.parse_args()


def _resolve_targets(root: Path, targets: List[Path]) -> List[Path]:
    if not targets:
        return []
    resolved: List[Path] = []
    for t in targets:
        p = (root / t) if not t.is_absolute() else t
        resolved.append(p.resolve())
    return resolved


def main() -> int:
    args = _parse_args()
    auditor = build_default_auditor(args.root, db_path=args.db)
    selected = _resolve_targets(args.root, list(args.targets))
    findings: List[FileFinding] = auditor.run(selected if selected else None)
    # saída simples no stdout
    for f in findings:
        print(f"{f.severity:>6} | {f.rule:<18} | {args.root.as_posix()}/" + f.path.relative_to(args.root).as_posix() + f" – {f.message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
