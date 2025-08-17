Pontos a melhorar (rápido)

Ordenação “humana”: ORDER BY task_key dá T10 antes de T2. Se você tem task_sequence, use-o como primário e task_key como fallback.

Duplicatas no IN: list_by_task_keys pode devolver duplicado se a lista entrar com chaves repetidas. Dedup rápido no input ou no output.

row.get no except: quando o parse falha você tenta row.get. Em sqlite3.Row não tem get. Você já protegeu com hasattr, mas é melhor padronizar: task_key = dict(row).get('task_key','unknown').

Erros de parse: você loga contagem, mas não retorna contexto. Vale incluir até 3 task_keys problemáticas no log pra depurar.

Consistência de exceções: agora tudo levanta RepoError (ok). Só garanta que camadas acima não silenciem isso.

Paginação: list_by_epic pode crescer. Preveja limit/offset opcionais.

Índices: só reforçando — garanta framework_tasks(epic_id, task_key) e framework_tasks(task_key) único se fizer sentido.

Patches cirúrgicos
1) Ordenação natural
def list_by_epic(self, epic_id: int) -> List[Task]:
    sql = f"""
      SELECT {BASE_FIELDS}
      FROM framework_tasks
      WHERE epic_id=? AND deleted_at IS NULL
      ORDER BY COALESCE(task_sequence, 1e9), task_key
    """
    ...

2) Dedup no IN (na entrada)
def list_by_task_keys(self, task_keys: List[str]) -> List[Task]:
    if not task_keys:
        return []
    # remove duplicatas preservando ordem
    seen, uniq = set(), []
    for k in task_keys:
        if k not in seen:
            seen.add(k); uniq.append(k)
    task_keys = uniq
    ...

3) task_key seguro em erros de parse
try:
    task = Task.from_db_row(dict(row))
    tasks.append(task)
except Exception as e:
    r = dict(row)
    task_key = r.get('task_key','unknown')
    logger.warning(f"Parse error tarefa {task_key}: {e}")
    parse_errors += 1

4) Paginação opcional
def list_by_epic(self, epic_id: int, limit: int|None=None, offset: int=0) -> List[Task]:
    base = f"""
      SELECT {BASE_FIELDS}
      FROM framework_tasks
      WHERE epic_id=? AND deleted_at IS NULL
      ORDER BY COALESCE(task_sequence, 1e9), task_key
    """
    sql = base + (" LIMIT ? OFFSET ?" if limit is not None else "")
    params = (epic_id,) if limit is None else (epic_id, limit, offset)
    with dict_rows(self.conn):
        rows = self.conn.execute(sql, params).fetchall()
    return [Task.from_db_row(dict(r)) for r in rows]

5) Sumário: evite divisão por zero (já tá) e padronize tipos
completion = round((completed_tasks / total_tasks * 100), 1) if total_tasks else 0.0

Coisas boas que você já acertou

BASE_FIELDS DRY ✅

RepoError consistente ✅

dict_rows isolando row_factory ✅

Chunking no IN ✅

SELECTs enxutos e coerentes com Task ✅

Se quiser, eu integro essas melhorias direto no arquivo e gero 3 testes rápidos pro repo (list_by_epic com sequence, IN com duplicatas, e parse error logando task_key).

Você disse: