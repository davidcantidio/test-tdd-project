# Auto-gerado por tools/refactor_split_db.py — NÃO EDITAR À MÃO
from __future__ import annotations

def get_connection(manager, database_name: str='framework') -> Iterator[Union[Connection, SQLiteConnection]]:
    """
        Get a database connection from the pool.

        Args:
            database_name (str): Name of the database to connect to.
                Defaults to "framework".

        Returns:
            Connection: SQLAlchemy connection object with context manager support.

        Raises:
            ConnectionError: If unable to establish connection after retries.
            CircuitBreakerOpenError: If circuit breaker is open.

        Examples:
            >>> db = DatabaseManager()
            >>> with db.get_connection() as conn:
            ...     result = conn.execute("SELECT COUNT(*) FROM users")
            ...     print(result.fetchone()[0])
        """
    if SQLALCHEMY_AVAILABLE and database_name in manager.engines:
        conn = manager.engines[database_name].connect()
        try:
            conn.execute(text('PRAGMA foreign_keys = ON'))
            yield conn
        finally:
            conn.close()
    else:
        db_path = manager.framework_db_path if database_name == 'framework' else manager.timer_db_path
        if not db_path.exists():
            raise FileNotFoundError(f'Database not found: {db_path}')
        conn = sqlite3.connect(str(db_path), timeout=20)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        try:
            yield conn
        finally:
            conn.close()

def release_connection(manager, connection: Union[Connection, SQLiteConnection]) -> None:
    """Return connection to pool with cleanup.

        This method is provided for cases where a connection obtained via
        :meth:`get_connection` needs to be closed manually instead of using the
        context manager protocol.

        Args:
            connection: Connection instance to be returned.

        Example:
            >>> conn = next(db_manager.get_connection())
            >>> db_manager.release_connection(conn)
        """
    try:
        connection.close()
    except Exception:
        logger.warning('Failed to close connection', exc_info=True)

def transaction(manager, database_name: str='framework', isolation_level: Optional[str]=None, timeout: int=30) -> Iterator[Union[Connection, SQLiteConnection]]:
    """
        Transaction context manager with proper isolation and rollback support.
        
        Provides ACID transaction guarantees for critical operations, especially
        cascade deletes that may lock tables. Addresses report.md requirement:
        "Large numbers of cascade deletes may lock tables; wrap in transactions with proper isolation."
        
        Args:
            database_name: Database to connect to ("framework" or "timer")
            isolation_level: Transaction isolation level:
                - "READ_UNCOMMITTED": Lowest isolation, allows dirty reads
                - "READ_COMMITTED": Prevents dirty reads (default for most operations) 
                - "REPEATABLE_READ": Prevents dirty and non-repeatable reads
                - "SERIALIZABLE": Highest isolation, prevents all phenomena
                - None: Use database default
            timeout: Transaction timeout in seconds
            
        Returns:
            Connection with active transaction context
            
        Raises:
            Exception: Re-raises any exception after rollback
            
        Example:
            >>> with db.transaction(isolation_level="READ_COMMITTED") as conn:
            ...     conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
            ...     conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            ...     # Auto-commit on success, rollback on exception
        """
    with manager.get_connection(database_name) as conn:
        if isolation_level and SQLALCHEMY_AVAILABLE:
            if isolation_level in ['READ_UNCOMMITTED', 'READ_COMMITTED', 'REPEATABLE_READ', 'SERIALIZABLE']:
                conn.execute(text(f'PRAGMA read_uncommitted = {('ON' if isolation_level == 'READ_UNCOMMITTED' else 'OFF')}'))
        elif isolation_level and hasattr(conn, 'isolation_level'):
            if isolation_level == 'SERIALIZABLE':
                conn.execute('PRAGMA locking_mode = EXCLUSIVE')
            elif isolation_level == 'READ_COMMITTED':
                conn.execute('PRAGMA journal_mode = WAL')
        if hasattr(conn, 'execute'):
            if SQLALCHEMY_AVAILABLE:
                conn.execute(text(f'PRAGMA busy_timeout = {timeout * 1000}'))
            else:
                conn.execute(f'PRAGMA busy_timeout = {timeout * 1000}')
        if SQLALCHEMY_AVAILABLE:
            trans = conn.begin()
        else:
            conn.execute('BEGIN IMMEDIATE')
            trans = None
        try:
            yield conn
            if SQLALCHEMY_AVAILABLE and trans:
                trans.commit()
            else:
                conn.commit()
        except Exception as e:
            try:
                if SQLALCHEMY_AVAILABLE and trans:
                    trans.rollback()
                else:
                    conn.rollback()
                logger.error(f'Transaction rolled back due to error: {e}')
            except Exception as rollback_error:
                logger.error(f'Failed to rollback transaction: {rollback_error}')
            raise

def execute_query(manager, query: str, params: Optional[Dict[str, Any]]=None, database_name: str='framework') -> Union[Result, List[Dict[str, Any]]]:
    """Execute a raw SQL query.

        Args:
            query: SQL query string to execute.
            params: Optional mapping of parameters.
            database_name: Database identifier, defaults to ``framework``.

        Returns:
            SQLAlchemy ``Result`` when available or list of row dictionaries.
        """
    params = params or {}
    with manager.get_connection(database_name) as conn:
        if SQLALCHEMY_AVAILABLE:
            return conn.execute(text(query), params)
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

