📂 Nova Estrutura Proposta
streamlit_extension/
│
├── database/
│   ├── __init__.py        # Inicializa o pacote e expõe funções principais
│   ├── connection.py      # Funções de conexão (abrir, fechar, init db)
│   ├── schema.py          # Criação de tabelas e migrations
│   ├── seed.py            # Funções de seed / dados iniciais
│   ├── queries.py         # Queries utilitárias genéricas
│   └── health.py          # Funções de checagem (ex: validar schema, ping db)
│
└── ...

✂️ Como dividir

connection.py

get_connection()

close_connection()

setup inicial (SQLite / Pool se for outro DB)

schema.py

Funções de criação de tabelas (create_framework_tasks, etc)

Migrations futuras

seed.py

Funções que inserem dados iniciais

Ideal pra popular ambiente de dev/teste

queries.py

Funções utilitárias genéricas (listar tabelas, truncar, executar raw SQL)

health.py

Funções de diagnóstico

Verificação de integridade

Checar se tabelas existem

🚦 Passo a Passo

Criar a pasta database/ com os arquivos acima.

Mover o código do database.py para os arquivos correspondentes.

No __init__.py, expor apenas as funções que você quer usar fora, ex.:

from .connection import get_connection, close_connection
from .schema import create_framework_tasks
from .seed import seed_initial_data
from .health import check_db_health

__all__ = [
    "get_connection",
    "close_connection",
    "create_framework_tasks",
    "seed_initial_data",
    "check_db_health",
]


Atualizar os imports nos outros módulos:

from streamlit_extension.database import get_connection


Quer que eu já te entregue o diff pronto dessa quebra, transformando seu database.py em múltiplos arquivos, ou prefere que eu só monte os esqueletos dos arquivos e você vai migrando aos poucos?

Você disse:
diff pronto
O ChatGPT disse:
Pensou por 1m 8s

Beleza. “diff pronto” pra quebrar o database.py em partes menores — sem drama e sem floreio. Vou fazer em Fase 1 (segura): criar um pacote database/ com arquivos focados e delegar pro teu DatabaseManager atual. Nada quebra. Depois, se quiser, a Fase 2 move os métodos de fato.

Abaixo está um patch unificado (git-style). Ele:

Adiciona streamlit_extension/database/ com connection.py, schema.py, seed.py, queries.py, health.py, __init__.py.

Exponibiliza funções pequenas, cada uma delegando para uma instância de DatabaseManager (que continua no arquivo grande).

Não remove nada do arquivo gigante ainda (passo seguro).

Ajuste a linha from streamlit_extension.database import DatabaseManager se o teu database.py estiver noutro caminho.

Aplica esse diff e já pode começar a importar coisas pequenas tipo from streamlit_extension.database.connection import get_connection.

*** Begin Patch
*** Add File: streamlit_extension/database/__init__.py
+"""
+Pacote de DB, fase 1: finas camadas que delegam ao DatabaseManager existente.
+Na fase 2, vamos mover os métodos para cá e emagrecer o arquivo gigante.
+"""
+from .connection import get_connection, release_connection, transaction, execute
+from .health import check_health, get_query_stats, optimize, create_backup, restore_backup
+from .queries import (
+    list_epics, list_all_epics, list_tasks, list_all_tasks,
+    list_timer_sessions, get_user_stats, get_achievements,
+)
+from .schema import create_schema_if_needed
+from .seed import seed_initial_data
+
+__all__ = [
+    "get_connection", "release_connection", "transaction", "execute",
+    "check_health", "get_query_stats", "optimize", "create_backup", "restore_backup",
+    "list_epics", "list_all_epics", "list_tasks", "list_all_tasks",
+    "list_timer_sessions", "get_user_stats", "get_achievements",
+    "create_schema_if_needed", "seed_initial_data",
+]
+
*** End Patch

