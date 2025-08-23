#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏗️ MODELS - SQLAlchemy Base Infrastructure (consolidated)

Fundação ORM com Base declarativa e gerenciamento de sessões integrado ao
módulo central de configuração de banco (models.database). Evita PRAGMAs
duplicados, garante pooling/URL corretos e mantém compatibilidade.

Uso:
    from streamlit_extension.models.base import Base, get_session, SessionManager
"""

from __future__ import annotations

import logging
import re
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional, Type, TypeVar, List

from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

# >>> Integra com a camada central de DB (pool/PRAGMAs/URL corretos)
from .database import create_db_engine, get_database_url

# -----------------------------------------------------------------------------#
# Typing / logger
# -----------------------------------------------------------------------------#
ModelType = TypeVar("ModelType", bound="Base")
logger = logging.getLogger(__name__)


# =============================================================================
# Helpers / Mixins
# =============================================================================

def _camel_to_snake(name: str) -> str:
    """Converte CamelCase para snake_case (para nomes de tabela automáticos)."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class QueryMixin:
    """Mixin com utilitários de consulta/CRUD comuns."""
    @classmethod
    def get_by_id(cls: Type[ModelType], session: Session, id: int) -> Optional[ModelType]:
        return session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_all(cls: Type[ModelType], session: Session) -> List[ModelType]:
        return session.query(cls).all()

    @classmethod
    def create(cls: Type[ModelType], session: Session, **kwargs: Any) -> ModelType:
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

    - __repr__ amigável
    - to_dict / update_from_dict
    - __tablename__ automático (snake_case) se não definido
    """
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
                value = value.isoformat()
            result[column.name] = value
        return result

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Atualiza atributos a partir de um dict (ignora chaves inexistentes)."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def get_table_name(cls) -> str:
        return cls.__tablename__  # type: ignore[attr-defined]

    def refresh_from_db(self, session: Session) -> None:
        session.refresh(self)

    # Hooks TDD/TDAH (extensíveis pelos modelos)
    def validate_tdd_workflow(self) -> bool:  # pragma: no cover - hook
        return True

    def calculate_tdah_complexity(self) -> int:  # pragma: no cover - hook
        return 1


# =============================================================================
# Session Management (singleton thread-safe)
# =============================================================================

class SessionManager:
    """
    Gerenciador de sessões thread-safe.

    - Usa engine central (create_db_engine/get_database_url)
    - Sessões com escopo por thread (scoped_session)
    - expire_on_commit=False para melhor DX em Streamlit
    - Context managers com commit/rollback automáticos
    """

    def __init__(self, database_url: Optional[str] = None):
        # Se não informado, resolve via módulo central (framework.db / env / DatabaseManager)
        self._database_url = database_url or get_database_url(None)
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None
        self._lock = threading.Lock()
        self._initialized = False

    def _initialize(self) -> None:
        """Inicializa lazy os componentes SQLAlchemy (idempotente)."""
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return

            # Usa a engine unificada (PRAGMAs/pooling corretos por dialeto)
            self._engine = create_db_engine(self._database_url)

            # Factory (SQLAlchemy 2.x: sem autocommit)
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
        assert self._engine is not None
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

def create_tables(database_url: Optional[str] = None) -> None:
    """Alias para init_database() (compat)."""
    init_database(database_url)

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
    Usa o resolvedor central para obter a URL correta (sqlite+pysqlite).
    """
    try:
        # Import tardio para evitar dependência forte
        from streamlit_extension.utils.database import DatabaseManager  # type: ignore

        db_manager = DatabaseManager()
        # Se o DatabaseManager expõe .db_path, resolvemos via camada central para não errar o driver.
        if hasattr(db_manager, "db_path") and db_manager.db_path:
            database_url = get_database_url(str(db_manager.db_path))
            get_session_manager(database_url)  # reconfigura singleton com URL correta

        logger.info("Integração com DatabaseManager concluída com sucesso.")
    except ImportError:
        logger.info("DatabaseManager não disponível para integração.")
    except Exception as e:
        logger.warning(f"Falha na integração com DatabaseManager: {e}")
