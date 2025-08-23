#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗄️ MODELS - Repository Pattern Base Classes

Enterprise repository pattern com CRUD genérico, gerenciamento transacional
e integração com o service layer existente.

- BaseRepository[T] tipado com Result pattern
- Suporte a sessão externa (DI) e transações internas
- Soft delete opcional (se o modelo tiver `deleted_at`)
- RepositoryFactory/Manager para DI e Unit of Work
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Callable
from datetime import datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .base import Base, get_session, transaction

# Type variables for generic repository
T = TypeVar("T", bound=Base)

logger = logging.getLogger(__name__)


# =============================================================================
# Repository Result Pattern
# =============================================================================

class RepositoryResult(Generic[T]):
    """
    Wrapper para operações de repositório (compatível com ServiceResult).
    Evita propagar exceções para a camada de serviço.
    """

    def __init__(self, success: bool, data: Optional[T] = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error
        self.errors = [error] if error else []

    @classmethod
    def ok(cls, data: T) -> "RepositoryResult[T]":
        return cls(success=True, data=data)

    @classmethod
    def error(cls, error: str) -> "RepositoryResult[T]":
        return cls(success=False, error=error)

    @classmethod
    def not_found(cls, entity: str = "Entity") -> "RepositoryResult[T]":
        return cls(success=False, error=f"{entity} not found")


class RepositoryListResult(Generic[T]):
    """Wrapper para operações que retornam listas."""

    def __init__(
        self,
        success: bool,
        data: Optional[List[T]] = None,
        error: Optional[str] = None,
        count: int = 0,
    ):
        self.success = success
        self.data = data or []
        self.error = error
        self.errors = [error] if error else []
        self.count = count

    @classmethod
    def ok(cls, data: List[T], count: Optional[int] = None) -> "RepositoryListResult[T]":
        return cls(success=True, data=data, count=count or len(data))

    @classmethod
    def error(cls, error: str) -> "RepositoryListResult[T]":
        return cls(success=False, error=error)

    @classmethod
    def empty(cls) -> "RepositoryListResult[T]":
        return cls(success=True, data=[], count=0)


# =============================================================================
# Interface
# =============================================================================

class IRepository(Generic[T], ABC):
    """Interface para DI e testes."""

    @abstractmethod
    def get_by_id(self, entity_id: int) -> RepositoryResult[T]:
        ...

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> RepositoryListResult[T]:
        ...

    @abstractmethod
    def create(self, entity: T) -> RepositoryResult[T]:
        ...

    @abstractmethod
    def update(self, entity: T) -> RepositoryResult[T]:
        ...

    @abstractmethod
    def delete(self, entity_id: int) -> RepositoryResult[bool]:
        ...


# =============================================================================
# Implementação Base
# =============================================================================

class BaseRepository(Generic[T], IRepository[T]):
    """
    Base genérica com CRUD, transações e logging.

    - Usa sessão externa se fornecida (controle transacional fora)
    - Caso contrário, usa o context manager `transaction()` do projeto
    """

    def __init__(self, model_class: Type[T], session: Optional[Session] = None):
        self.model_class = model_class
        self._session = session
        self._external_session = session is not None

    @property
    def session(self) -> Session:
        return self._session or get_session()

    # ---------- READ ----------

    def get_by_id(self, entity_id: int) -> RepositoryResult[T]:
        try:
            entity = (
                self.session.query(self.model_class)
                .filter(self.model_class.id == entity_id)
                .first()
            )
            return RepositoryResult.ok(entity) if entity else RepositoryResult.not_found(self.model_class.__name__)
        except SQLAlchemyError as e:
            logger.exception("DB error on get_by_id(%s): %s", entity_id, e)
            return RepositoryResult.error(f"Database error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error on get_by_id(%s): %s", entity_id, e)
            return RepositoryResult.error(f"Unexpected error: {str(e)}")

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        desc: bool = False,
    ) -> RepositoryListResult[T]:
        try:
            query = self.session.query(self.model_class)

            # Filtros seguros: ignorar chaves inexistentes
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field):
                        query = query.filter(getattr(self.model_class, field) == value)

            # Ordenação opcional
            if order_by and hasattr(self.model_class, order_by):
                col = getattr(self.model_class, order_by)
                query = query.order_by(col.desc() if desc else col.asc())

            total_count = query.count()
            entities = query.offset(max(0, skip)).limit(max(1, limit)).all()

            return RepositoryListResult.ok(entities, total_count)
        except SQLAlchemyError as e:
            logger.exception("DB error on get_all: %s", e)
            return RepositoryListResult.error(f"Database error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error on get_all: %s", e)
            return RepositoryListResult.error(f"Unexpected error: {str(e)}")

    def find_by(self, **kwargs) -> RepositoryListResult[T]:
        """
        Busca por campos (igualdade). Chaves inexistentes são ignoradas.
        """
        try:
            query = self.session.query(self.model_class)
            for field, value in kwargs.items():
                if hasattr(self.model_class, field):
                    query = query.filter(getattr(self.model_class, field) == value)

            return RepositoryListResult.ok(query.all())
        except SQLAlchemyError as e:
            logger.exception("DB error on find_by(%s): %s", kwargs, e)
            return RepositoryListResult.error(f"Database error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error on find_by(%s): %s", kwargs, e)
            return RepositoryListResult.error(f"Unexpected error: {str(e)}")

    def count(self, filters: Optional[Dict[str, Any]] = None) -> RepositoryResult[int]:
        try:
            query = self.session.query(self.model_class)
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field):
                        query = query.filter(getattr(self.model_class, field) == value)
            return RepositoryResult.ok(query.count())
        except SQLAlchemyError as e:
            logger.exception("DB error on count: %s", e)
            return RepositoryResult.error(f"Database error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error on count: %s", e)
            return RepositoryResult.error(f"Unexpected error: {str(e)}")

    def exists(self, entity_id: int) -> RepositoryResult[bool]:
        try:
            q = self.session.query(self.model_class.id).filter(self.model_class.id == entity_id)
            return RepositoryResult.ok(self.session.query(q.exists()).scalar())
        except SQLAlchemyError as e:
            logger.exception("DB error on exists(%s): %s", entity_id, e)
            return RepositoryResult.error(f"Database error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error on exists(%s): %s", entity_id, e)
            return RepositoryResult.error(f"Unexpected error: {str(e)}")

    # ---------- WRITE ----------

    def _touch_timestamps_on_create(self, entity: T) -> None:
        # Define created_at/updated_at se existirem no modelo
        now = datetime.utcnow()
        if hasattr(entity, "created_at") and getattr(entity, "created_at") is None:
            setattr(entity, "created_at", now)
        if hasattr(entity, "updated_at"):
            setattr(entity, "updated_at", now)

    def _touch_updated_at(self, entity: T) -> None:
        if hasattr(entity, "updated_at"):
            setattr(entity, "updated_at", datetime.utcnow())

    def create(self, entity: T) -> RepositoryResult[T]:
        try:
            self._touch_timestamps_on_create(entity)

            if self._external_session:
                self.session.add(entity)
                self.session.flush()
            else:
                with transaction():
                    self.session.add(entity)
                    self.session.flush()

            logger.info("Created %s id=%s", self.model_class.__name__, getattr(entity, "id", None))
            return RepositoryResult.ok(entity)
        except IntegrityError as e:
            logger.exception("Integrity error on create: %s", e)
            return RepositoryResult.error(f"Data integrity error: {str(e)}")
        except SQLAlchemyError as e:
            logger.exception("DB error on create: %s", e)
            return RepositoryResult.error(f"Database error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error on create: %s", e)
            return RepositoryResult.error(f"Unexpected error: {str(e)}")

    def update(self, entity: T) -> RepositoryResult[T]:
        try:
            entity_id = getattr(entity, "id", None)
            if not entity_id:
                return RepositoryResult.error("Entity must have ID for update")

            self._touch_updated_at(entity)

            if self._external_session:
                self.session.merge(entity)
                self.session.flush()
            else:
                with transaction():
                    self.session.merge(entity)
                    self.session.flush()

            logger.info("Updated %s id=%s", self.model_class.__name__, entity_id)
            return RepositoryResult.ok(entity)
        except IntegrityError as e:
            logger.exception("Integrity error on update: %s", e)
            return RepositoryResult.error(f"Data integrity error: {str(e)}")
        except SQLAlchemyError as e:
            logger.exception("DB error on update: %s", e)
            return RepositoryResult.error(f"Database error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error on update: %s", e)
            return RepositoryResult.error(f"Unexpected error: {str(e)}")

    def delete(self, entity_id: int) -> RepositoryResult[bool]:
        try:
            if self._external_session:
                deleted = (
                    self.session.query(self.model_class)
                    .filter(self.model_class.id == entity_id)
                    .delete(synchronize_session=False)
                )
                self.session.flush()
            else:
                with transaction():
                    deleted = (
                        self.session.query(self.model_class)
                        .filter(self.model_class.id == entity_id)
                        .delete(synchronize_session=False)
                    )
                    self.session.flush()

            if deleted > 0:
                logger.info("Deleted %s id=%s", self.model_class.__name__, entity_id)
                return RepositoryResult.ok(True)
            return RepositoryResult.not_found(f"{self.model_class.__name__} with ID {entity_id}")
        except IntegrityError as e:
            logger.exception("Integrity error on delete: %s", e)
            return RepositoryResult.error(f"Cannot delete due to integrity constraints: {str(e)}")
        except SQLAlchemyError as e:
            logger.exception("DB error on delete: %s", e)
            return RepositoryResult.error(f"Database error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error on delete: %s", e)
            return RepositoryResult.error(f"Unexpected error: {str(e)}")

    def soft_delete(self, entity_id: int) -> RepositoryResult[bool]:
        """
        Marca `deleted_at` se o modelo suportar (soft delete).
        """
        try:
            if not hasattr(self.model_class, "deleted_at"):
                return RepositoryResult.error(f"{self.model_class.__name__} does not support soft delete")

            now = datetime.utcnow()

            if self._external_session:
                updated = (
                    self.session.query(self.model_class)
                    .filter(self.model_class.id == entity_id)
                    .update({"deleted_at": now}, synchronize_session=False)
                )
                self.session.flush()
            else:
                with transaction():
                    updated = (
                        self.session.query(self.model_class)
                        .filter(self.model_class.id == entity_id)
                        .update({"deleted_at": now}, synchronize_session=False)
                    )
                    self.session.flush()

            if updated > 0:
                logger.info("Soft deleted %s id=%s", self.model_class.__name__, entity_id)
                return RepositoryResult.ok(True)
            return RepositoryResult.not_found(f"{self.model_class.__name__} with ID {entity_id}")
        except SQLAlchemyError as e:
            logger.exception("DB error on soft_delete: %s", e)
            return RepositoryResult.error(f"Database error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error on soft_delete: %s", e)
            return RepositoryResult.error(f"Unexpected error: {str(e)}")


