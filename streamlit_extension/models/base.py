#!/usr/bin/env python3
"""
🏗️ MODELS - SQLAlchemy Base Infrastructure

SQLAlchemy declarative base e gerenciamento de sessões integrados aos padrões
existentes do projeto. Fornece a fundação para modelos ORM mantendo
compatibilidade com o DatabaseManager atual.

Uso:
    from streamlit_extension.models.base import Base, get_session, SessionManager

Recursos:
- Base declarativa com configuração otimizada para TDD/TDAH
- Gerenciamento de sessão integrado aos padrões de conexão existentes
- Sessões thread-safe
- Limpeza automática e conexão com pool
"""

from __future__ import annotations

import logging
import re
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional, Type, TypeVar, List

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

# -----------------------------------------------------------------------------#
# Typing
# -----------------------------------------------------------------------------#
ModelType = TypeVar("ModelType", bound="Base")
logger = logging.getLogger(__name__)


# =============================================================================
# Helper/Mixins
# =============================================================================

def _camel_to_snake(name: str) -> str:
    """Converte CamelCase para snake_case (para nomes de tabela automáticos)."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class QueryMixin:
    """Mixin com utilitários de consulta e CRUD comum."""

    @classmethod
    def get_by_id(cls: Type[ModelType], session: Session, id: int) -> Optional[ModelType]:
        return session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_all(cls: Type[ModelType], session: Session) -> List[ModelType]:
        return session.query(cls).all()

    @classmethod
    def create(cls: Type[ModelType], session: Session, **kwargs) -> ModelType:
        instance = cls(**kwargs)
        session.add(instance)
        session.flush()  # obtém ID sem commit
        return instance

    def save(self, session: Session) -> None:
        session.add(self)
        session.flush()

    def delete(self, session: Session) -> None:
        session.delete(self)
        session.flush()


# =============================================================================
# SQLAlchemy Declarative Base
# =============================================================================

class Base(DeclarativeBase, QueryMixin):
    """
    Base declarativa com utilitários TDD/TDAH.

    - Representação amigável (__repr__)
    - Serialização para dict
    - Atualização a partir de dict
    - Nome de tabela automático (snake_case) quando __tablename__ não for definido
    """

    # Nome de tabela automático caso a classe filha não defina __tablename__
    def __init_subclass__(cls, **kwargs):  # type: ignore[override]
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "__tablename__"):
            cls.__tablename__ = _camel_to_snake(cls.__name__)

    def __repr__(self) -> str:  # pragma: no cover - utilitário simples
        pk_value = getattr(self, "id", "new")
        return f"<{self.__class__.__name__}(id={pk_value})>"

    def to_dict(self) -> Dict[str, Any]:
        """Converte a instância em dict serializável em JSON."""
        result: Dict[str, Any] = {}
        for column in self.__table__.columns:  # type: ignore[attr-defined]
            value = getattr(self, column.name)
            if hasattr(value, "isoformat"):
                value = value.isoformat()  # datas/horários
            result[column.name] = value
        return result

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Atualiza atributos a partir de um dict."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def get_table_name(cls) -> str:
        """Retorna o nome da tabela da classe."""
        return cls.__tablename__  # type: ignore[attr-defined]

    def refresh_from_db(self, session: Session) -> None:
        """Recarrega dados do banco (útil para recuperação pós-interrupção)."""
        session.refresh(self)

    # Pontos de extensão para TDD/TDAH
    def validate_tdd_workflow(self) -> bool:  # pragma: no cover - hook
        return True

    def calculate_tdah_complexity(self) -> int:  # pragma: no cover - hook
        return 1


# =============================================================================
# Session Management
# =============================================================================

class SessionManager:
    """
    Gerenciador de sessões thread-safe.

    - Integração com padrões existentes de conexão (DatabaseManager)
    - Conexão SQLite com WAL e pool de conexões
    - Escopo transacional com commit/rollback automáticos
    """

    def __init__(self, database_url: Optional[str] = None):
        # padrão: banco local do framework
        self._database_url = database_url or "sqlite:///framework.db"
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None
        self._lock = threading.Lock()
        self._initialized = False

    def _initialize(self) -> None:
        """Inicializa lazy os componentes SQLAlchemy."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            # Engine
            # Observação:
            # - Em SQLAlchemy 2.0, 'future=True' é padrão → não usamos.
            # - Evitamos StaticPool em arquivo SQLite para permitir pooling real.
            self._engine = create_engine(
                self._database_url,
                pool_pre_ping=True,
                connect_args={
                    "check_same_thread": False,  # multi-thread
                    "timeout": 30,               # paciência p/ TDAH
                },
                echo=False,
            )

            # PRAGMAs SQLite para concorrência e integridade
            @event.listens_for(self._engine, "connect")
            def _set_sqlite_pragmas(dbapi_connection, connection_record):  # noqa: N802
                try:
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA busy_timeout=5000")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.close()
                except Exception as e:  # pragma: no cover - proteção extra
                    logger.warning(f"Falha ao aplicar PRAGMAs SQLite: {e}")

            # Session factory (SQLAlchemy 2.x: sem autocommit)
            self._session_factory = sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                autoflush=True,
            )

            # Sessão com escopo por thread
            self._scoped_session = scoped_session(self._session_factory)

            self._initialized = True

    @property
    def engine(self) -> Engine:
        self._initialize()
        assert self._engine is not None  # para type-checkers
        return self._engine

    def get_session(self) -> Session:
        """Obtém uma sessão local à thread."""
        self._initialize()
        assert self._scoped_session is not None
        return self._scoped_session()

    def remove_session(self) -> None:
        """Remove a sessão atual (scoped)."""
        if self._scoped_session:
            self._scoped_session.remove()

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """
        Escopo transacional simples (commit/rollback automáticos).
        """
        session = self.get_session()
        try:
            with session.begin():
                yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    @contextmanager
    def tdd_cycle_transaction(self) -> Iterator[Session]:
        """
        Escopo especial para ciclos TDD com savepoint para recuperação.
        """
        session = self.get_session()
        try:
            with session.begin():
                with session.begin_nested():  # savepoint
                    yield session
        except Exception as e:
            logger.error(f"TDD cycle transaction failed: {e}")
            raise
        finally:
            session.close()

    # Utilidades de schema
    def create_all_tables(self) -> None:
        self._initialize()
        Base.metadata.create_all(self._engine)  # type: ignore[arg-type]
        logger.info("Tabelas criadas com sucesso.")

    def drop_all_tables(self) -> None:
        self._initialize()
        Base.metadata.drop_all(self._engine)  # type: ignore[arg-type]
        logger.warning("Todas as tabelas foram removidas.")


