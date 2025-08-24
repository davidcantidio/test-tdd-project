"""
🏗️ Service Container

Dependency Injection (DI) container para gerenciar instâncias de serviços.
Suporta API legada (DatabaseManager) e nova API modular via adapter.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, Type, TypeVar, Iterable
import logging
import threading
from contextlib import contextmanager
from datetime import datetime

from .base import BaseService
from .project_service import ProjectService
from .epic_service import EpicService
from .task_service import TaskService
from .analytics_service import AnalyticsService
from .timer_service import TimerService

# Legado
from ..utils.database import DatabaseManager  # type: ignore

# Modular
from ..database import connection as db_connection, queries as db_queries

T = TypeVar("T", bound=BaseService)
logger = logging.getLogger(__name__)


# =============================================================================
# Adapter para API Modular
# =============================================================================
class ModularDatabaseAdapter:
    """
    Fornece uma interface semelhante ao DatabaseManager, usando a API modular.
    Evita heurísticas frágeis de formatos de retorno: queries retornam list[dict]/dict.
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(f"{__name__}.ModularDatabaseAdapter")
        self._logger.debug("ModularDatabaseAdapter initialized")

    # --- Conexão & Execução ---------------------------------------------------
    def get_connection(self):
        """Obtém conexão via API modular (quando exposta pelo projeto)."""
        return db_connection.get_connection()

    def get_connection_context(self):
        """Context manager de conexão direta SQLite da API modular."""
        return db_connection.get_connection_context()

    def transaction(self):
        """Context manager de transação da API modular."""
        return db_connection.transaction()

    def execute_query(self, sql: str, params: Optional[Iterable[Any]] = None) -> Any:
        """Executa SQL bruto via API modular."""
        return db_connection.execute(sql, params or ())

    # --- Operações de domínio (delegadas para queries) ------------------------
    def get_epics(self) -> list[dict]:
        try:
            res = db_queries.list_epics()
            return list(res)  # já é list[dict]
        except Exception as e:
            self._logger.error("get_epics failed: %s", e, exc_info=True)
            return []

    def get_all_epics(self) -> list[dict]:
        try:
            res = db_queries.list_all_epics()
            return list(res)
        except Exception as e:
            self._logger.error("get_all_epics failed: %s", e, exc_info=True)
            return []

    def get_tasks(self, epic_id: int) -> list[dict]:
        try:
            res = db_queries.list_tasks(epic_id)
            return list(res)
        except Exception as e:
            self._logger.error("get_tasks(%s) failed: %s", epic_id, e, exc_info=True)
            return []

    def get_all_tasks(self) -> list[dict]:
        try:
            res = db_queries.list_all_tasks()
            return list(res)
        except Exception as e:
            self._logger.error("get_all_tasks failed: %s", e, exc_info=True)
            return []

    def get_timer_sessions(self, **kwargs: Any) -> list[dict]:
        try:
            return db_queries.list_timer_sessions()
        except Exception as e:
            self._logger.error("get_timer_sessions failed: %s", e, exc_info=True)
            return []

    def get_user_stats(self, user_id: int = 1, **kwargs: Any) -> dict:
        try:
            return db_queries.get_user_stats(user_id)
        except Exception as e:
            self._logger.error("get_user_stats(%s) failed: %s", user_id, e, exc_info=True)
            return {}

    def get_achievements(self, user_id: int = 1, **kwargs: Any) -> list[dict]:
        try:
            return db_queries.get_achievements(user_id)
        except Exception as e:
            self._logger.error("get_achievements(%s) failed: %s", user_id, e, exc_info=True)
            return []

    def check_database_health(self) -> dict:
        from ..database.health import check_health  # type: ignore
        try:
            return check_health()
        except Exception as e:
            self._logger.error("check_database_health failed: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}

    def __getattr__(self, name: str):
        self._logger.warning("ModularDatabaseAdapter: método '%s' não implementado", name)
        raise AttributeError(f"ModularDatabaseAdapter has no method '{name}'")


# =============================================================================
# Tipos de erro
# =============================================================================
class ServiceError(Exception):
    """Erro de operações do container de serviços."""


# =============================================================================
# Service Container
# =============================================================================
class ServiceContainer:
    """
    Container de DI com singletons por serviço, suportando inicialização preguiçosa.
    Suporta API legada (DatabaseManager) ou a API modular (via adapter).
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None, use_modular_api: bool = False) -> None:
        """
        Args:
            db_manager: Instância do DatabaseManager (obrigatória se use_modular_api=False)
            use_modular_api: True para usar a API modular
        """
        self.db_manager = db_manager
        self.use_modular_api = use_modular_api
        self._logger = logging.getLogger(f"{__name__}.ServiceContainer")

        if not use_modular_api and db_manager is None:
            raise ValueError("db_manager é obrigatório quando use_modular_api=False")

        self._logger.info(
            "ServiceContainer initialized with %s",
            "modular API" if use_modular_api else "legacy DatabaseManager",
        )

        self._services: Dict[str, BaseService] = {}
        self._service_classes: Dict[str, Type[BaseService]] = {
            "project": ProjectService,
            "epic": EpicService,
            "task": TaskService,
            "analytics": AnalyticsService,
            "timer": TimerService,
        }

        self._lazy_loading = True
        self._initialized = False
        self._lock = threading.Lock()

    # --- ciclo de vida --------------------------------------------------------
    def initialize(self, lazy_loading: bool = True) -> None:
        self._lazy_loading = lazy_loading

        if not lazy_loading:
            for name in list(self._service_classes.keys()):
                self._create_service(name)

        self._initialized = True
        self._logger.info("Service container initialized (lazy_loading=%s)", lazy_loading)

    def shutdown(self) -> None:
        """Desaloca instâncias e marca container como não inicializado."""
        self.clear_all_services()
        self._initialized = False
        self._logger.info("Service container shutdown")

    # --- transações -----------------------------------------------------------
    @contextmanager
    def transaction_scope(self):
        """
        Escopo transacional real: usa a transação da API modular ou do DatabaseManager.
        Todos os serviços usados dentro do bloco compartilham o mesmo contexto.
        """
        if self.use_modular_api:
            cm = db_connection.transaction()
        else:
            assert self.db_manager is not None
            cm = self.db_manager.transaction()

        try:
            with cm:
                yield self
        except Exception:
            # rollback é responsabilidade do context manager subjacente
            self._logger.exception("Transaction scope error")
            raise

    # --- registro e acesso a serviços ----------------------------------------
    def register_service(self, service_name: str, service_class: Type[BaseService]) -> None:
        self._service_classes[service_name] = service_class
        if not self._lazy_loading and self._initialized:
            self._create_service(service_name)
        self._logger.info("Registered service: %s -> %s", service_name, service_class.__name__)

    def has_service(self, service_name: str) -> bool:
        return service_name in self._service_classes

    def list_services(self) -> Dict[str, str]:
        return {name: cls.__name__ for name, cls in self._service_classes.items()}

    def is_service_created(self, service_name: str) -> bool:
        return service_name in self._services

    def clear_service(self, service_name: str) -> None:
        if service_name in self._services:
            del self._services[service_name]
            self._logger.info("Cleared service instance: %s", service_name)

    def clear_all_services(self) -> None:
        names = list(self._services.keys())
        self._services.clear()
        self._logger.info("Cleared all service instances: %s", names)

    def get_service_status(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "lazy_loading": self._lazy_loading,
            "registered_services": list(self._service_classes.keys()),
            "created_services": list(self._services.keys()),
            "service_count": len(self._service_classes),
            "created_count": len(self._services),
        }

    def validate_services(self) -> Dict[str, bool]:
        """
        Verifica se todos os serviços podem ser instanciados.
        Não persiste as instâncias quando validate_only=True.
        """
        results: Dict[str, bool] = {}
        for name in self._service_classes.keys():
            try:
                self._create_service(name, validate_only=True)
                results[name] = True
                self._logger.debug("Service validation passed: %s", name)
            except Exception as e:
                results[name] = False
                self._logger.error("Service validation failed: %s - %s", name, e)
        return results

    # --- getters específicos --------------------------------------------------
    def get_project_service(self) -> ProjectService:
        return self._get_service("project", ProjectService)

    def get_epic_service(self) -> EpicService:
        return self._get_service("epic", EpicService)

    def get_task_service(self) -> TaskService:
        return self._get_service("task", TaskService)

    def get_analytics_service(self) -> AnalyticsService:
        return self._get_service("analytics", AnalyticsService)

    def get_timer_service(self) -> TimerService:
        return self._get_service("timer", TimerService)

    # --- núcleo de criação/recuperação ---------------------------------------
    def _get_service(self, service_name: str, service_class: Type[T]) -> T:
        with self._lock:
            if service_name not in self._services:
                if not self._initialized:
                    raise ServiceError("Service container not initialized. Call initialize() first.")
                self._services[service_name] = self._create_service(service_name)

            service = self._services[service_name]
            if not isinstance(service, service_class):
                raise ServiceError(
                    f"Service type mismatch: expected {service_class.__name__}, got {type(service).__name__}"
                )
            return service  # type: ignore[return-value]

    def _create_service(self, service_name: str, validate_only: bool = False) -> BaseService:
        if service_name not in self._service_classes:
            raise ServiceError(f"Unknown service: {service_name}")

        cls = self._service_classes[service_name]
        try:
            if self.use_modular_api:
                db_adapter = ModularDatabaseAdapter()
                service = cls(db_adapter)
                if not validate_only:
                    logger.debug("Created service: %s -> %s (modular API)", service_name, cls.__name__)
            else:
                assert self.db_manager is not None
                service = cls(self.db_manager)
                if not validate_only:
                    logger.debug("Created service: %s -> %s (legacy API)", service_name, cls.__name__)
            return service
        except Exception as e:
            raise ServiceError(f"Failed to create service {service_name}: {e}") from e


# =============================================================================
# Container global
# =============================================================================
_service_container: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    global _service_container
    if _service_container is None:
        raise ServiceError("Service container not initialized. Call initialize_service_container() first.")
    return _service_container


def initialize_service_container(db_manager: DatabaseManager, lazy_loading: bool = True) -> ServiceContainer:
    global _service_container
    if _service_container is not None:
        _service_container.shutdown()
    _service_container = ServiceContainer(db_manager=db_manager, use_modular_api=False)
    _service_container.initialize(lazy_loading)
    return _service_container


def initialize_service_container_modular(lazy_loading: bool = True) -> ServiceContainer:
    global _service_container
    if _service_container is not None:
        _service_container.shutdown()
    _service_container = ServiceContainer(use_modular_api=True)
    _service_container.initialize(lazy_loading)
    return _service_container


def shutdown_service_container() -> None:
    global _service_container
    if _service_container is not None:
        _service_container.shutdown()
        _service_container = None


# =============================================================================
# Conveniências para acesso direto
# =============================================================================
def get_project_service() -> ProjectService:
    return get_service_container().get_project_service()


def get_epic_service() -> EpicService:
    return get_service_container().get_epic_service()


def get_task_service() -> TaskService:
    return get_service_container().get_task_service()


def get_analytics_service() -> AnalyticsService:
    return get_service_container().get_analytics_service()


def get_timer_service() -> TimerService:
    return get_service_container().get_timer_service()


# =============================================================================
# Context manager transacional para operações de serviço
# =============================================================================
@contextmanager
def service_transaction():
    container = get_service_container()
    with container.transaction_scope():
        yield container


# =============================================================================
# Health Check dos serviços
# =============================================================================
def check_service_health() -> Dict[str, Any]:
    try:
        container = get_service_container()
        validation = container.validate_services()
        status = container.get_service_status()
        all_ok = all(validation.values())
        return {
            "overall_health": "healthy" if all_ok else "unhealthy",
            "container_status": status,
            "service_validation": validation,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        return {
            "overall_health": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


# =============================================================================
# Exemplo de uso (manual)
# =============================================================================
def example_service_usage() -> None:
    """Exemplo simples de inicialização e uso do container (modo legado)."""
    dm = DatabaseManager()  # type: ignore[call-arg]
    container = initialize_service_container(dm, lazy_loading=True)

    try:
        project_service = get_project_service()
        epic_service = get_epic_service()
        task_service = get_task_service()
        analytics_service = get_analytics_service()
        timer_service = get_timer_service()

        # Exemplos ilustrativos (ajuste conforme as assinaturas reais dos serviços)
        _ = project_service
        _ = epic_service
        _ = task_service
        _ = analytics_service
        _ = timer_service

        # Escopo transacional real
        with service_transaction():
            # operações relacionadas...
            pass
    finally:
        shutdown_service_container()


if __name__ == "__main__":
    example_service_usage()