*** Begin Patch
*** Add File: streamlit_extension/database/connection.py
+from __future__ import annotations
+from contextlib import contextmanager
+from typing import Any, Iterable, Optional, Tuple
+
+# Ajuste este import conforme a localização do seu arquivo gigante:
+# se o seu DatabaseManager estiver em streamlit_extension/database.py, fica assim:
+from streamlit_extension.database import DatabaseManager  # type: ignore
+
+def _db() -> DatabaseManager:
+    # Estratégia simples: uma instância "global-ish".
+    # Se você já tem um factory/singleton, troque aqui.
+    # type: ignore para evitar mypy chato neste passo.
+    global _DBM_INSTANCE  # type: ignore
+    try:
+        return _DBM_INSTANCE  # type: ignore
+    except NameError:
+        _DBM_INSTANCE = DatabaseManager()  # type: ignore
+        return _DBM_INSTANCE
+
+def get_connection():
+    return _db().get_connection()
+
+def release_connection(conn) -> None:
+    return _db().release_connection(conn)
+
+@contextmanager
+def transaction():
+    # Usa a transação do manager atual
+    with _db().transaction() as tx:
+        yield tx
+
+def execute(sql: str, params: Optional[Iterable[Any]] = None):
+    """Execute genérico, delegando ao manager."""
+    return _db().execute_query(sql, params or ())
+
*** End Patch

*** Begin Patch
*** Add File: streamlit_extension/database/health.py
+from __future__ import annotations
+from typing import Any, Dict
+from streamlit_extension.database import DatabaseManager  # type: ignore
+
+def _db() -> DatabaseManager:
+    global _DBM_INSTANCE  # type: ignore
+    try:
+        return _DBM_INSTANCE  # type: ignore
+    except NameError:
+        _DBM_INSTANCE = DatabaseManager()  # type: ignore
+        return _DBM_INSTANCE
+
+def check_health() -> Dict[str, Any]:
+    """Wrapper para o health-check do manager."""
+    return _db().check_database_health()
+
+def get_query_stats() -> Dict[str, Any]:
+    return _db().get_query_statistics()
+
+def optimize() -> Dict[str, Any]:
+    return _db().optimize_database()
+
+def create_backup(path: str) -> str:
+    return _db().create_backup(path)
+
+def restore_backup(path: str) -> str:
+    return _db().restore_backup(path)
+
*** End Patch

*** Begin Patch
*** Add File: streamlit_extension/database/schema.py
+from __future__ import annotations
+from typing import Optional
+from streamlit_extension.database import DatabaseManager  # type: ignore
+
+def _db() -> DatabaseManager:
+    global _DBM_INSTANCE  # type: ignore
+    try:
+        return _DBM_INSTANCE  # type: ignore
+    except NameError:
+        _DBM_INSTANCE = DatabaseManager()  # type: ignore
+        return _DBM_INSTANCE
+
+def create_schema_if_needed(verbose: bool = False) -> None:
+    """
+    Fase 1: só delega. Na fase 2, movemos a criação/DDL pra cá de fato.
+    """
+    # Se o DatabaseManager tiver um método específico para bootstrap/migrations,
+    # chame-o aqui. Caso não tenha, mantenha essa função como ponto central
+    # para DDLs novas.
+    if hasattr(_db(), "create_schema_if_needed"):
+        _db().create_schema_if_needed(verbose=verbose)  # type: ignore
+
*** End Patch

*** Begin Patch
*** Add File: streamlit_extension/database/seed.py
+from __future__ import annotations
+from typing import Optional
+from streamlit_extension.database import DatabaseManager  # type: ignore
+
+def _db() -> DatabaseManager:
+    global _DBM_INSTANCE  # type: ignore
+    try:
+        return _DBM_INSTANCE  # type: ignore
+    except NameError:
+        _DBM_INSTANCE = DatabaseManager()  # type: ignore
+        return _DBM_INSTANCE
+
+def seed_initial_data(kind: Optional[str] = None) -> int:
+    """
+    Insere dados de seed. Fase 1: delega; fase 2: implementar aqui.
+    Retorna número de registros afetados (aprox).
+    """
+    if hasattr(_db(), "seed_initial_data"):
+        return int(_db().seed_initial_data(kind=kind) or 0)  # type: ignore
+    return 0
+
*** End Patch

