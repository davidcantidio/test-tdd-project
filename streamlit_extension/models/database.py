#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗄️ MODELS - SQLAlchemy Database Configuration (Fixed)

- Corrige detecção do dialeto SQLite (inclui 'sqlite+pysqlite')
- Garante aplicação de PRAGMAs e pooling corretos
- Mantém API pública e padrões de segurança/desempenho do projeto
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from sqlalchemy import text, event
from sqlalchemy.engine import Engine, URL
from sqlalchemy.engine import make_url  # ← correção principal
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy import create_engine as sa_create_engine

logger = logging.getLogger(__name__)

# =============================================================================
# Helpers
# =============================================================================

def _is_sqlite_url(url_like: str | URL) -> bool:
    """
    Retorna True se a URL aponta para backend SQLite (inclui 'sqlite+pysqlite').
    Evita falsos negativos de 'startswith("sqlite://")'.
    """
    try:
        url_obj = url_like if isinstance(url_like, URL) else make_url(str(url_like))
        return url_obj.get_backend_name() == "sqlite"
    except Exception:  # fallback defensivo
        s = str(url_like)
        return s.startswith("sqlite://") or s.startswith("sqlite+pysqlite://")


def _coalesce_call(attr: Any) -> Any:
    if callable(attr):
        try:
            return attr()
        except Exception:  # pragma: no cover - diagnóstico
            return "N/A"
    return attr


# =============================================================================
# Database Configuration
# =============================================================================

