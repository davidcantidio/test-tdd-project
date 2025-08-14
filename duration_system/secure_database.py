"""
🔐 Secure Database Manager with SQLCipher Encryption

Enterprise-grade database security implementation addressing SEC-002:
- SQLCipher-based database encryption
- Secure key management and rotation
- Migration from unencrypted to encrypted databases
- Transparent encryption/decryption operations
- SOC 2 compliant data protection

Security Features:
1. AES-256 database encryption via SQLCipher
2. PBKDF2 key derivation with high iteration count
3. Secure key storage with environment variable fallback
4. Database migration with integrity verification
5. Connection pooling with encrypted connections
"""

import os
import secrets
import hashlib
import sqlite3
from pathlib import Path
from typing import Any, Optional, Dict, List, Union, ContextManager
from datetime import datetime
import threading
import queue
from contextlib import contextmanager
import logging

try:
    import pysqlcipher3.dbapi2 as sqlite
    SQLCIPHER_AVAILABLE = True
except ImportError:
    import sqlite3 as sqlite
    SQLCIPHER_AVAILABLE = False
    logging.warning("SQLCipher not available - falling back to standard SQLite")


class SecureDatabaseManager:
    """
    Secure database manager with SQLCipher encryption.
    
    Provides enterprise-grade database security including:
    - AES-256 encryption of database files
    - Secure key management and rotation
    - Migration from unencrypted databases
    - Connection pooling with encryption
    """
    
    def __init__(self, 
                 db_path: Union[str, Path], 
                 encryption_key: Optional[str] = None,
                 pool_size: int = 10,
                 key_iterations: int = 256000):
        """
        Initialize secure database manager.
        
        Args:
            db_path: Path to database file
            encryption_key: Encryption key (if None, generates new one)
            pool_size: Connection pool size
            key_iterations: PBKDF2 iterations for key derivation
        """
        self.db_path = Path(db_path)
        self.encrypted_db_path = self.db_path.with_suffix('.encrypted.db')
        self.pool_size = pool_size
        self.key_iterations = key_iterations
        
        # Thread-safe connection pool
        self._connection_pool = queue.Queue(maxsize=pool_size)
        self._pool_lock = threading.Lock()
        
        # Security configuration
        self.encryption_key = encryption_key or self._get_or_create_encryption_key()
        self.derived_key = self._derive_key(self.encryption_key)
        
        # Statistics
        self.stats = {
            "encrypted_connections": 0,
            "failed_connections": 0,
            "migrations_completed": 0,
            "key_rotations": 0
        }
        
        # Initialize encrypted database if needed
        self._initialize_encrypted_database()
    
    def _get_or_create_encryption_key(self) -> str:
        """
        Get encryption key from environment or generate new one.
        
        Returns:
            Encryption key as hex string
        """
        # Try to get key from environment variable
        env_key = os.getenv('DATABASE_ENCRYPTION_KEY')
        if env_key:
            return env_key
        
        # Generate new cryptographically secure key
        key = secrets.token_hex(32)  # 256-bit key
        
        # Save to key file with secure permissions
        key_file = self.db_path.parent / '.db_key'
        try:
            with open(key_file, 'w') as f:
                f.write(key)
            # Set secure file permissions (owner read/write only)
            os.chmod(key_file, 0o600)
            logging.info(f"Generated new encryption key and saved to {key_file}")
        except OSError as e:
            logging.warning(f"Could not save key file: {e}")
        
        return key
    
    def _derive_key(self, base_key: str) -> str:
        """
        Derive encryption key using PBKDF2.
        
        Args:
            base_key: Base encryption key
            
        Returns:
            Derived key for SQLCipher
        """
        # Use database path as salt for deterministic but unique keys
        salt = hashlib.sha256(str(self.db_path).encode()).digest()[:16]
        
        # Derive key using PBKDF2
        derived = hashlib.pbkdf2_hmac(
            'sha256',
            base_key.encode(),
            salt,
            self.key_iterations
        )
        
        return derived.hex()
    
    def _initialize_encrypted_database(self):
        """Initialize encrypted database and connection pool."""
        if not SQLCIPHER_AVAILABLE:
            logging.warning("SQLCipher not available - using unencrypted database")
            return
        
        # Create encrypted database if it doesn't exist
        if not self.encrypted_db_path.exists():
            self._create_encrypted_database()
        
        # Initialize connection pool
        self._initialize_connection_pool()
    
    def _create_encrypted_database(self):
        """Create new encrypted database."""
        try:
            conn = self._create_encrypted_connection()
            # Test the connection
            conn.execute("CREATE TABLE IF NOT EXISTS _encryption_test (id INTEGER)")
            conn.execute("DROP TABLE IF EXISTS _encryption_test")
            conn.close()
            
            self.stats["encrypted_connections"] += 1
            logging.info(f"Created encrypted database: {self.encrypted_db_path}")
            
        except Exception as e:
            self.stats["failed_connections"] += 1
            logging.error(f"Failed to create encrypted database: {e}")
            raise
    
    def _create_encrypted_connection(self) -> sqlite.Connection:
        """
        Create new encrypted SQLite connection.
        
        Returns:
            Encrypted SQLite connection
        """
        if not SQLCIPHER_AVAILABLE:
            # Fallback to regular SQLite
            return sqlite3.connect(str(self.db_path))
        
        conn = sqlite.connect(str(self.encrypted_db_path))
        
        # Set encryption key (PRAGMA key must be first command)
        conn.execute(f"PRAGMA key = '{self.derived_key}'")
        
        # Configure SQLCipher security settings
        conn.execute("PRAGMA cipher_page_size = 4096")  # Standard page size
        conn.execute("PRAGMA kdf_iter = 256000")        # High iteration count
        conn.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512")
        conn.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512")
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode = WAL")
        
        return conn
    
    def _initialize_connection_pool(self):
        """Initialize connection pool with encrypted connections."""
        with self._pool_lock:
            for _ in range(self.pool_size):
                try:
                    conn = self._create_encrypted_connection()
                    self._connection_pool.put(conn)
                except Exception as e:
                    logging.error(f"Failed to create pooled connection: {e}")
    
    @contextmanager
    def get_connection(self) -> ContextManager[sqlite.Connection]:
        """
        Get encrypted database connection from pool.
        
        Yields:
            Encrypted SQLite connection
        """
        conn = None
        try:
            # Get connection from pool (blocking if pool is empty)
            conn = self._connection_pool.get(timeout=5.0)
            yield conn
        except queue.Empty:
            # Pool exhausted, create temporary connection
            conn = self._create_encrypted_connection()
            yield conn
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                try:
                    # Return connection to pool
                    self._connection_pool.put_nowait(conn)
                except queue.Full:
                    # Pool full, close connection
                    conn.close()
    
    def migrate_from_unencrypted(self, source_db_path: Union[str, Path]) -> bool:
        """
        Migrate data from unencrypted database to encrypted database.
        
        Args:
            source_db_path: Path to unencrypted source database
            
        Returns:
            True if migration successful
        """
        source_path = Path(source_db_path)
        
        if not source_path.exists():
            logging.warning(f"Source database does not exist: {source_path}")
            return False
        
        if not SQLCIPHER_AVAILABLE:
            logging.warning("SQLCipher not available - copying database as-is")
            import shutil
            shutil.copy2(source_path, self.db_path)
            return True
        
        try:
            # Open source (unencrypted) database
            source_conn = sqlite3.connect(str(source_path))
            
            # Open target (encrypted) database
            with self.get_connection() as target_conn:
                # Get all table names
                tables = source_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                
                for (table_name,) in tables:
                    # Skip sqlite internal tables
                    if table_name.startswith('sqlite_'):
                        continue
                    
                    logging.info(f"Migrating table: {table_name}")
                    
                    # Get table schema
                    schema = source_conn.execute(
                        f"SELECT sql FROM sqlite_master WHERE name='{table_name}'"
                    ).fetchone()
                    
                    if schema:
                        # Create table in encrypted database
                        target_conn.execute(schema[0])
                        
                        # Copy data
                        rows = source_conn.execute(f"SELECT * FROM {table_name}").fetchall()
                        if rows:
                            # Get column count for placeholder string
                            columns = source_conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                            placeholders = ','.join(['?' for _ in columns])
                            
                            target_conn.executemany(
                                f"INSERT INTO {table_name} VALUES ({placeholders})",
                                rows
                            )
                
                target_conn.commit()
            
            source_conn.close()
            
            # Verify migration
            if self._verify_migration(source_path):
                # Backup original and rename encrypted
                backup_path = source_path.with_suffix('.backup.db')
                source_path.rename(backup_path)
                
                self.stats["migrations_completed"] += 1
                logging.info(f"Migration completed successfully. Original backed up to {backup_path}")
                return True
            else:
                logging.error("Migration verification failed")
                return False
                
        except Exception as e:
            logging.error(f"Migration failed: {e}")
            return False
    
    def _verify_migration(self, source_db_path: Path) -> bool:
        """
        Verify migration integrity by comparing record counts.
        
        Args:
            source_db_path: Path to source database
            
        Returns:
            True if verification passed
        """
        try:
            source_conn = sqlite3.connect(str(source_db_path))
            
            with self.get_connection() as target_conn:
                # Get table names from source
                tables = source_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                
                for (table_name,) in tables:
                    if table_name.startswith('sqlite_'):
                        continue
                    
                    # Compare record counts
                    source_count = source_conn.execute(
                        f"SELECT COUNT(*) FROM {table_name}"
                    ).fetchone()[0]
                    
                    target_count = target_conn.execute(
                        f"SELECT COUNT(*) FROM {table_name}"
                    ).fetchone()[0]
                    
                    if source_count != target_count:
                        logging.error(
                            f"Record count mismatch in {table_name}: "
                            f"source={source_count}, target={target_count}"
                        )
                        return False
            
            source_conn.close()
            logging.info("Migration verification passed")
            return True
            
        except Exception as e:
            logging.error(f"Migration verification failed: {e}")
            return False
    
    def rotate_encryption_key(self, new_key: str) -> bool:
        """
        Rotate database encryption key.
        
        Args:
            new_key: New encryption key
            
        Returns:
            True if rotation successful
        """
        if not SQLCIPHER_AVAILABLE:
            logging.warning("Key rotation not available without SQLCipher")
            return False
        
        try:
            # Create temporary database with new key
            temp_path = self.encrypted_db_path.with_suffix('.temp.db')
            new_derived_key = self._derive_key(new_key)
            
            # Copy data to new encrypted database
            with self.get_connection() as source_conn:
                source_conn.execute(f"ATTACH DATABASE '{temp_path}' AS temp_db KEY '{new_derived_key}'")
                
                # Copy all tables
                tables = source_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                
                for (table_name,) in tables:
                    if table_name.startswith('sqlite_'):
                        continue
                    
                    # Get schema and copy to new database
                    schema = source_conn.execute(
                        f"SELECT sql FROM sqlite_master WHERE name='{table_name}'"
                    ).fetchone()
                    
                    if schema:
                        source_conn.execute(f"CREATE TABLE temp_db.{table_name} AS SELECT * FROM {table_name}")
                
                source_conn.execute("DETACH DATABASE temp_db")
            
            # Replace old database with new one
            backup_path = self.encrypted_db_path.with_suffix('.backup_old_key.db')
            self.encrypted_db_path.rename(backup_path)
            temp_path.rename(self.encrypted_db_path)
            
            # Update keys
            self.encryption_key = new_key
            self.derived_key = new_derived_key
            
            # Reinitialize connection pool
            self._close_all_connections()
            self._initialize_connection_pool()
            
            self.stats["key_rotations"] += 1
            logging.info("Encryption key rotation completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Key rotation failed: {e}")
            return False
    
    def _close_all_connections(self):
        """Close all connections in the pool."""
        with self._pool_lock:
            while not self._connection_pool.empty():
                try:
                    conn = self._connection_pool.get_nowait()
                    conn.close()
                except queue.Empty:
                    break
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database security statistics."""
        stats = self.stats.copy()
        stats.update({
            "encryption_enabled": SQLCIPHER_AVAILABLE,
            "database_path": str(self.encrypted_db_path if SQLCIPHER_AVAILABLE else self.db_path),
            "key_iterations": self.key_iterations,
            "pool_size": self.pool_size,
            "pool_available": self._connection_pool.qsize(),
        })
        return stats
    
    def health_check(self) -> bool:
        """
        Perform database health check.
        
        Returns:
            True if database is healthy
        """
        try:
            with self.get_connection() as conn:
                # Basic connectivity test
                conn.execute("SELECT 1").fetchone()
                
                # Encryption verification (SQLCipher only)
                if SQLCIPHER_AVAILABLE:
                    # This will fail if encryption is not working
                    conn.execute("PRAGMA cipher_integrity_check").fetchone()
                
                return True
        except Exception as e:
            logging.error(f"Database health check failed: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._close_all_connections()


# Factory function for easy database manager creation
def create_secure_database(db_path: Union[str, Path], 
                          encryption_key: Optional[str] = None) -> SecureDatabaseManager:
    """
    Create secure database manager with automatic configuration.
    
    Args:
        db_path: Database file path
        encryption_key: Optional encryption key
        
    Returns:
        Configured secure database manager
    """
    return SecureDatabaseManager(db_path, encryption_key)


# Migration utility for existing databases
def migrate_database_to_encrypted(source_path: Union[str, Path], 
                                target_path: Optional[Union[str, Path]] = None,
                                encryption_key: Optional[str] = None) -> bool:
    """
    Migrate existing unencrypted database to encrypted format.
    
    Args:
        source_path: Path to unencrypted database
        target_path: Path for encrypted database (optional)
        encryption_key: Encryption key (optional)
        
    Returns:
        True if migration successful
    """
    source = Path(source_path)
    target = Path(target_path) if target_path else source.with_suffix('.encrypted.db')
    
    manager = SecureDatabaseManager(target, encryption_key)
    return manager.migrate_from_unencrypted(source)


if __name__ == "__main__":
    # Example usage and testing
    import tempfile
    import shutil
    
    def test_secure_database():
        """Test secure database functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            
            # Create test database
            print("Creating secure database...")
            with create_secure_database(test_db) as db:
                with db.get_connection() as conn:
                    conn.execute("CREATE TABLE test_table (id INTEGER, data TEXT)")
                    conn.execute("INSERT INTO test_table VALUES (1, 'encrypted data')")
                    conn.commit()
                
                # Health check
                print(f"Health check: {'PASS' if db.health_check() else 'FAIL'}")
                
                # Show stats
                print(f"Database stats: {db.get_stats()}")
    
    test_secure_database()