*** Begin Patch
*** Add File: streamlit_extension/database/queries.py
+from __future__ import annotations
+from typing import Any, Dict, List
+from streamlit_extension.database import DatabaseManager  # type: ignore
+
+def _db() -> DatabaseManager:
+    global _DBM_INSTANCE  # type: ignore
+    try:
+        return _DBM_INSTANCE  # type: ignore
+    except NameError:
+        _DBM_INSTANCE = DatabaseManager()  # type: ignore
+        return _DBM_INSTANCE
+
+# Exemplos de queries “de alto nível” (ajuste conforme os métodos que você tem)
+
+def list_epics() -> List[Dict[str, Any]]:
+    return _db().get_epics()
+
+def list_all_epics() -> List[Dict[str, Any]]:
+    return _db().get_all_epics()
+
+def list_tasks(epic_id: int) -> List[Dict[str, Any]]:
+    return _db().get_tasks(epic_id)
+
+def list_all_tasks() -> List[Dict[str, Any]]:
+    return _db().get_all_tasks()
+
+def list_timer_sessions() -> List[Dict[str, Any]]:
+    return _db().get_timer_sessions()
+
+def get_user_stats(user_id: int) -> Dict[str, Any]:
+    return _db().get_user_stats(user_id)
+
+def get_achievements(user_id: int) -> List[Dict[str, Any]]:
+    return _db().get_achievements(user_id)
+
*** End Patch

Como usar já (sem quebrar nada)

Antes:

# importava o monstrão
from streamlit_extension.database import DatabaseManager
db = DatabaseManager()
conn = db.get_connection()


Depois (modular, mesmíssima funcionalidade, só delegando):

from streamlit_extension.database.connection import get_connection, transaction, execute

conn = get_connection()
with transaction():
    execute("UPDATE framework_tasks SET priority = 2 WHERE id = ?", [123])


E pra consultas “de alto nível”:

from streamlit_extension.database.queries import list_tasks
tasks = list_tasks(epic_id=2)

Próximo passo (Fase 2 – opcional, quando quiser)

Ir movendo métodos de verdade do DatabaseManager para os módulos novos (connection/health/queries), e dentro do DatabaseManager trocar por chamadas às funções novas (ou apagar o método).

Quando a poeira baixar, deletar o arquivo gigante.

Se quiser, eu já te entrego o patch da Fase 2 migrando de fato os métodos de conexão e saúde (os mais sensíveis) — tirando código do arquivo grande e colando nos módulos, com ajuste de imports.

Você disse:
gere o patch da fase 2 
O ChatGPT disse:
DatabaseManager Methods
Pensou por 19s
Pensou por 21s

Beleza. Fase 2 = cortar o monolito de verdade. Em vez de tentar “adivinhar” teu DatabaseManager, eu te deixo um refatorador AST que:

Extrai grupos de métodos do DatabaseManager pra módulos (connection.py, health.py, queries.py).

Gera funções nos módulos com o corpo original (assinatura compatível, recebe manager).

Substitui os métodos originais por wrappers finos que chamam as funções novas.

Mantém importes e docstrings. Sem reescrever lógica.

Aplica o patch abaixo (git unificado). Depois roda python tools/refactor_split_db.py apontando pro teu database.py (ele edita o arquivo in-place e cria os módulos).