class DatabaseConfig:
    """
    Gerencia configuração SQLAlchemy por ambiente com otimizações p/ TDD/TDAH.
    """
    ENVIRONMENTS = {
        "development": {
            "echo": False,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "connect_args": {"check_same_thread": False, "timeout": 30},
        },
        "testing": {
            "echo": False,
            "pool_size": 1,
            "max_overflow": 0,
            "pool_timeout": 5,
            "pool_recycle": -1,
            "connect_args": {"check_same_thread": False, "timeout": 5},
        },
        "production": {
            "echo": False,
            "pool_size": 20,
            "max_overflow": 30,
            "pool_timeout": 30,
            "pool_recycle": 7200,
            "connect_args": {"check_same_thread": False, "timeout": 60},
        },
    }

    def __init__(self, environment: str = "development"):
        self.environment = environment
        self._config = self.ENVIRONMENTS.get(environment, self.ENVIRONMENTS["development"])
        if os.environ.get("SQL_ECHO", "").strip().lower() in {"1", "true", "yes"}:
            self._config["echo"] = True

    # ------------------------------------------------------------------ #
    # URL & path resolution
    # ------------------------------------------------------------------ #
    def get_database_url(self, db_path: Optional[str] = None) -> str:
        """
        Gera URL SQLAlchemy correta (sem double-encoding).
        Prioridade: parâmetro → env FRAMEWORK_DB → DatabaseManager → ./framework.db
        """
        if not db_path:
            db_path = self._resolve_db_path()

        path = Path(db_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        url = URL.create(drivername="sqlite+pysqlite", database=str(path))
        return str(url)

    def _resolve_db_path(self) -> str:
        env_path = os.environ.get("FRAMEWORK_DB")
        if env_path:
            return env_path
        try:
            from streamlit_extension.utils.database import DatabaseManager  # type: ignore
            db_manager = DatabaseManager()
            if getattr(db_manager, "db_path", None):
                return str(db_manager.db_path)
        except ImportError:
            logger.info("DatabaseManager não disponível para integração")
        except Exception as e:  # pragma: no cover
            logger.warning(f"Não foi possível integrar com DatabaseManager: {e}")
        return str(Path.cwd() / "framework.db")

    # ------------------------------------------------------------------ #
    # Engine creation
    # ------------------------------------------------------------------ #
    def create_engine(self, db_path: Optional[str] = None, **overrides: Any) -> Engine:
        """
        Cria Engine SQLAlchemy com configuração otimizada por dialeto/ambiente.
        """
        database_url_str = self.get_database_url(db_path)
        database_url = make_url(database_url_str)  # trabalhar com URL tipada
        cfg = {**self._config, **overrides}

        if _is_sqlite_url(database_url):
            # Para SQLite (arquivo), preferimos StaticPool + check_same_thread=False
            pool_kwargs: Dict[str, Any] = {
                "poolclass": StaticPool,
                "pool_pre_ping": True,
                "connect_args": cfg.get("connect_args", {}),
            }
        else:
            pool_kwargs = {
                "poolclass": QueuePool,
                "pool_size": cfg.get("pool_size", 5),
                "max_overflow": cfg.get("max_overflow", 10),
                "pool_timeout": cfg.get("pool_timeout", 30),
                "pool_recycle": cfg.get("pool_recycle", 3600),
                "pool_pre_ping": True,
            }

        engine = sa_create_engine(
            database_url,
            echo=cfg.get("echo", False),
            future=True,
            **pool_kwargs,
        )

        if _is_sqlite_url(database_url):
            self._configure_sqlite_engine(engine)

        return engine

    # ------------------------------------------------------------------ #
    # SQLite PRAGMAs / tuning
    # ------------------------------------------------------------------ #
    def _configure_sqlite_engine(self, engine: Engine) -> None:
        """
        Ajustes de SQLite:
        - foreign_keys ON
        - WAL (somente para arquivos)
        - synchronous NORMAL
        - busy_timeout
        - temp_store MEMORY
        - mmap e cache_size (quando aplicável)
        """
        @event.listens_for(engine, "connect")
        def set_sqlite_pragmas(dbapi_connection, _connection_record):  # noqa: N802
            cursor = dbapi_connection.cursor()
            # Sem suposições sobre driver; aplicar com segurança:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA read_uncommitted=OFF")

            # Detecta se é arquivo (não ':memory:')
            try:
                database_name = dbapi_connection.execute("PRAGMA database_list").fetchone()
                is_memory = database_name and database_name[2] == ":memory:"
            except Exception:
                is_memory = False

            if not is_memory:
                # PRAGMAs válidos para arquivo
                try:
                    cursor.execute("PRAGMA journal_mode=WAL")
                except Exception:
                    pass  # alguns builds podem restringir

                try:
                    cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
                except Exception:
                    pass

                try:
                    cursor.execute("PRAGMA cache_size=-10000")    # ~10MB
                except Exception:
                    pass

            cursor.close()

        logger.info("Engine SQLite configurada com PRAGMAs de desempenho e segurança")

# =============================================================================
# Instância global & Facade
# =============================================================================

_database_config: Optional[DatabaseConfig] = None

def get_database_config(environment: Optional[str] = None) -> DatabaseConfig:
    global _database_config
    if _database_config is None or (environment and _database_config.environment != environment):
        env = environment or os.environ.get("TDD_ENVIRONMENT", "development")
        _database_config = DatabaseConfig(env)
    return _database_config

def get_database_url(db_path: Optional[str] = None, environment: Optional[str] = None) -> str:
    return get_database_config(environment).get_database_url(db_path)

def create_db_engine(
    db_path: Optional[str] = None,
    environment: Optional[str] = None,
    **kwargs: Any,
) -> Engine:
    return get_database_config(environment).create_engine(db_path, **kwargs)

# =============================================================================
# Utilities
# =============================================================================

def check_database_connection(engine: Engine) -> bool:
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return bool(result.scalar() == 1)
    except Exception as e:
        logger.error(f"Falha no health check do banco: {e}")
        return False

def get_database_info(engine: Engine) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "url": str(engine.url),
        "dialect": engine.dialect.name,
        "driver": engine.dialect.driver,
        "pool": {
            "class": engine.pool.__class__.__name__,
            "size": _coalesce_call(getattr(engine.pool, "size", "N/A")),
            "checked_in": _coalesce_call(getattr(engine.pool, "checkedin", "N/A")),
            "checked_out": _coalesce_call(getattr(engine.pool, "checkedout", "N/A")),
            "overflow": _coalesce_call(getattr(engine.pool, "overflow", "N/A")),
        },
    }
    if engine.dialect.name == "sqlite":
        try:
            with engine.connect() as conn:
                sqlite_version = conn.execute(text("SELECT sqlite_version()")).scalar()
                journal_mode = conn.execute(text("PRAGMA journal_mode")).scalar()
                foreign_keys = conn.execute(text("PRAGMA foreign_keys")).scalar()
            info["sqlite"] = {
                "version": sqlite_version,
                "journal_mode": journal_mode,
                "foreign_keys": bool(foreign_keys),
            }
        except Exception as e:  # pragma: no cover
            info["sqlite"] = {"error": str(e)}
    return info

