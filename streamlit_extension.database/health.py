# Auto-gerado por tools/refactor_split_db.py — NÃO EDITAR À MÃO
from __future__ import annotations

def check_database_health(manager) -> Dict[str, Any]:
    """Comprehensive database health check with diagnostics.

        Performs connection tests against both framework and timer databases and
        reports the availability of optional dependencies used by the
        application.

        Returns:
            Dict[str, Any]: Dictionary describing connection status and
                dependency availability.

        Example:
            >>> health = db_manager.check_database_health()
            >>> health["framework_db_connected"]
        """
    health = {'framework_db_exists': manager.framework_db_path.exists(), 'timer_db_exists': manager.timer_db_path.exists(), 'framework_db_connected': False, 'timer_db_connected': False, 'sqlalchemy_available': SQLALCHEMY_AVAILABLE, 'pandas_available': PANDAS_AVAILABLE}
    try:
        with manager.get_connection('framework') as conn:
            if SQLALCHEMY_AVAILABLE:
                conn.execute(text('SELECT 1'))
            else:
                conn.execute('SELECT 1')
            health['framework_db_connected'] = True
    except Exception as e:
        logging.getLogger(__name__).debug('Framework DB connection failed: %s', e, exc_info=False)
        health['framework_db_connected'] = False
    if manager.timer_db_path.exists():
        try:
            with manager.get_connection('timer') as conn:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text('SELECT 1'))
                else:
                    conn.execute('SELECT 1')
                health['timer_db_connected'] = True
        except Exception as e:
            logging.getLogger(__name__).debug('Timer DB connection failed: %s', e, exc_info=False)
            health['timer_db_connected'] = False
    return health

def get_query_statistics(manager) -> Dict[str, Any]:
    """Get detailed query performance statistics.

        Returns:
            Dict[str, Any]: Mapping of engine names to connection pool metrics.

        Example:
            >>> stats = db_manager.get_query_statistics()
        """
    stats: Dict[str, Any] = {}
    if not SQLALCHEMY_AVAILABLE:
        return stats
    for name, engine in manager.engines.items():
        pool = getattr(engine, 'pool', None)
        stats[name] = {'checked_out': getattr(pool, 'checkedout', lambda: None)(), 'size': getattr(pool, 'size', lambda: None)()}
    return stats

def optimize_database(manager) -> Dict[str, Any]:
    """Run database optimization and return performance report.

        Executes ``VACUUM`` on all available databases and reports size before
        and after the operation.

        Returns:
            Dict[str, Any]: Optimization report keyed by database name.

        Example:
            >>> report = db_manager.optimize_database()
        """
    report: Dict[str, Any] = {}
    for name, path in {'framework': manager.framework_db_path, 'timer': manager.timer_db_path}.items():
        if not path.exists():
            continue
        size_before = path.stat().st_size
        with sqlite3.connect(str(path)) as conn:
            conn.execute('VACUUM')
        size_after = path.stat().st_size
        report[name] = {'size_before': size_before, 'size_after': size_after}
    return report

def create_backup(manager, backup_path: Optional[str]=None) -> str:
    """Create full database backup with verification.

        Args:
            backup_path: Destination file path. When ``None`` a ``.bak`` file is
                created next to the framework database.

        Returns:
            str: Path to the created backup file.

        Example:
            >>> backup_file = db_manager.create_backup()
        """
    backup_file = backup_path or str(manager.framework_db_path.with_suffix('.bak'))
    with sqlite3.connect(str(manager.framework_db_path)) as src, sqlite3.connect(backup_file) as dst:
        src.backup(dst)
    return backup_file

def restore_backup(manager, backup_path: str, verify: bool=True) -> bool:
    """Restore database from backup with integrity verification.

        Args:
            backup_path: Path to backup file created by :meth:`create_backup`.
            verify: When ``True`` perform ``PRAGMA integrity_check`` after
                restoration.

        Returns:
            bool: ``True`` if restore succeeded and verification passed.

        Example:
            >>> db_manager.restore_backup("framework.bak")
        """
    with sqlite3.connect(backup_path) as src, sqlite3.connect(str(manager.framework_db_path)) as dst:
        src.backup(dst)
    if verify:
        with sqlite3.connect(str(manager.framework_db_path)) as conn:
            result = conn.execute('PRAGMA integrity_check').fetchone()
            return result[0] == 'ok'
    return True

