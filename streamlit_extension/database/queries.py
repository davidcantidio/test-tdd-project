from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from streamlit_extension.utils.database import DatabaseManager  # type: ignore
from .connection import execute_cached_query, get_optimized_connection

_DBM_INSTANCE: DatabaseManager | None = None  # type: ignore
_DBM_LOCK = threading.Lock()


# SEMANTIC DEDUPLICATION: Use centralized singleton instead of duplicate implementation
from .database_singleton import get_database_manager as _db
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


# =============================================================================
# Adaptação compatível com a API legada (delegação ao DatabaseManager)
# =============================================================================

def list_epics() -> List[Dict[str, Any]]:
    """Lista epics conforme regra do DatabaseManager legado."""
    return _db().get_epics()


def list_all_epics() -> List[Dict[str, Any]]:
    """Lista todos os epics (incluindo arquivados/deletados, se suportado)."""
    return _db().get_all_epics()


def list_tasks(epic_id: int) -> List[Dict[str, Any]]:
    """Lista tasks de um epic específico (via legado)."""
    return _db().get_tasks(epic_id)


def list_all_tasks() -> List[Dict[str, Any]]:
    """Lista todas as tasks via legado (pode ser custoso)."""
    return _db().get_all_tasks()


def list_timer_sessions() -> List[Dict[str, Any]]:
    """Retorna sessões de timer agregadas pelo manager legado."""
    return _db().get_timer_sessions()


def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Métricas agregadas por usuário (via legado)."""
    return _db().get_user_stats(user_id)


def get_achievements(user_id: int) -> List[Dict[str, Any]]:
    """Conquistas/gamificação do usuário (via legado)."""
    return _db().get_achievements(user_id)


# =============================================================================
# ⚡ PERFORMANCE-OPTIMIZED QUERIES (alinhadas ao schema atual)
# =============================================================================

def list_epics_optimized(cache_ttl: int = 300) -> List[Dict[str, Any]]:
    """
    Lista epics com SELECT enxuto + cache.

    Columns existentes (schema atual):
      - id, epic_key, name, description, status, priority, duration_days, progress,
        created_at, updated_at
    """
    sql = """
        SELECT
            id,
            epic_key,
            name,
            description,
            status,
            priority,
            duration_days,
            progress,
            created_at,
            updated_at
        FROM framework_epics
        ORDER BY priority ASC, created_at DESC
    """
    return execute_cached_query(sql, cache_ttl=cache_ttl)


def list_tasks_optimized(epic_id: int, cache_ttl: int = 120) -> List[Dict[str, Any]]:
    """
    Lista tasks de um epic com JOIN para trazer dados do epic.

    Columns existentes (schema atual):
      - tasks: id, task_key, epic_id, title, description, tdd_phase, status,
               estimate_minutes, created_at, updated_at
      - epics: id, name, epic_key
    """
    sql = """
        SELECT
            t.id,
            t.task_key,
            t.epic_id,
            t.title,
            t.description,
            t.tdd_phase,
            t.status,
            t.estimate_minutes,
            t.created_at,
            t.updated_at,
            e.name  AS epic_name,
            e.epic_key
        FROM framework_tasks AS t
        JOIN framework_epics AS e ON t.epic_id = e.id
        WHERE t.epic_id = ?
        ORDER BY t.created_at DESC, t.id DESC
    """
    return execute_cached_query(sql, params=(epic_id,), cache_ttl=cache_ttl)


def get_epic_summary_optimized(epic_id: int, cache_ttl: int = 180) -> Optional[Dict[str, Any]]:
    """
    Retorna um resumo do epic com agregados de tasks.

    Observações:
      - completion_percentage calculado como tasks concluídas / total.
    """
    sql = """
        SELECT
            e.id,
            e.epic_key,
            e.name,
            e.description,
            e.status,
            e.priority,
            e.duration_days,
            e.progress,
            COUNT(t.id) AS total_tasks,
            COUNT(CASE WHEN t.status = 'completed' THEN 1 END) AS completed_tasks,
            COUNT(CASE WHEN t.status = 'active' THEN 1 END) AS active_tasks,
            COALESCE(SUM(t.estimate_minutes), 0) AS total_estimated_minutes,
            ROUND(
                CASE
                    WHEN COUNT(t.id) > 0
                    THEN CAST(COUNT(CASE WHEN t.status = 'completed' THEN 1 END) AS REAL)
                         / COUNT(t.id) * 100
                    ELSE 0
                END
            , 1) AS completion_percentage
        FROM framework_epics AS e
        LEFT JOIN framework_tasks AS t ON e.id = t.epic_id
        WHERE e.id = ?
        GROUP BY
            e.id, e.epic_key, e.name, e.description, e.status,
            e.priority, e.duration_days, e.progress
    """
    results = execute_cached_query(sql, params=(epic_id,), cache_ttl=cache_ttl)
    return results[0] if results else None


def get_user_stats_optimized(user_id: int = 1, cache_ttl: int = 240) -> Dict[str, Any]:
    """
    Estatísticas agregadas do usuário (com cache).

    Tabelas/colunas usadas (schema atual):
      - epics: id
      - tasks: id, epic_id, status
      - work_sessions: id, task_id, duration_minutes, focus_score
      - user_achievements: id, user_id
    """
    sql = """
        SELECT
            COUNT(DISTINCT e.id) AS total_epics,
            COUNT(DISTINCT t.id) AS total_tasks,
            COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) AS completed_tasks,
            COUNT(DISTINCT ws.id) AS total_sessions,
            COALESCE(SUM(ws.duration_minutes), 0) AS total_minutes,
            COALESCE(AVG(ws.focus_score), 0) AS avg_focus_score,
            COUNT(DISTINCT ua.id) AS total_achievements
        FROM framework_epics AS e
        LEFT JOIN framework_tasks AS t ON e.id = t.epic_id
        LEFT JOIN work_sessions AS ws ON t.id = ws.task_id
        LEFT JOIN user_achievements AS ua ON ua.user_id = ?
    """
    results = execute_cached_query(sql, params=(user_id,), cache_ttl=cache_ttl)
    return results[0] if results else {}


def get_recent_timer_sessions_optimized(days: int = 7, cache_ttl: int = 60) -> List[Dict[str, Any]]:
    """
    Lista sessões de timer recentes (últimos N dias) com JOIN em task/epic.

    Observações:
      - Usa `datetime('now', ?)` com parâmetro '-{days} days' para evitar concatenação em SQL.
      - Limita a 100 resultados mais recentes.
    """
    sql = """
        SELECT
            ws.id,
            ws.task_id,
            ws.start_time,
            ws.end_time,
            ws.duration_minutes,
            ws.session_type,
            ws.focus_score,
            t.title AS task_title,
            t.task_key,
            e.name  AS epic_name,
            e.epic_key
        FROM work_sessions AS ws
        JOIN framework_tasks AS t ON ws.task_id = t.id
        JOIN framework_epics AS e ON t.epic_id = e.id
        WHERE ws.start_time >= datetime('now', ?)
        ORDER BY ws.start_time DESC
        LIMIT 100
    """
    param = (f"-{int(days)} days",)
    return execute_cached_query(sql, params=param, cache_ttl=cache_ttl)