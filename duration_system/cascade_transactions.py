#!/usr/bin/env python3
"""
Simplified Cascade Transaction Manager
Safe cascade delete operations with proper SQL parameter binding.
SECURITY FIX: All SQL queries use parameter binding to prevent injection.
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager
import uuid

logger = logging.getLogger(__name__)


@dataclass
class CascadeOperation:
    """Represents a cascade delete operation."""
    operation_id: str
    parent_table: str
    parent_id: int
    dry_run: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    affected_tables: List[str] = None
    total_records_affected: int = 0
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.affected_tables is None:
            self.affected_tables = []


class CascadeTransactionManager:
    """Simplified cascade transaction manager with security focus."""

    def __init__(self, database_path: str):
        """Initialize cascade transaction manager."""
        self.database_path = database_path
        
        # Define safe table relationships (whitelist approach)
        self.safe_relationships = {
            'framework_clients': [
                {'table': 'framework_projects', 'foreign_key': 'client_id'},
                {'table': 'framework_epics', 'foreign_key': 'client_id'},
                {'table': 'framework_tasks', 'foreign_key': 'client_id'}
            ],
            'framework_projects': [
                {'table': 'framework_epics', 'foreign_key': 'project_id'},
                {'table': 'framework_tasks', 'foreign_key': 'project_id'}
            ],
            'framework_epics': [
                {'table': 'framework_tasks', 'foreign_key': 'epic_id'}
            ]
        }

    def get_cascade_impact(self, table: str, record_id: int) -> Dict[str, Any]:
        """Analyze cascade delete impact using safe SQL."""
        if table not in self.safe_relationships:
            return {'error': 'Table not supported for cascade operations'}
        
        impact = {
            'tables_affected': [],
            'estimated_records': 0,
            'warnings': []
        }

        try:
            with sqlite3.connect(self.database_path) as conn:
                # SECURITY FIX: Use parameter binding for all queries
                relationships = self.safe_relationships[table]
                
                for relationship in relationships:
                    child_table = relationship['table']
                    foreign_key = relationship['foreign_key']
                    
                    # Use parameter binding to prevent SQL injection
                    query = f"SELECT COUNT(*) FROM {child_table} WHERE {foreign_key} = ?"
                    cursor = conn.execute(query, (record_id,))
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        impact['tables_affected'].append(child_table)
                        impact['estimated_records'] += count
                
                # Add warnings based on impact
                if impact['estimated_records'] > 100:
                    impact['warnings'].append("Large number of records to delete")
                
                if len(impact['tables_affected']) > 3:
                    impact['warnings'].append("Many tables affected")

        except Exception as e:
            logger.error(f"Error analyzing cascade impact: {e}")
            impact['error'] = str(e)

        return impact

    @contextmanager
    def cascade_transaction(self, operation: CascadeOperation):
        """Context manager for cascade operations."""
        operation.started_at = datetime.now()
        connection = None
        
        try:
            connection = sqlite3.connect(self.database_path, timeout=30)
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("BEGIN IMMEDIATE")
            
            logger.info(f"Started cascade operation {operation.operation_id}")
            yield connection
            
            connection.commit()
            operation.completed_at = datetime.now()
            logger.info(f"Cascade operation {operation.operation_id} completed")
            
        except Exception as e:
            logger.error(f"Error in cascade operation {operation.operation_id}: {e}")
            operation.error_message = str(e)
            if connection:
                try:
                    connection.rollback()
                except:
                    pass
            raise
        finally:
            if connection:
                try:
                    connection.close()
                except:
                    pass

    def cascade_delete(self, table: str, record_id: int, dry_run: bool = False) -> CascadeOperation:
        """Perform cascade delete with proper SQL security."""
        if table not in self.safe_relationships:
            raise ValueError(f"Table {table} not supported for cascade operations")
        
        operation = CascadeOperation(
            operation_id=str(uuid.uuid4())[:8],
            parent_table=table,
            parent_id=record_id,
            dry_run=dry_run
        )

        if dry_run:
            # Just analyze impact without deleting
            impact = self.get_cascade_impact(table, record_id)
            operation.affected_tables = impact.get('tables_affected', [])
            operation.total_records_affected = impact.get('estimated_records', 0)
            operation.completed_at = datetime.now()
            return operation

        # Perform actual deletion
        try:
            with self.cascade_transaction(operation) as conn:
                self._perform_cascade_delete(conn, operation)
        except Exception as e:
            operation.error_message = str(e)
            raise

        return operation

    def _perform_cascade_delete(self, conn: sqlite3.Connection, operation: CascadeOperation):
        """Perform the actual cascade delete with safe SQL."""
        deleted_count = 0
        table = operation.parent_table
        record_id = operation.parent_id
        
        # Delete in reverse dependency order (children first)
        relationships = self.safe_relationships.get(table, [])
        
        # Reverse order for proper cascade
        for relationship in reversed(relationships):
            child_table = relationship['table']
            foreign_key = relationship['foreign_key']
            
            # SECURITY FIX: Use parameter binding
            delete_query = f"DELETE FROM {child_table} WHERE {foreign_key} = ?"
            cursor = conn.execute(delete_query, (record_id,))
            
            if cursor.rowcount > 0:
                deleted_count += cursor.rowcount
                operation.affected_tables.append(child_table)
                logger.debug(f"Deleted {cursor.rowcount} records from {child_table}")

        # Finally delete the parent record
        # SECURITY FIX: Use parameter binding
        parent_delete_query = f"DELETE FROM {table} WHERE id = ?"
        cursor = conn.execute(parent_delete_query, (record_id,))
        
        if cursor.rowcount > 0:
            deleted_count += cursor.rowcount
            operation.affected_tables.append(table)

        operation.total_records_affected = deleted_count


def safe_cascade_delete(table: str, record_id: int, database_path: str = "framework.db") -> Dict[str, Any]:
    """Safe cascade delete with comprehensive error handling."""
    try:
        manager = CascadeTransactionManager(database_path)
        operation = manager.cascade_delete(table, record_id)
        
        return {
            'success': True,
            'operation_id': operation.operation_id,
            'affected_tables': operation.affected_tables,
            'records_deleted': operation.total_records_affected,
            'duration_ms': (
                (operation.completed_at - operation.started_at).total_seconds() * 1000
                if operation.completed_at and operation.started_at else 0
            )
        }
        
    except Exception as e:
        logger.error(f"Cascade delete failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def analyze_cascade_impact(table: str, record_id: int, database_path: str = "framework.db") -> Dict[str, Any]:
    """Analyze cascade delete impact safely."""
    try:
        manager = CascadeTransactionManager(database_path)
        return manager.get_cascade_impact(table, record_id)
    except Exception as e:
        logger.error(f"Impact analysis failed: {e}")
        return {'error': str(e)}


def render_cascade_dashboard():
    """Simple Streamlit dashboard for cascade operations."""
    import streamlit as st

    st.title("🗑️ Safe Cascade Delete")

    # Risk analysis
    st.subheader("🔍 Impact Analysis")
    
    table = st.selectbox("Table", ["framework_clients", "framework_projects", "framework_epics"])
    record_id = st.number_input("Record ID", min_value=1, value=1)

    if st.button("Analyze Impact"):
        impact = analyze_cascade_impact(table, record_id)
        