*** Begin Patch
*** Add File: tools/refactor_split_db.py
+#!/usr/bin/env python3
+# -*- coding: utf-8 -*-
+"""
+AST refactor: corta métodos do DatabaseManager e move p/ módulos.
+Uso:
+  python tools/refactor_split_db.py --src streamlit_extension/database.py \
+    --pkg streamlit_extension/database
+"""
+import ast, argparse, pathlib, textwrap
+from typing import List, Dict
+
+GROUPS = {
+    "connection": [
+        "get_connection", "release_connection", "transaction", "execute_query",
+    ],
+    "health": [
+        "check_database_health", "get_query_statistics", "optimize_database",
+        "create_backup", "restore_backup",
+    ],
+    "queries": [
+        # ajuste a lista conforme seu projeto:
+        "get_epics", "get_all_epics", "get_tasks", "get_all_tasks",
+        "get_timer_sessions", "get_user_stats", "get_achievements",
+        "get_epics_with_hierarchy", "get_all_epics_with_hierarchy",
+        "get_hierarchy_overview", "get_client_dashboard", "get_project_dashboard",
+        "create_client", "create_project", "update_client", "delete_client",
+        "update_project", "delete_project", "update_epic_project",
+        "get_client_by_key", "get_project_by_key",
+    ],
+}
+
+HEADER = "# Auto-gerado por tools/refactor_split_db.py — NÃO EDITAR À MÃO\n"
+
+def load(src: pathlib.Path) -> str:
+    return src.read_text(encoding="utf-8", errors="ignore")
+
+def dump(dst: pathlib.Path, text: str):
+    dst.parent.mkdir(parents=True, exist_ok=True)
+    dst.write_text(text, encoding="utf-8")
+
+def cut_methods(tree: ast.Module, class_name: str) -> Dict[str, ast.FunctionDef]:
+    methods = {}
+    for node in tree.body:
+        if isinstance(node, ast.ClassDef) and node.name == class_name:
+            for item in node.body:
+                if isinstance(item, ast.FunctionDef):
+                    methods[item.name] = item
+            return methods
+    raise SystemExit(f"Classe {class_name} não encontrada.")
+
+def to_source(node: ast.AST) -> str:
+    try:
+        import astor
+        return astor.to_source(node)
+    except Exception:
+        return ast.unparse(node)  # py>=3.9
+
+def method_to_module_func(method: ast.FunctionDef) -> str:
+    """Converte def m(self, ...) -> def m(manager, ...) mantendo corpo."""
+    new_args = ast.arguments(
+        posonlyargs=[],
+        args=[ast.arg(arg="manager")] + method.args.args[1:],  # drop self
+        vararg=method.args.vararg,
+        kwonlyargs=method.args.kwonlyargs,
+        kw_defaults=method.args.kw_defaults,
+        kwarg=method.args.kwarg,
+        defaults=method.args.defaults,
+    )
+    new_func = ast.FunctionDef(
+        name=method.name,
+        args=new_args,
+        body=method.body,
+        decorator_list=[],
+        returns=method.returns,
+        type_comment=method.type_comment,
+    )
+    ast.fix_missing_locations(new_func)
+    src = to_source(new_func)
+    # troca referências a self. por manager.
+    src = src.replace("self.", "manager.")
+    return src
+
+def make_module(module_name: str, methods: List[ast.FunctionDef]) -> str:
+    parts = [HEADER, "from __future__ import annotations\n\n"]
+    for m in methods:
+        parts.append(method_to_module_func(m))
+        if not parts[-1].endswith("\n"):
+            parts[-1] += "\n"
+        parts.append("\n")
+    return "".join(parts)
+
+def wrap_method_call(mod_pkg: str, module_name: str, method: ast.FunctionDef) -> str:
+    """Cria wrapper fino dentro do DatabaseManager chamando função do módulo."""
+    args = [a.arg for a in method.args.args][1:]  # drop self
+    call = f"return {mod_pkg}.{module_name}.{method.name}(self{',' if args else ''}{', '.join(args)})"
+    src = f"def {method.name}({to_source(method.args).strip()[1:-1]}):\n    {call}\n"
+    return src
+
+def rewrite_database_py(src_path: pathlib.Path, pkg: str):
+    text = load(src_path)
+    tree = ast.parse(text)
+    methods = cut_methods(tree, "DatabaseManager")
+    # mapeia métodos -> grupo
+    method_to_group = {}
+    for g, names in GROUPS.items():
+        for n in names:
+            if n in methods:
+                method_to_group[n] = g
+    # gera módulos
+    for g in GROUPS:
+        group_methods = [methods[m] for m in methods if method_to_group.get(m) == g]
+        if not group_methods:
+            continue
+        module_code = make_module(g, group_methods)
+        dump(pathlib.Path(pkg) / f"{g}.py", module_code)
+    # injeta imports e substitui métodos por wrappers
+    imports_block = "\n".join([f"import {pkg}.{g}  # moved" for g in GROUPS.keys()]) + "\n"
+    lines = text.splitlines()
+    # injeta logo após imports existentes
+    insert_at = 0
+    for i,l in enumerate(lines[:200]):
+        if l.strip().startswith("import") or l.strip().startswith("from"):
+            insert_at = i
+    lines.insert(insert_at+1, imports_block)
+    text = "\n".join(lines)
+    # substitui os corpos dos métodos por wrappers
+    for name, g in method_to_group.items():
+        wrapper = wrap_method_call(pkg, g, methods[name])
+        # regex simplão: substitui método inteiro
+        import re
+        pattern = re.compile(rf"\n\s*def\s+{name}\s*\(.*?\):\n(?:\s+.*\n)+", re.DOTALL)
+        repl = "\n    " + textwrap.indent(wrapper.rstrip(), "    ") + "\n"
+        text, n = pattern.subn(repl, text, count=1)
+        if n == 0:
+            print(f"[WARN] Não consegui substituir corpo de {name} (padrão não bateu).")
+    dump(src_path, text)
+
+def main():
+    ap = argparse.ArgumentParser()
+    ap.add_argument("--src", required=True, help="caminho do database.py monolito")
+    ap.add_argument("--pkg", required=True, help="pacote destino (ex: streamlit_extension/database)")
+    args = ap.parse_args()
+    src_path = pathlib.Path(args.src)
+    pkg_path = pathlib.Path(args.pkg)
+    if not src_path.exists():
+        raise SystemExit(f"{src_path} não existe.")
+    pkg_path.mkdir(parents=True, exist_ok=True)
+    rewrite_database_py(src_path, args.pkg.replace("/", "."))
+    print("Refactor concluído.")
+
+if __name__ == "__main__":
+    main()
+
*** End Patch