# =============================================================================
# Async (placeholder para futuro)
# =============================================================================

class BaseRepositoryAsync(Generic[T]):
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class

    async def get_by_id(self, entity_id: int) -> RepositoryResult[T]:
        raise NotImplementedError("Async repository not yet implemented")

    async def get_all(self, skip: int = 0, limit: int = 100) -> RepositoryListResult[T]:
        raise NotImplementedError("Async repository not yet implemented")

    async def create(self, entity: T) -> RepositoryResult[T]:
        raise NotImplementedError("Async repository not yet implemented")

    async def update(self, entity: T) -> RepositoryResult[T]:
        raise NotImplementedError("Async repository not yet implemented")

    async def delete(self, entity_id: int) -> RepositoryResult[bool]:
        raise NotImplementedError("Async repository not yet implemented")


# =============================================================================
# Factory
# =============================================================================

class RepositoryFactory:
    """
    Factory para instanciar repositórios com DI.
    """

    _repositories: Dict[Type, Type[BaseRepository]] = {}

    @classmethod
    def register_repository(cls, model_class: Type[T], repository_class: Type[BaseRepository[T]]) -> None:
        cls._repositories[model_class] = repository_class

    @classmethod
    def create_repository(cls, model_class: Type[T], session: Optional[Session] = None) -> BaseRepository[T]:
        repo_cls: Type[BaseRepository[T]] = cls._repositories.get(model_class, BaseRepository)  # type: ignore[assignment]
        return repo_cls(model_class, session)

    @classmethod
    def get_registered_repositories(cls) -> Dict[Type, Type[BaseRepository]]:
        return cls._repositories.copy()


