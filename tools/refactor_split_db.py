#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AST refactor: corta métodos do DatabaseManager e move p/ módulos.
Uso:
  python tools/refactor_split_db.py --src streamlit_extension/utils/database.py \
    --pkg streamlit_extension/database
"""
import ast, argparse, pathlib, textwrap
from typing import List, Dict

GROUPS = {
    "connection": [
        "get_connection", "release_connection", "transaction", "execute_query",
    ],
    "health": [
        "check_database_health", "get_query_statistics", "optimize_database",
        "create_backup", "restore_backup",
    ],
    "queries": [
        # ajuste a lista conforme seu projeto:
        "get_epics", "get_all_epics", "get_tasks", "get_all_tasks",
        "get_timer_sessions", "get_user_stats", "get_achievements",
        "get_epics_with_hierarchy", "get_all_epics_with_hierarchy",
        "get_hierarchy_overview", "get_client_dashboard", "get_project_dashboard",
        "create_client", "create_project", "update_client", "delete_client",
        "update_project", "delete_project", "update_epic_project",
        "get_client_by_key", "get_project_by_key",
    ],
}

HEADER = "# Auto-gerado por tools/refactor_split_db.py — NÃO EDITAR À MÃO\n"

def load(src: pathlib.Path) -> str:
    return src.read_text(encoding="utf-8", errors="ignore")

def dump(dst: pathlib.Path, text: str):
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")

def cut_methods(tree: ast.Module, class_name: str) -> Dict[str, ast.FunctionDef]:
    methods = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods[item.name] = item
            return methods
    raise SystemExit(f"Classe {class_name} não encontrada.")

def to_source(node: ast.AST) -> str:
    try:
        import astor
        return astor.to_source(node)
    except Exception:
        return ast.unparse(node)  # py>=3.9

def method_to_module_func(method: ast.FunctionDef) -> str:
    """Converte def m(self, ...) -> def m(manager, ...) mantendo corpo."""
    new_args = ast.arguments(
        posonlyargs=[],
        args=[ast.arg(arg="manager")] + method.args.args[1:],  # drop self
        vararg=method.args.vararg,
        kwonlyargs=method.args.kwonlyargs,
        kw_defaults=method.args.kw_defaults,
        kwarg=method.args.kwarg,
        defaults=method.args.defaults,
    )
    new_func = ast.FunctionDef(
        name=method.name,
        args=new_args,
        body=method.body,
        decorator_list=[],
        returns=method.returns,
        type_comment=method.type_comment,
    )
    ast.fix_missing_locations(new_func)
    src = to_source(new_func)
    # troca referências a self. por manager.
    src = src.replace("self.", "manager.")
    return src

def make_module(module_name: str, methods: List[ast.FunctionDef]) -> str:
    parts = [HEADER, "from __future__ import annotations\n\n"]
    for m in methods:
        parts.append(method_to_module_func(m))
        if not parts[-1].endswith("\n"):
            parts[-1] += "\n"
        parts.append("\n")
    return "".join(parts)

def wrap_method_call(mod_pkg: str, module_name: str, method: ast.FunctionDef) -> str:
    """Cria wrapper fino dentro do DatabaseManager chamando função do módulo."""
    args = [a.arg for a in method.args.args][1:]  # drop self
    call = f"return {mod_pkg}.{module_name}.{method.name}(self{',' if args else ''}{', '.join(args)})"
    src = f"def {method.name}({to_source(method.args).strip()[1:-1]}):\n    {call}\n"
    return src

def rewrite_database_py(src_path: pathlib.Path, pkg: str):
    text = load(src_path)
    tree = ast.parse(text)
    methods = cut_methods(tree, "DatabaseManager")
    # mapeia métodos -> grupo
    method_to_group = {}
    for g, names in GROUPS.items():
        for n in names:
            if n in methods:
                method_to_group[n] = g
    # gera módulos
    for g in GROUPS:
        group_methods = [methods[m] for m in methods if method_to_group.get(m) == g]
        if not group_methods:
            continue
        module_code = make_module(g, group_methods)
        dump(pathlib.Path(pkg) / f"{g}.py", module_code)
    # injeta imports e substitui métodos por wrappers
    imports_block = "\n".join([f"import {pkg}.{g}  # moved" for g in GROUPS.keys()]) + "\n"
    lines = text.splitlines()
    # injeta logo após imports existentes
    insert_at = 0
    for i,l in enumerate(lines[:200]):
        if l.strip().startswith("import") or l.strip().startswith("from"):
            insert_at = i
    lines.insert(insert_at+1, imports_block)
    text = "\n".join(lines)
    # substitui os corpos dos métodos por wrappers
    for name, g in method_to_group.items():
        wrapper = wrap_method_call(pkg, g, methods[name])
        # regex simplão: substitui método inteiro
        import re
        pattern = re.compile(rf"\n\s*def\s+{name}\s*\(.*?\):\n(?:\s+.*\n)+", re.DOTALL)
        repl = "\n    " + textwrap.indent(wrapper.rstrip(), "    ") + "\n"
        text, n = pattern.subn(repl, text, count=1)
        if n == 0:
            print(f"[WARN] Não consegui substituir corpo de {name} (padrão não bateu).")
    dump(src_path, text)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="caminho do database.py monolito")
    ap.add_argument("--pkg", required=True, help="pacote destino (ex: streamlit_extension/database)")
    args = ap.parse_args()
    src_path = pathlib.Path(args.src)
    pkg_path = pathlib.Path(args.pkg)
    if not src_path.exists():
        raise SystemExit(f"{src_path} não existe.")
    pkg_path.mkdir(parents=True, exist_ok=True)
    rewrite_database_py(src_path, args.pkg.replace("/", "."))
    print("Refactor concluído.")

if __name__ == "__main__":
    main()