from __future__ import annotations

from typing import Any, Dict, List

from streamlit_extension.utils.database import DatabaseManager  # type: ignore

_DBM_INSTANCE: DatabaseManager | None = None  # type: ignore


def _db() -> DatabaseManager:
    global _DBM_INSTANCE  # type: ignore
    try:
        return _DBM_INSTANCE  # type: ignore
    except NameError:
        _DBM_INSTANCE = DatabaseManager()  # type: ignore
        return _DBM_INSTANCE


def list_epics() -> List[Dict[str, Any]]:
    """Lista epics ativos conforme regra do ``DatabaseManager``."""

    return _db().get_epics()


def list_all_epics() -> List[Dict[str, Any]]:
    """Lista epics, incluindo arquivados/deletados (se suportado)."""

    return _db().get_all_epics()


def list_tasks(epic_id: int) -> List[Dict[str, Any]]:
    """Lista tasks de um epic específico."""

    return _db().get_tasks(epic_id)


def list_all_tasks() -> List[Dict[str, Any]]:
    """Lista todas as tasks; pode ser custoso."""

    return _db().get_all_tasks()


def list_timer_sessions() -> List[Dict[str, Any]]:
    """Retorna sessões de timer agregadas pelo manager."""

    return _db().get_timer_sessions()


def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Métricas agregadas por usuário."""

    return _db().get_user_stats(user_id)


def get_achievements(user_id: int) -> List[Dict[str, Any]]:
    """Conquistas/gamificação do usuário."""

    return _db().get_achievements(user_id)