# =============================================================================
# Unit of Work / Manager
# =============================================================================

class RepositoryManager:
    """
    Coordena múltiplos repositórios compartilhando a mesma sessão.
    Implementa um padrão Unit of Work simples.
    """

    def __init__(self, session: Optional[Session] = None):
        self._session = session or get_session()
        self._repositories: Dict[Type, BaseRepository] = {}

    def get_repository(self, model_class: Type[T]) -> BaseRepository[T]:
        if model_class not in self._repositories:
            self._repositories[model_class] = RepositoryFactory.create_repository(model_class, self._session)
        return self._repositories[model_class]

    @contextmanager
    def transaction(self):
        """
        with RepositoryManager().transaction():
            repo_a = rm.get_repository(ModelA)
            repo_b = rm.get_repository(ModelB)
            repo_a.create(a); repo_b.create(b)
        """
        try:
            yield self
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        finally:
            # Fecha apenas se não houver transação ativa
            try:
                # SQLAlchemy 1.4/2.0: get_transaction() retorna transação atual ou None
                tx = getattr(self._session, "get_transaction", None)
                if callable(tx):
                    if tx() is None:
                        self._session.close()
                else:
                    # Fallback genérico
                    self._session.close()
            except Exception:
                # Nunca deixe escapar erro de close
                pass

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def close(self) -> None:
        try:
            self._session.close()
        except Exception:
            pass


# =============================================================================
# Decorators
# =============================================================================

def with_repository_error_handling(func: Callable[..., Any]):
    """
    Decorator para tratamento consistente de erros em métodos customizados.
    Se o método já retorna RepositoryResult/RepositoryListResult, apenas propaga.
    """

    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            return result
        except IntegrityError as e:
            logger.exception("Integrity error in %s: %s", func.__name__, e)
            # tenta inferir tipo de retorno
            return RepositoryResult.error(f"Data integrity error: {str(e)}")
        except SQLAlchemyError as e:
            logger.exception("DB error in %s: %s", func.__name__, e)
            return RepositoryResult.error(f"Database error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error in %s: %s", func.__name__, e)
            return RepositoryResult.error(f"Unexpected error: {str(e)}")

    return wrapper


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "BaseRepository",
    "BaseRepositoryAsync",
    "IRepository",
    "RepositoryResult",
    "RepositoryListResult",
    "RepositoryFactory",
    "RepositoryManager",
    "with_repository_error_handling",
]