# =============================================================================
# Global Session Manager Instance
# =============================================================================

_session_manager: Optional[SessionManager] = None
_session_lock = threading.Lock()


def get_session_manager(database_url: Optional[str] = None) -> SessionManager:
    """Obtém instância global do SessionManager (singleton thread-safe)."""
    global _session_manager
    if _session_manager is None:
        with _session_lock:
            if _session_manager is None:
                _session_manager = SessionManager(database_url)
    return _session_manager


def get_session() -> Session:
    """Atalho para uma sessão do banco."""
    return get_session_manager().get_session()


def get_engine() -> Engine:
    """Atalho para o engine do banco."""
    return get_session_manager().engine


@contextmanager
def session_scope(database_url: Optional[str] = None) -> Iterator[Session]:
    """
    Context manager transacional (atalho).

    Exemplo:
        with session_scope() as session:
            epic = session.query(Epic).filter_by(id=epic_id).first()
            epic.status = 'completed'
    """
    manager = get_session_manager(database_url)
    with manager.session_scope() as session:
        yield session


@contextmanager
def tdd_transaction(database_url: Optional[str] = None) -> Iterator[Session]:
    """
    Context manager com savepoint para ciclos TDD.

    Exemplo:
        with tdd_transaction() as session:
            task = session.query(Task).filter_by(id=task_id).first()
            task.transition_tdd_phase('Green')
    """
    manager = get_session_manager(database_url)
    with manager.tdd_cycle_transaction() as session:
        yield session


# =============================================================================
# Utility Functions
# =============================================================================

def init_database(database_url: Optional[str] = None) -> None:
    """Inicializa o banco criando todas as tabelas."""
    manager = get_session_manager(database_url)
    manager.create_all_tables()


def reset_database(database_url: Optional[str] = None) -> None:
    """Reseta o banco (drop + create). CUIDADO: destrutivo."""
    manager = get_session_manager(database_url)
    manager.drop_all_tables()
    manager.create_all_tables()


# =============================================================================
# Integration Helpers
# =============================================================================

def integrate_with_existing_db_manager() -> None:
    """
    Integra a URL do SQLAlchemy com o DatabaseManager existente, quando presente.
    """
    try:
        # Import tardio para evitar dependência forte
        from streamlit_extension.utils.database import DatabaseManager  # type: ignore

        db_manager = DatabaseManager()
        if hasattr(db_manager, "db_path"):
            database_url = f"sqlite:///{db_manager.db_path}"
            get_session_manager(database_url)

        logger.info("Integração com DatabaseManager concluída com sucesso.")
    except ImportError:
        logger.warning("DatabaseManager não disponível para integração.")
    except Exception as e:
        logger.warning(f"Falha na integração com DatabaseManager: {e}")
