Erros/risquinhos imediatos

Dataclass vs SELECT: você seleciona task_group, task_sequence, mas Task não tem esses campos. Task(**row) vai quebrar. Ou adiciona os campos na dataclass, ou remove do SELECT.

Row factory: Task(**row) só funciona se fetchall() devolver dict-like. Garanta row_factory = sqlite3.Row (ou mapeie manualmente).

hasattr(task, 'task_group'): hoje sempre falso (vide item 1). E mesmo com o campo, hasattr é redundante: inicialize task_group na dataclass.

DAG check recebe in_degree e ignora: parâmetro morto. Não atrapalha, mas suja a API.

Cálculo de caminho crítico caro: você chama _calculate_critical_path DENTRO do score (muitas vezes). Resultado: O(V·E). Faça memo global 1x por grafo ou pré-compute para todos os nós.

value_density confuso: complexity/effort dá score maior para tasks com mais story points (!). Se story_points já é esforço, use priority / effort (ou defina claramente que SP mede “valor”, o que é incomum).

Colunas derivadas no DB: depends_on_count, blocks_count, critical_path_length são deriváveis do grafo. Persistir tende a desatualizar. Calcule em runtime ou mantenha via trigger.

ALTER TABLE: em SQLite não há IF NOT EXISTS por coluna; rodar duas vezes estoura. Proteja com checagem de pragma ou migração versionada.

TDD “analysis”: você separou task_type, ok; então tire “analysis” do mapping de tdd_phase. Evita incoerência semântica.

Tie-breaker do heap: hoje usa só (-score, task_key). Pode gerar ordem pouco estável. Adicione desempate por (prioridade desc, estimate asc, task_key).

Melhorias de arquitetura

Fonte da verdade: bom ter migrado JSON→DB. Crie índices:
task_dependencies(task_id), task_dependencies(depends_on_task_key), framework_tasks(epic_id, task_key).

Caminho crítico ponderado: use duração (ex.: estimate_minutes) como peso, não 1 por nó.

Paralelização por níveis: seu batching tá ok, mas você revarre tudo a cada rodada. Dá pra reaproveitar o in_degree estilo Kahn por camada (O(V+E)).

Aging anti-fome: se quiser evitar starvation de tarefa média, acrescente um +ε por “rodada esperando”.

Patches cirúrgicos
1) Dataclass e SELECT alinhados
@dataclass
class Task:
    id: int
    task_key: str
    epic_id: int
    tdd_phase: Optional[str]
    tdd_order: Optional[int]
    task_type: str
    priority: int
    story_points: Optional[int]
    estimate_minutes: Optional[int]
    task_group: Optional[str] = None
    task_sequence: Optional[int] = None


E garanta:

conn.row_factory = sqlite3.Row

2) Grafo + pré-cálculos eficientes
def build_dependency_graph(...):
    ...
    # compute out_degree ao montar adj
    out_degree = {k: 0 for k in task_map}
    for src in adjacency:
        out_degree[src] = len(adjacency[src])
    # critical path PONDERADO por estimate_minutes (default 1)
    critical = _longest_path_weighted(adjacency, task_map)
    return adjacency, in_degree, task_map, out_degree, critical

def _longest_path_weighted(adj, task_map):
    topo = _topo_order_unscored(adj)  # simples Kahn sem heap
    dur = {k: max(task_map[k].estimate_minutes or 1, 1) for k in task_map}
    dist = {k: dur[k] for k in task_map}
    for u in topo:
        for v in adj[u]:
            if dist[v] < dist[u] + dur[v]:
                dist[v] = dist[u] + dur[v]
    return dist  # tempo total até o fim via melhor caminho

3) Score claro (maior = melhor)
def calculate_priority_score(task, out_degree, critical_time, wait_age=0):
    # pesos
    W_PRIO, W_DENS, W_UNBLOCK, W_CRIT, W_TDD, W_AGING = 10, 6, 3, 2, 1, 0.2

    prio = max(1, min(5, task.priority or 3))  # 1=crítico
    effort = max(task.estimate_minutes or task.story_points or 1, 1)
    dens  = (1.0 * (6 - prio)) / effort        # valor/tempo (aprox)

    tdd_bonus = 0
    if task.tdd_order:
        tdd_bonus = (4 - task.tdd_order)  # red>green>refactor

    return (
        W_PRIO * (6 - prio) +
        W_DENS * dens +
        W_UNBLOCK * out_degree.get(task.task_key, 0) +
        W_CRIT * (critical_time.get(task.task_key, 0)) +
        W_TDD  * tdd_bonus +
        W_AGING * wait_age
    )

4) Kahn com prioridade + tie-break
def topological_sort_with_priority(...):
    adj, indeg, tasks, outdeg, crit = build_dependency_graph(epic_id)
    ready = []
    for k, d in indeg.items():
        if d == 0:
            s = calculate_priority_score(tasks[k], outdeg, crit)
            heapq.heappush(ready, (-s, -(6 - (tasks[k].priority or 3)), tasks[k].estimate_minutes or 10**9, k))

    order = []
    while ready:
        _, _, _, u = heapq.heappop(ready)
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                s = calculate_priority_score(tasks[v], outdeg, crit)
                heapq.heappush(ready, (-s, -(6 - (tasks[v].priority or 3)), tasks[v].estimate_minutes or 10**9, v))
    if len(order) != len(tasks):
        raise CyclicDependencyError("Ciclo ou dados faltando")
    return order

5) Batching linear por níveis
def get_parallel_batches(epic_id, max_parallel=5):
    adj, indeg, tasks, outdeg, crit = build_dependency_graph(epic_id)
    # fila por prioridade a cada nível
    batches = []
    ready = []
    for k, d in indeg.items():
        if d == 0:
            s = calculate_priority_score(tasks[k], outdeg, crit)
            heapq.heappush(ready, (-s, k))
    done = set()
    while ready:
        batch = []
        tmp = []
        while ready and len(batch) < max_parallel:
            _, u = heapq.heappop(ready)
            batch.append(u)
        batches.append(batch)
        for u in batch:
            done.add(u)
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    s = calculate_priority_score(tasks[v], outdeg, crit)
                    heapq.heappush(tmp, (-s, v))
        ready = tmp
    if len(done) != len(tasks):
        missing = set(tasks) - done
        raise RuntimeError(f"Deadlock/pendências inválidas: {missing}")
    return batches

6) Migração segura (SQLite)

Antes de cada ALTER TABLE, cheque:

PRAGMA table_info(framework_tasks);
-- só adicione se a coluna não existir


Crie índices:

CREATE INDEX IF NOT EXISTS idx_tasks_epic_key ON framework_tasks(epic_id, task_key);
CREATE INDEX IF NOT EXISTS idx_td_task ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_td_depkey ON task_dependencies(depends_on_task_key);

TL;DR

Ajuste a dataclass/SELECT (bug certo).

Pré-compute caminho crítico (ponderado por duração).

Score = valor/tempo + desbloqueio + criticidade + bônus TDD, com pesos.

Kahn com heap e desempates determinísticos.

Batching por níveis sem varredura O(n²).

Evite colunas derivadas no DB (ou mantenha com trigger).