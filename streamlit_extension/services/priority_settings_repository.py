"""
🎯 PrioritySettingsRepository - História 3.2
Repository for project-specific priority weight configuration persistence.

Implements repository pattern for clean architecture with SQLite backend.
"""

from abc import ABC, abstractmethod
from typing import Optional
import sqlite3
import logging
from datetime import datetime

from ..core.dto.priority_weights_dto import PriorityWeightsDTO
from ..database.connection import get_connection_context

logger = logging.getLogger(__name__)


class PrioritySettingsRepository(ABC):
    """
    Abstract repository interface for priority weight settings.
    
    Defines contract for managing project-specific priority weights
    with implementations free to use any persistence mechanism.
    """
    
    @abstractmethod
    def get_by_project_id(self, project_id: int) -> Optional[PriorityWeightsDTO]:
        """
        Get priority weights for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            PriorityWeightsDTO if found, None otherwise
        """
        pass
    
    @abstractmethod
    def save(self, weights: PriorityWeightsDTO) -> PriorityWeightsDTO:
        """
        Save or update priority weights for a project.
        
        Implements UPSERT logic - creates new record or updates existing one.
        
        Args:
            weights: Priority weights configuration to save
            
        Returns:
            Saved PriorityWeightsDTO with ID and timestamps
            
        Raises:
            ValueError: If weights don't sum to ~1.0 or validation fails
        """
        pass
    
    @staticmethod
    def get_default_weights() -> PriorityWeightsDTO:
        """
        Get default weight configuration.
        
        Returns default weights that preserve the 5:3:2:2 proportion
        from História 3.1 in normalized form.
        
        Returns:
            PriorityWeightsDTO with default values
        """
        return PriorityWeightsDTO.get_defaults()


