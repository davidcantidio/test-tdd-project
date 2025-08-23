#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗄️ MODELS - SQLAlchemy Database Configuration

Camada de configuração do SQLAlchemy integrada aos padrões existentes do projeto.
Foco em: segurança, desempenho (<1ms), simplicidade de integração e suporte multi‑ambiente.

Uso:
    from streamlit_extension.models.database import (
        DatabaseConfig,
        get_database_url,
        get_database_config,
        create_db_engine,              # ← nome não conflita com SQLAlchemy
        check_database_connection,
        get_database_info,
        optimize_database_for_tdd,
        create_development_database,
        setup_test_database,
        setup_production_database,
    )

Principais pontos:
- SQLite otimizado (WAL, foreign_keys, busy_timeout, cache)
- Pooling adequado por dialeto (StaticPool p/ SQLite; QueuePool p/ outros)
- Integração com DatabaseManager (quando disponível)
- API estável e segura (sem double-encoding de paths; sem sombra de nomes)
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from sqlalchemy import text, event
from sqlalchemy.engine import Engine, URL
from sqlalchemy.pool import StaticPool, QueuePool

# Import do criador de engine com alias para evitar conflito com função local
from sqlalchemy import create_engine as sa_create_engine

logger = logging.getLogger(__name__)

# =============================================================================
# Helpers internos
# =============================================================================


def _is_sqlite_url(url: str) -> bool:
    return url.startswith("sqlite://")


def _coalesce_call(attr: Any) -> Any:
    """
    Para inspecionar propriedades do pool que podem ser métodos (QueuePool.size()).
    Se for chamável, executa e retorna; do contrário, retorna o atributo bruto.
    """
    if callable(attr):
        try:
            return attr()
        except Exception:  # pragma: no cover - diagnóstico apenas
            return "N/A"
    return attr


# =============================================================================
# Database Configuration
# =============================================================================