def optimize_database_for_tdd(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.begin() as conn:
            conn.execute(text("ANALYZE"))
            if os.environ.get("TDD_ENVIRONMENT", "development") == "development":
                conn.execute(text("REINDEX"))
        logger.info("Banco otimizado para TDD (SQLite).")
    except Exception as e:  # pragma: no cover
        logger.warning(f"Falha ao otimizar banco para TDD: {e}")

# =============================================================================
# Environment shortcuts
# =============================================================================

def create_development_database(db_path: Optional[str] = None) -> Engine:
    engine = create_db_engine(db_path, environment="development")
    optimize_database_for_tdd(engine)
    if not check_database_connection(engine):
        raise ConnectionError("Falha ao conectar no banco de desenvolvimento")
    logger.info(f"Banco de desenvolvimento pronto: {engine.url}")
    return engine

def setup_test_database() -> Engine:
    mem_url = URL.create(drivername="sqlite+pysqlite", database=":memory:")
    engine = sa_create_engine(
        mem_url,
        echo=False,
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    DatabaseConfig("testing")._configure_sqlite_engine(engine)
    return engine

def setup_production_database(db_path: str) -> Engine:
    engine = create_db_engine(db_path, environment="production")
    optimize_database_for_tdd(engine)  # ANALYZE; REINDEX fica para manutenção
    if not check_database_connection(engine):
        raise ConnectionError("Falha ao conectar no banco de produção")
    return engine

# =============================================================================
# Integrações opcionais (logs apenas)
# =============================================================================

def integrate_with_connection_pool() -> None:
    try:
        from streamlit_extension.database.connection import (  # type: ignore
            get_connection, release_connection,
        )
        _ = (get_connection, release_connection)
        logger.info("Integração com pool externo disponível.")
    except ImportError:
        logger.info("Pool externo não encontrado; usando apenas pooling do SQLAlchemy.")

def sync_with_database_manager_config() -> None:
    try:
        from streamlit_extension.utils.database import DatabaseManager  # type: ignore
        _ = DatabaseManager
        logger.info("Config sincronizável com DatabaseManager (se necessário).")
    except ImportError:
        logger.info("DatabaseManager indisponível para sync de configuração.")

# =============================================================================
# Facade (backward compatibility)
# =============================================================================

class SQLAlchemyDatabase:
    def __init__(self, environment: str = "development", db_path: Optional[str] = None):
        self.config = DatabaseConfig(environment)
        self.db_path = db_path
        self._engine: Optional[Engine] = None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = self.config.create_engine(self.db_path)
        return self._engine

    def get_database_url(self) -> str:
        return self.config.get_database_url(self.db_path)

    def create_tables(self) -> None:
        from .base import Base
        Base.metadata.create_all(self.engine)

    def check_connection(self) -> bool:
        return check_database_connection(self.engine)

    def get_info(self) -> Dict[str, Any]:
        return get_database_info(self.engine)

    def optimize_for_tdd(self) -> None:
        optimize_database_for_tdd(self.engine)

__all__ = [
    "DatabaseConfig",
    "SQLAlchemyDatabase",
    "get_database_config",
    "get_database_url",
    "create_db_engine",
    "check_database_connection",
    "get_database_info",
    "optimize_database_for_tdd",
    "create_development_database",
    "setup_test_database",
    "setup_production_database",
    "integrate_with_connection_pool",
    "sync_with_database_manager_config",
]