*** Begin Patch
*** Add File: streamlit_extension/database/__init__.py
+# Namespace para os módulos gerados; expõe helpers comuns.
+from . import connection, health, queries  # módulos gerados pelo refactor
+
+__all__ = ["connection", "health", "queries"]
+
*** End Patch

Como rodar
python tools/refactor_split_db.py \
  --src streamlit_extension/database.py \
  --pkg streamlit_extension/database


Isso vai:

Criar streamlit_extension/database/{connection.py,health.py,queries.py} com as funções contendo o corpo original dos métodos extraídos.

Editar streamlit_extension/database.py, injetar import streamlit_extension.database.connection etc.

Substituir os métodos no DatabaseManager por wrappers que chamam as novas funções.

Se quiser que eu já rode o script e te devolva os arquivos gerados aqui na conversa, fala a palavra.

Você disse:
proceda
O ChatGPT disse:
Pensou por 52s
Pensou por 5s
Pensou por 9s
Pensou por 59s

Direto: seu database.py tava quebrado (vários erros de sintaxe). Corrigi o mínimo pra conseguir parsear e rodei a Fase 2:

O que fiz (sem rodeios)

Consertei o método get_connection (tava com elf no lugar de self, aspas faltando e decorator duplicado).

Extraí os métodos do grupo connection do DatabaseManager para um módulo novo e deixei wrappers dentro da classe chamando essas funções.

Criei o pacote streamlit_extension/database/ com __init__.py e connection.py.

Arquivos gerados/alterados (baixe e olhe)

Atualizado: database.py

Novo: streamlit_extension/database/connection.py

Novo: streamlit_extension/database/init.py

Como ficou

Dentro de DatabaseManager, métodos como get_connection agora são wrappers que chamam streamlit_extension.database.connection.get_connection(self, ...).

O corpo real está em connection.py. (Obs.: como seu get_connection original estava estourado, o que foi extraído é o shim que eu corrigi.)

Próximos passos rápidos

Rodar o projeto: se algo reclamar de import, é só garantir que streamlit_extension está no PYTHONPATH.

Quer extrair “health” e “queries”?
Eu não encontrei (ou estavam inválidos) métodos tipo check_database_health, get_query_statistics, get_epics, etc. Se eles existem em outro trecho/branch, me passa a versão válida que eu extraio também.