class DatabaseConfig:
    """
    Gerenciador de configuração de banco p/ integração SQLAlchemy.

    Fornece configuração específica por ambiente com otimizações para TDD/TDAH.
    """

    # Defaults por ambiente
    ENVIRONMENTS = {
        "development": {
            "echo": False,  # pode habilitar por variável de ambiente
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "connect_args": {
                "check_same_thread": False,
                "timeout": 30,
            },
        },
        "testing": {
            "echo": False,
            "pool_size": 1,
            "max_overflow": 0,
            "pool_timeout": 5,
            "pool_recycle": -1,
            "connect_args": {
                "check_same_thread": False,
                "timeout": 5,
            },
        },
        "production": {
            "echo": False,
            "pool_size": 20,
            "max_overflow": 30,
            "pool_timeout": 30,
            "pool_recycle": 7200,
            "connect_args": {
                "check_same_thread": False,
                "timeout": 60,
            },
        },
    }

    def __init__(self, environment: str = "development"):
        self.environment = environment
        self._config = self.ENVIRONMENTS.get(environment, self.ENVIRONMENTS["development"])

        # Permite forçar echo via env sem alterar código
        if os.environ.get("SQL_ECHO", "").strip().lower() in {"1", "true", "yes"}:
            self._config["echo"] = True

    # --------------------------------------------------------------------- #
    # Resolução do caminho e URL
    # --------------------------------------------------------------------- #

    def get_database_url(self, db_path: Optional[str] = None) -> str:
        """
        Retorna uma URL SQLAlchemy correta (sem double-encoding).
        Prioridade:
          1) db_path explícito
          2) env FRAMEWORK_DB
          3) DatabaseManager (se existir)
          4) ./framework.db
        """
        if not db_path:
            db_path = self._resolve_db_path()

        # Caminho absoluto normalizado
        path = Path(db_path).expanduser().resolve()

        # Garante que o diretório exista (evita erro silencioso em Windows/Linux)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Cria URL segura usando API do SQLAlchemy (evita problemas de quoting)
        url = URL.create(
            drivername="sqlite+pysqlite",
            database=str(path),
        )
        return str(url)

    def _resolve_db_path(self) -> str:
        env_path = os.environ.get("FRAMEWORK_DB")
        if env_path:
            return env_path

        # Integração com DatabaseManager (graciosa)
        try:
            from streamlit_extension.utils.database import DatabaseManager  # type: ignore

            db_manager = DatabaseManager()
            if hasattr(db_manager, "db_path") and db_manager.db_path:
                return str(db_manager.db_path)
        except ImportError:
            logger.info("DatabaseManager não disponível para integração")
        except Exception as e:  # pragma: no cover - apenas log
            logger.warning(f"Não foi possível integrar com DatabaseManager: {e}")

        return str(Path.cwd() / "framework.db")

    # --------------------------------------------------------------------- #
    # Criação de Engine
    # --------------------------------------------------------------------- #

    def create_engine(self, db_path: Optional[str] = None, **overrides: Any) -> Engine:
        """
        Cria Engine SQLAlchemy com configuração otimizada e segura.
        """
        database_url = self.get_database_url(db_path)
        cfg = {**self._config, **overrides}

        # Parâmetros específicos por dialeto
        if _is_sqlite_url(database_url):
            # Para SQLite em arquivo, usar StaticPool + check_same_thread=False
            # garante reuso de conexão com segurança entre threads do Streamlit.
            pool_kwargs = {
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

    # --------------------------------------------------------------------- #
    # PRAGMAs e tunning específicos para SQLite
    # --------------------------------------------------------------------- #

    def _configure_sqlite_engine(self, engine: Engine) -> None:
        """
        Ajustes de SQLite:
        - foreign_keys ON
        - WAL
        - synchronous NORMAL
        - busy_timeout 5s
        - temp_store MEMORY
        - mmap 256MB
        - cache_size ~10MB (negativo = KB em páginas)
        Obs.: NÃO habilitamos read_uncommitted por padrão (segurança > velocidade).
        """

        @event.listens_for(engine, "connect")
        def set_sqlite_pragmas(dbapi_connection, _connection_record):  # noqa: N802
            cursor = dbapi_connection.cursor()

            # Integridade e concorrência
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=5000")

            # Performance
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=268435456")  # 256 MB
            cursor.execute("PRAGMA cache_size=-10000")    # ~10MB

            # Segurança > performance (não usar dirty reads por padrão)
            cursor.execute("PRAGMA read_uncommitted=OFF")

            cursor.close()

        logger.info("Engine SQLite configurada com PRAGMAs de desempenho e segurança")


# =============================================================================
# Instância Global
# =============================================================================

_database_config: Optional[DatabaseConfig] = None


def get_database_config(environment: Optional[str] = None) -> DatabaseConfig:
    """
    Retorna instância global (um por processo) respeitando o ambiente.
    """
    global _database_config
    if _database_config is None or (environment and _database_config.environment != environment):
        env = environment or os.environ.get("TDD_ENVIRONMENT", "development")
        _database_config = DatabaseConfig(env)
    return _database_config


def get_database_url(db_path: Optional[str] = None, environment: Optional[str] = None) -> str:
    return get_database_config(environment).get_database_url(db_path)


# Nome não conflita com sqlalchemy.create_engine (alias sa_create_engine)
def create_db_engine(
    db_path: Optional[str] = None,
    environment: Optional[str] = None,
    **kwargs: Any,
) -> Engine:
    """
    Função de conveniência para criar Engine sem risco de sombra de nomes.
    """
    return get_database_config(environment).create_engine(db_path, **kwargs)


# =============================================================================
# Utilidades de Banco
# =============================================================================


def check_database_connection(engine: Engine) -> bool:
    """
    Verifica saúde da conexão (TRUE=OK).
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return bool(result.scalar() == 1)
    except Exception as e:
        logger.error(f"Falha no health check do banco: {e}")
        return False


def get_database_info(engine: Engine) -> Dict[str, Any]:
    """
    Informações diagnósticas do banco e do pool.
    """
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
        except Exception as e:  # pragma: no cover - diagnóstico
            info["sqlite"] = {"error": str(e)}

    return info


def optimize_database_for_tdd(engine: Engine) -> None:
    """
    Otimizações pós‑init (ANALYZE/REINDEX em dev).
    """
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
# Atalhos por Ambiente
# =============================================================================


def create_development_database(db_path: Optional[str] = None) -> Engine:
    """
    Cria e valida banco de desenvolvimento com otimizações ativas.
    """
    engine = create_db_engine(db_path, environment="development")
    optimize_database_for_tdd(engine)
    if not check_database_connection(engine):
        raise ConnectionError("Falha ao conectar no banco de desenvolvimento")
    logger.info(f"Banco de desenvolvimento pronto: {engine.url}")
    return engine


def setup_test_database() -> Engine:
    """
    Banco de testes isolado (memória).
    """
    # URL correta de memória em SQLAlchemy 2.x
    mem_url = URL.create(drivername="sqlite+pysqlite", database=":memory:")
    engine = sa_create_engine(
        mem_url,
        echo=False,
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

    # Ajusta pragmas também para o in-memory
    DatabaseConfig("testing")._configure_sqlite_engine(engine)
    return engine


def setup_production_database(db_path: str) -> Engine:
    """
    Banco de produção com verificações básicas.
    """
    engine = create_db_engine(db_path, environment="production")
    # Em produção mantemos ANALYZE; REINDEX fica a cargo de manutenção
    optimize_database_for_tdd(engine)
    if not check_database_connection(engine):
        raise ConnectionError("Falha ao conectar no banco de produção")
    return engine


# =============================================================================
# Integrações (opcionais e seguras)
# =============================================================================


def integrate_with_connection_pool() -> None:
    """
    Gatilho para integração com pools existentes (DatabaseManager), quando houver.
    Mantemos separado do SQLAlchemy para evitar acoplamento.
    """
    try:
        # Essas importações são opcionais e não quebram se ausentes
        from streamlit_extension.database.connection import (  # type: ignore
            get_connection,
            release_connection,
        )

        _ = (get_connection, release_connection)  # evita lint de variável não usada
        logger.info("Integração com padrões de pool externo disponível.")
    except ImportError:
        logger.info("Pool externo não encontrado; usando apenas pooling do SQLAlchemy.")


def sync_with_database_manager_config() -> None:
    """
    Sincroniza configuração com DatabaseManager (se existir).
    """
    try:
        from streamlit_extension.utils.database import DatabaseManager  # type: ignore

        _ = DatabaseManager  # sem uso direto; apenas valida presença
        logger.info("Config sincronizável com DatabaseManager (se necessário).")
    except ImportError:
        logger.info("DatabaseManager indisponível para sync de configuração.")


# =============================================================================
# Export público
# =============================================================================

__all__ = [
    "DatabaseConfig",
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