class DatabasePrioritySettingsRepository(PrioritySettingsRepository):
    """
    SQLite implementation of PrioritySettingsRepository.
    
    Uses SQLite database with foreign key constraints and triggers
    for maintaining data integrity and audit fields.
    """
    
    def __init__(self, connection: Optional[sqlite3.Connection] = None):
        """
        Initialize repository with database connection.
        
        Args:
            connection: Optional SQLite connection (for testing).
                       If None, uses default connection from connection pool.
        """
        self.connection = connection
        self._ensure_table_exists()
    
    def _get_connection(self):
        """Get database connection (test or production)"""
        if self.connection:
            return self.connection
        return get_connection_context()
    
    def _ensure_table_exists(self):
        """Ensure priority settings table exists (for testing)"""
        if self.connection:
            # Only create table if using test connection
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS framework_priority_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    valor_weight REAL DEFAULT 0.4167,
                    risco_weight REAL DEFAULT 0.25,
                    esforco_weight REAL DEFAULT 0.1667,
                    alinhamento_weight REAL DEFAULT 0.1667,
                    confidence_weight REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE,
                    UNIQUE(project_id),
                    CHECK (ABS((valor_weight + risco_weight + esforco_weight + alinhamento_weight + confidence_weight) - 1.0) <= 0.0001),
                    CHECK (valor_weight >= 0 AND risco_weight >= 0 AND esforco_weight >= 0 AND alinhamento_weight >= 0 AND confidence_weight >= 0)
                )
            """)
            self.connection.commit()
    
    def get_by_project_id(self, project_id: int) -> Optional[PriorityWeightsDTO]:
        """
        Get priority weights for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            PriorityWeightsDTO if found, None otherwise
        """
        try:
            if self.connection:
                # Test mode - use provided connection
                cursor = self.connection.cursor()
                cursor.execute("""
                    SELECT id, project_id, valor_weight, risco_weight, 
                           esforco_weight, alinhamento_weight, confidence_weight,
                           created_at, updated_at
                    FROM framework_priority_settings
                    WHERE project_id = ?
                """, (project_id,))
                row = cursor.fetchone()
            else:
                # Production mode - use connection pool
                with get_connection_context() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, project_id, valor_weight, risco_weight, 
                               esforco_weight, alinhamento_weight, confidence_weight,
                               created_at, updated_at
                        FROM framework_priority_settings
                        WHERE project_id = ?
                    """, (project_id,))
                    row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert row to dictionary
            if hasattr(row, 'keys'):
                # sqlite3.Row object
                data = dict(row)
            else:
                # Tuple (test mode)
                data = {
                    'id': row[0],
                    'project_id': row[1],
                    'valor_weight': row[2],
                    'risco_weight': row[3],
                    'esforco_weight': row[4],
                    'alinhamento_weight': row[5],
                    'confidence_weight': row[6],
                    'created_at': row[7],
                    'updated_at': row[8]
                }
            
            return PriorityWeightsDTO.from_dict(data)
            
        except Exception as e:
            logger.error(f"Error getting priority weights for project {project_id}: {e}")
            return None
    
    def save(self, weights: PriorityWeightsDTO) -> PriorityWeightsDTO:
        """
        Save or update priority weights for a project.
        
        Implements UPSERT logic using INSERT OR REPLACE.
        
        Args:
            weights: Priority weights configuration to save
            
        Returns:
            Saved PriorityWeightsDTO with ID and timestamps
            
        Raises:
            ValueError: If weights don't sum to ~1.0 or validation fails
        """
        # Validate weights sum to ~1.0
        total = (weights.valor_weight + weights.risco_weight + 
                weights.esforco_weight + weights.alinhamento_weight + 
                weights.confidence_weight)
        
        if abs(total - 1.0) > 0.0001:
            raise ValueError(
                f"Priority weights must sum to 1.0 (±0.0001). "
                f"Current sum: {total:.4f}"
            )
        
        try:
            if self.connection:
                # Test mode - use provided connection
                cursor = self.connection.cursor()
                
                # Check if record exists
                cursor.execute("""
                    SELECT id FROM framework_priority_settings 
                    WHERE project_id = ?
                """, (weights.project_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    cursor.execute("""
                        UPDATE framework_priority_settings
                        SET valor_weight = ?, risco_weight = ?, 
                            esforco_weight = ?, alinhamento_weight = ?,
                            confidence_weight = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE project_id = ?
                    """, (weights.valor_weight, weights.risco_weight,
                         weights.esforco_weight, weights.alinhamento_weight,
                         weights.confidence_weight, weights.project_id))
                    
                    weights.id = existing[0]
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO framework_priority_settings
                        (project_id, valor_weight, risco_weight, esforco_weight,
                         alinhamento_weight, confidence_weight)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (weights.project_id, weights.valor_weight, weights.risco_weight,
                         weights.esforco_weight, weights.alinhamento_weight,
                         weights.confidence_weight))
                    
                    weights.id = cursor.lastrowid
                
                self.connection.commit()
                
                # Fetch updated record to get timestamps
                return self.get_by_project_id(weights.project_id)
                
            else:
                # Production mode - use connection pool
                with get_connection_context() as conn:
                    cursor = conn.cursor()
                    
                    # Check if record exists
                    cursor.execute("""
                        SELECT id FROM framework_priority_settings 
                        WHERE project_id = ?
                    """, (weights.project_id,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing record
                        cursor.execute("""
                            UPDATE framework_priority_settings
                            SET valor_weight = ?, risco_weight = ?, 
                                esforco_weight = ?, alinhamento_weight = ?,
                                confidence_weight = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE project_id = ?
                        """, (weights.valor_weight, weights.risco_weight,
                             weights.esforco_weight, weights.alinhamento_weight,
                             weights.confidence_weight, weights.project_id))
                        
                        weights.id = existing[0]
                    else:
                        # Insert new record
                        cursor.execute("""
                            INSERT INTO framework_priority_settings
                            (project_id, valor_weight, risco_weight, esforco_weight,
                             alinhamento_weight, confidence_weight)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (weights.project_id, weights.valor_weight, weights.risco_weight,
                             weights.esforco_weight, weights.alinhamento_weight,
                             weights.confidence_weight))
                        
                        weights.id = cursor.lastrowid
                    
                    conn.commit()
                    
                    # Fetch updated record to get timestamps
                    cursor.execute("""
                        SELECT id, project_id, valor_weight, risco_weight, 
                               esforco_weight, alinhamento_weight, confidence_weight,
                               created_at, updated_at
                        FROM framework_priority_settings
                        WHERE project_id = ?
                    """, (weights.project_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        data = dict(row) if hasattr(row, 'keys') else {
                            'id': row[0],
                            'project_id': row[1],
                            'valor_weight': row[2],
                            'risco_weight': row[3],
                            'esforco_weight': row[4],
                            'alinhamento_weight': row[5],
                            'confidence_weight': row[6],
                            'created_at': row[7],
                            'updated_at': row[8]
                        }
                        return PriorityWeightsDTO.from_dict(data)
                    
                    return weights
                    
        except sqlite3.IntegrityError as e:
            if "CHECK constraint failed" in str(e):
                raise ValueError(
                    f"Priority weights validation failed. Ensure weights sum to 1.0 "
                    f"and all values are non-negative."
                )
            raise
        except Exception as e:
            logger.error(f"Error saving priority weights: {e}")
            raise


class InMemoryPrioritySettingsRepository(PrioritySettingsRepository):
    """
    In-memory implementation for testing and development.
    
    Stores priority weights in memory without persistence.
    Useful for unit tests and local development.
    """
    
    def __init__(self):
        """Initialize empty in-memory storage"""
        self._storage = {}
        self._next_id = 1
    
    def get_by_project_id(self, project_id: int) -> Optional[PriorityWeightsDTO]:
        """Get priority weights from memory storage"""
        return self._storage.get(project_id)
    
    def save(self, weights: PriorityWeightsDTO) -> PriorityWeightsDTO:
        """Save priority weights to memory storage"""
        # Validate weights sum
        total = (weights.valor_weight + weights.risco_weight + 
                weights.esforco_weight + weights.alinhamento_weight + 
                weights.confidence_weight)
        
        if abs(total - 1.0) > 0.0001:
            raise ValueError(
                f"Priority weights must sum to 1.0 (±0.0001). "
                f"Current sum: {total:.4f}"
            )
        
        # Assign ID if new
        if weights.id is None:
            weights.id = self._next_id
            self._next_id += 1
            weights.created_at = datetime.now()
        
        weights.updated_at = datetime.now()
        
        # Store by project_id
        self._storage[weights.project_id] = weights
        
        return weights