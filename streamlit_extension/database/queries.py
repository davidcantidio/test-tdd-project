from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from .connection import execute_cached_query, get_optimized_connection, get_connection_context

# -----------------------------------------------------------------------------
# Compat helpers: epic_key pode não existir após a migração 012.
# Construímos fragmentos SQL dinamicamente para manter a API estável.
# -----------------------------------------------------------------------------
_EPIC_KEY_PRESENT: Optional[bool] = None


def _has_epic_key_column() -> bool:
    global _EPIC_KEY_PRESENT
    if _EPIC_KEY_PRESENT is not None:
        return _EPIC_KEY_PRESENT
    try:
        with get_connection_context() as conn:
            rows = conn.execute("PRAGMA table_info('framework_epics')").fetchall()
            names = [r[1] if isinstance(r, tuple) else r["name"] for r in rows]
            _EPIC_KEY_PRESENT = "epic_key" in set(names)
    except Exception:
        # Padrão seguro enquanto o schema está em transição
        _EPIC_KEY_PRESENT = True
    return _EPIC_KEY_PRESENT


def _epic_key_expr(alias: Optional[str] = None) -> str:
    has = _has_epic_key_column()
    if alias:
        return f"{alias}.epic_key" if has else f"'EPIC-' || {alias}.id AS epic_key"
    return "epic_key" if has else "'EPIC-' || id AS epic_key"

# Removed legacy DatabaseManager dependencies


# Auth imports removed - using official Streamlit OAuth


# =============================================================================
# Adaptação compatível com a API legada (delegação ao DatabaseManager)
# =============================================================================

def list_epics() -> List[Dict[str, Any]]:
    """Lista epics usando consulta direta otimizada."""
    return list_epics_optimized()


def list_all_epics() -> List[Dict[str, Any]]:
    """Lista todos os epics (incluindo arquivados/deletados)."""
    ek = _epic_key_expr()
    sql = f"""
        SELECT
            id, {ek}, name, description, status, priority,
            duration_days, created_at, updated_at
        FROM framework_epics
        ORDER BY created_at DESC
    """
    return execute_cached_query(sql, cache_ttl=300)


def list_tasks(epic_id: int) -> List[Dict[str, Any]]:
    """Lista tasks de um epic específico usando consulta direta."""
    return list_tasks_optimized(epic_id)


def list_all_tasks() -> List[Dict[str, Any]]:
    """Lista todas as tasks com dados do epic (otimizada)."""
    ek = _epic_key_expr("e")
    sql = f"""
        SELECT
            t.id, t.task_key, t.epic_id, t.title, t.description,
            t.tdd_phase, t.status, t.estimate_minutes,
            t.created_at, t.updated_at,
            e.name AS epic_name, {ek}
        FROM framework_tasks AS t
        JOIN framework_epics AS e ON t.epic_id = e.id
        ORDER BY t.created_at DESC, t.id DESC
    """
    return execute_cached_query(sql, cache_ttl=240)


def list_timer_sessions() -> List[Dict[str, Any]]:
    """Retorna sessões de timer com dados de task/epic."""
    return get_recent_timer_sessions_optimized(days=30)


def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Métricas agregadas por usuário usando consulta otimizada."""
    return get_user_stats_optimized(user_id)


def get_achievements(user_id: int) -> List[Dict[str, Any]]:
    """Conquistas/gamificação do usuário usando consulta direta."""
    sql = """
        SELECT
            ua.id, ua.user_id, ua.achievement_type_id, ua.earned_at,
            at.name AS achievement_name, at.description AS achievement_description,
            at.icon AS achievement_icon, at.points AS achievement_points
        FROM user_achievements AS ua
        JOIN achievement_types AS at ON ua.achievement_type_id = at.id
        WHERE ua.user_id = ?
        ORDER BY ua.earned_at DESC
    """
    return execute_cached_query(sql, params=(user_id,), cache_ttl=180)


# =============================================================================
# PROJECT QUERIES (for projects.py migration)
# =============================================================================

def list_all_projects() -> List[Dict[str, Any]]:
    """Lista todos os projetos (incluindo inativos) - compatível com get_projects(include_inactive=True)."""
    sql = """
        SELECT
            id, project_key, name, description, status,
            created_at, updated_at
        FROM framework_projects
        ORDER BY created_at DESC
    """
    return execute_cached_query(sql, cache_ttl=300)


def list_active_projects() -> List[Dict[str, Any]]:
    """Lista apenas projetos ativos.""" 
    sql = """
        SELECT
            id, project_key, name, description, status,
            created_at, updated_at
        FROM framework_projects
        WHERE status = 'active'
        ORDER BY created_at DESC
    """
    return execute_cached_query(sql, cache_ttl=300)


# =============================================================================
# ⚡ PERFORMANCE-OPTIMIZED QUERIES (alinhadas ao schema atual)
# =============================================================================

def list_epics_optimized(cache_ttl: int = 300) -> List[Dict[str, Any]]:
    """
    Lista epics com SELECT enxuto + cache.

    Columns retornadas:
      - id, epic_key (ou EPIC-{id}), name, description, status, priority,
        duration_days, created_at, updated_at
    """
    ek = _epic_key_expr()
    sql = f"""
        SELECT
            id,
            {ek},
            name,
            description,
            status,
            priority,
            duration_days,
            created_at,
            updated_at
        FROM framework_epics
        ORDER BY priority ASC, created_at DESC
    """
    return execute_cached_query(sql, cache_ttl=cache_ttl)


def list_tasks_optimized(epic_id: int, cache_ttl: int = 120) -> List[Dict[str, Any]]:
    """
    Lista tasks de um epic com JOIN para trazer dados do epic.

    Columns retornadas:
      - tasks: id, task_key, epic_id, title, description, tdd_phase, status,
               estimate_minutes, created_at, updated_at
      - epics: id, name, epic_key (ou EPIC-{id})
    """
    ek = _epic_key_expr("e")
    sql = f"""
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
            {ek}
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
    ek_raw = _epic_key_expr("e")
    sql = f"""
        SELECT
            e.id,
            {ek_raw},
            e.name,
            e.description,
            e.status,
            e.priority,
            e.duration_days,
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
        GROUP BY e.id, e.name, e.description, e.status, e.priority, e.duration_days
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
    ek = _epic_key_expr("e")
    sql = f"""
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
            {ek}
        FROM work_sessions AS ws
        JOIN framework_tasks AS t ON ws.task_id = t.id
        JOIN framework_epics AS e ON t.epic_id = e.id
        WHERE ws.start_time >= datetime('now', ?)
        ORDER BY ws.start_time DESC
        LIMIT 100
    """
    param = (f"-{int(days)} days",)
    return execute_cached_query(sql, params=param, cache_ttl=cache_ttl)
