"""
ScrumMasterOrchestrator — Orquestrador determinístico da geração/ordenação de épicos.

Princípios (alinhados ao PRD):
- A IA pode errar. A ordenação topológica é sempre aplicada pelo
  DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO.py e é a fonte de verdade.
- Não há perguntas ao usuário. Em caso de dados insuficientes, retornamos
  avisos estruturados (warnings) e bloqueamos a persistência.
- Auditoria: registrar model/version/explainer em framework_epic_ai_audit.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO import (
    Task,
    topological_sort_with_priority_corrected,
)

from streamlit_extension.database.ai_audit import log_epic_ai_ordering


Warnings = List[str]


@dataclass
class ScrumMasterOrchestrator:
    """Orquestra o fluxo entre geração IA e ordenação determinística."""

    def validate_epic_suggestions(self, epics: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Warnings]:
        """Normaliza e valida sugestões de épicos.

        Regras essenciais:
        - 3 ≤ qtd ≤ 7 (PRD)
        - dependencies deve referenciar apenas temp_keys existentes; ignorar desconhecidas com warning
        - effort_estimate ∈ [1..30], complexity_score ∈ [1.0..5.0]
        - name/description não vazios
        """
        warnings: Warnings = []
        if not isinstance(epics, list):
            return [], ["Entrada de épicos inválida (esperado lista)"]

        keys = [e.get("temp_key") for e in epics if isinstance(e, dict)]
        keyset = {k for k in keys if k}
        n = len(keyset)
        if n < 3 or n > 7:
            warnings.append(f"Quantidade de épicos fora do intervalo [3..7]: {n}")

        normalized: List[Dict[str, Any]] = []
        for e in epics:
            if not isinstance(e, Dict):
                warnings.append("Item de épico inválido; ignorado")
                continue
            k = str(e.get("temp_key") or "").strip()
            name = str(e.get("name") or "").strip()
            desc = str(e.get("description") or "").strip()
            deps = e.get("dependencies") or []
            try:
                deps = [d for d in (deps or []) if d in keyset and d != k]
            except Exception:
                deps = []
                warnings.append(f"Deps inválidas em {k}; resetadas")

            # Faixas
            eff = e.get("effort_estimate")
            try:
                eff = int(eff)
            except Exception:
                eff = None
            if not (isinstance(eff, int) and 1 <= eff <= 30):
                warnings.append(f"effort_estimate inválido em {k}; esperado [1..30]")
                eff = None

            comp = e.get("complexity_score")
            try:
                comp = float(comp)
            except Exception:
                comp = None
            if not (isinstance(comp, float) and 1.0 <= comp <= 5.0):
                warnings.append(f"complexity_score inválido em {k}; esperado [1.0..5.0]")
                comp = None

            if not name:
                warnings.append(f"name vazio em {k}")
            if not desc:
                warnings.append(f"description vazia em {k}")

            normalized.append({
                "temp_key": k,
                "name": name,
                "description": desc,
                "dependencies": deps,
                "effort_estimate": eff,
                "complexity_score": comp,
                # prioridade opcional (1..5); default 3
                "priority": max(1, min(5, int(e.get("priority", 3) or 3))) if str(e.get("priority", "")).isdigit() else 3,
            })

        return normalized, warnings

    def run_ordering(self, epics: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, Any], Warnings]:
        """Aplica a ordenação topológica determinística.

        Retorna (execution_order[temp_key], scores_by_key, warnings)
        """
        warnings: Warnings = []
        normalized, w = self.validate_epic_suggestions(epics)
        warnings.extend(w)

        # Construir tarefas para o algoritmo
        tasks: List[Task] = []
        for e in normalized:
            t = Task(
                task_key=e["temp_key"],
                priority=e.get("priority", 3),
                effort_estimate=e.get("effort_estimate") or 1,
            )
            tasks.append(t)

        # Construir pares (dependente, prerequisito)
        deps_pairs: List[Tuple[str, str]] = []
        for e in normalized:
            for d in e.get("dependencies", []):
                deps_pairs.append((e["temp_key"], d))

        # Rodar algoritmo determinístico
        try:
            execution_order, task_scores, exec_ms = topological_sort_with_priority_corrected(tasks, deps_pairs)
        except Exception as exc:
            warnings.append(f"Falha ao ordenar topologicamente: {exc}")
            return [], {}, warnings

        # Validação de cobertura: se nem todos foram ordenados, há ciclo ou inconsistência
        if len(execution_order) != len({e["temp_key"] for e in normalized}):
            warnings.append("Ordenação incompleta: verifique ciclos/dependências inválidas.")
            return [], {}, warnings

        # Converter scores para dict simples
        scores: Dict[str, Any] = {
            k: {
                "total": v.total_score,
                "priority": v.priority_score,
                "value_density": v.value_density_score,
                "unblock": v.unblock_score,
                "critical_path": v.critical_path_score,
                "tdd_bonus": v.tdd_bonus_score,
                "aging": v.aging_score,
            }
            for k, v in task_scores.items()
        }

        return execution_order, scores, warnings

    def persist_order_and_dependencies(
        self,
        project_id: int,
        temp_to_epic_id: Dict[str, int],
        execution_order: List[str],
        dependencies: List[Tuple[str, str]],
    ) -> None:
        """Persiste sort_order por projeto e dependências N:N.

        Args:
            project_id: ID do projeto
            temp_to_epic_id: mapping temp_key→epic_id persistido
            execution_order: lista ordenada de temp_keys
            dependencies: pares (dependent_temp_key, prerequisite_temp_key)
        """
        from streamlit_extension.database.connection import execute

        # Atualizar sort_order sequencial por projeto
        for idx, tk in enumerate(execution_order, start=1):
            epic_id = temp_to_epic_id.get(tk)
            if epic_id:
                execute(
                    "UPDATE framework_epics SET sort_order = ? WHERE id = ? AND project_id = ?",
                    (idx, epic_id, project_id),
                )

        # Inserir dependências válidas
        for dependent_tk, prereq_tk in dependencies:
            dep_id = temp_to_epic_id.get(dependent_tk)
            pre_id = temp_to_epic_id.get(prereq_tk)
            if dep_id and pre_id and dep_id != pre_id:
                try:
                    execute(
                        "INSERT INTO framework_epic_dependencies (project_id, epic_id, depends_on_epic_id) VALUES (?, ?, ?)",
                        (project_id, dep_id, pre_id),
                    )
                except Exception:
                    # Dependência duplicada ou FK inválida — ignorar silenciosamente
                    pass

    def audit_ordering(
        self,
        project_id: int,
        ordered_temp_keys: List[str],
        temp_to_epic_id: Dict[str, int],
        model: str,
        version: str,
        explainer: str,
    ) -> None:
        """Grava auditoria por épico (epic_id) na tabela framework_epic_ai_audit."""
        for tk in ordered_temp_keys:
            epic_id = temp_to_epic_id.get(tk)
            if epic_id:
                log_epic_ai_ordering(epic_id=epic_id, project_id=project_id, model=model, version=version, explainer=explainer)
