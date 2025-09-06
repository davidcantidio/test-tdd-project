"""
🧪 TDD Tests for PrioritySettingsRepository - História 3.2
Tests for project-specific priority weight configuration persistence.

Following TDD Red-Green-Refactor methodology.
"""

import unittest
from typing import Optional
from datetime import datetime
import sqlite3
import tempfile
import os

# These imports will fail initially (RED phase)
from streamlit_extension.core.dto.priority_weights_dto import PriorityWeightsDTO
from streamlit_extension.services.priority_settings_repository import (
    PrioritySettingsRepository,
    DatabasePrioritySettingsRepository
)


class TestPrioritySettingsRepository(unittest.TestCase):
    """Test suite for PrioritySettingsRepository implementation"""
    
    def setUp(self):
        """Set up test database and repository"""
        # Create temporary database for testing
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Create necessary tables for testing
        self._create_test_schema()
        
        # Initialize repository with test database
        self.repository = DatabasePrioritySettingsRepository(self.conn)
        
    def tearDown(self):
        """Clean up test database"""
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def _create_test_schema(self):
        """Create minimal schema for testing"""
        cursor = self.conn.cursor()
        
        # Enable foreign key constraints in SQLite
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create projects table (minimal version for FK constraint)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS framework_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_key VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL
            )
        """)
        
        # Create priority settings table (from migration 011)
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
        
        # Create trigger for updated_at
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_priority_settings_updated
            AFTER UPDATE ON framework_priority_settings
            FOR EACH ROW
            BEGIN
                UPDATE framework_priority_settings
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = OLD.id;
            END
        """)
        
        # Insert test project
        cursor.execute("""
            INSERT INTO framework_projects (id, project_key, name)
            VALUES (1, 'TEST_PROJ', 'Test Project')
        """)
        
        self.conn.commit()
    
    # ========== Test Cases (8 total) ==========
    
    def test_get_by_project_id_returns_none_when_not_exists(self):
        """Should return None when no configuration exists for project"""
        # Given: A project ID with no priority settings
        project_id = 999
        
        # When: Getting priority settings for non-existent project
        result = self.repository.get_by_project_id(project_id)
        
        # Then: Should return None
        self.assertIsNone(result)
    
    def test_get_by_project_id_returns_saved_weights(self):
        """Should return saved weights for project"""
        # Given: A saved priority configuration
        weights = PriorityWeightsDTO(
            project_id=1,
            valor_weight=0.3,
            risco_weight=0.3,
            esforco_weight=0.2,
            alinhamento_weight=0.2,
            confidence_weight=0.0
        )
        saved = self.repository.save(weights)
        
        # When: Getting by project ID
        result = self.repository.get_by_project_id(1)
        
        # Then: Should return the saved weights
        self.assertIsNotNone(result)
        self.assertEqual(result.project_id, 1)
        self.assertAlmostEqual(result.valor_weight, 0.3, places=4)
        self.assertAlmostEqual(result.risco_weight, 0.3, places=4)
        self.assertAlmostEqual(result.esforco_weight, 0.2, places=4)
        self.assertAlmostEqual(result.alinhamento_weight, 0.2, places=4)
        self.assertAlmostEqual(result.confidence_weight, 0.0, places=4)
    
    def test_save_creates_new_priority_weights(self):
        """Should create new priority weights configuration"""
        # Given: A new priority weights configuration
        weights = PriorityWeightsDTO(
            project_id=1,
            valor_weight=0.5,
            risco_weight=0.2,
            esforco_weight=0.2,
            alinhamento_weight=0.1,
            confidence_weight=0.0
        )
        
        # When: Saving new weights
        result = self.repository.save(weights)
        
        # Then: Should create and return with ID
        self.assertIsNotNone(result.id)
        self.assertEqual(result.project_id, 1)
        self.assertAlmostEqual(result.valor_weight, 0.5, places=4)
        self.assertIsNotNone(result.created_at)
        self.assertIsNotNone(result.updated_at)
    
    def test_save_updates_existing_priority_weights(self):
        """Should update existing configuration via UPSERT"""
        # Given: An existing configuration
        initial = PriorityWeightsDTO(
            project_id=1,
            valor_weight=0.4167,
            risco_weight=0.25,
            esforco_weight=0.1667,
            alinhamento_weight=0.1667,
            confidence_weight=0.0
        )
        saved = self.repository.save(initial)
        initial_id = saved.id
        
        # When: Saving updated weights for same project
        updated = PriorityWeightsDTO(
            project_id=1,
            valor_weight=0.6,
            risco_weight=0.1,
            esforco_weight=0.2,
            alinhamento_weight=0.1,
            confidence_weight=0.0
        )
        result = self.repository.save(updated)
        
        # Then: Should update existing record (UPSERT)
        self.assertEqual(result.id, initial_id)  # Same ID (updated, not created)
        self.assertAlmostEqual(result.valor_weight, 0.6, places=4)
        self.assertAlmostEqual(result.risco_weight, 0.1, places=4)
        
        # Verify only one record exists for the project
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM framework_priority_settings WHERE project_id = ?", (1,))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
    
    def test_get_default_weights_returns_standard_values(self):
        """Should return default weights (~0.4167, 0.25, 0.1667, 0.1667, 0.0)"""
        # When: Getting default weights
        defaults = PrioritySettingsRepository.get_default_weights()
        
        # Then: Should return correct default proportions (5:3:2:2)
        self.assertAlmostEqual(defaults.valor_weight, 0.4167, places=3)
        self.assertAlmostEqual(defaults.risco_weight, 0.25, places=3)
        self.assertAlmostEqual(defaults.esforco_weight, 0.1667, places=3)
        self.assertAlmostEqual(defaults.alinhamento_weight, 0.1667, places=3)
        self.assertAlmostEqual(defaults.confidence_weight, 0.0, places=3)
        
        # Verify sum is ~1.0
        total = (defaults.valor_weight + defaults.risco_weight + 
                defaults.esforco_weight + defaults.alinhamento_weight + 
                defaults.confidence_weight)
        self.assertAlmostEqual(total, 1.0, places=3)
    
    def test_weights_sum_validation(self):
        """Should reject weights that don't sum to 1.0 (tolerance 1e-4)"""
        # Given: Weights that don't sum to 1.0
        # Create DTO bypassing __post_init__ validation for testing
        invalid_weights = PriorityWeightsDTO.__new__(PriorityWeightsDTO)
        invalid_weights.id = None
        invalid_weights.project_id = 1
        invalid_weights.valor_weight = 0.5
        invalid_weights.risco_weight = 0.5
        invalid_weights.esforco_weight = 0.3  # Sum = 1.3 (invalid)
        invalid_weights.alinhamento_weight = 0.0
        invalid_weights.confidence_weight = 0.0
        invalid_weights.created_at = None
        invalid_weights.updated_at = None
        
        # When/Then: Should raise validation error
        with self.assertRaises(ValueError) as context:
            self.repository.save(invalid_weights)
        
        self.assertIn("sum to 1.0", str(context.exception).lower())
    
    def test_updated_at_changes_on_update(self):
        """Should update updated_at via trigger on changes"""
        # Given: An existing configuration
        weights = PriorityWeightsDTO(
            project_id=1,
            valor_weight=0.4167,
            risco_weight=0.25,
            esforco_weight=0.1667,
            alinhamento_weight=0.1667,
            confidence_weight=0.0
        )
        saved = self.repository.save(weights)
        initial_updated_at = saved.updated_at
        
        # Ensure timestamp will be different
        import time
        time.sleep(1.1)  # SQLite datetime has second precision
        
        # When: Updating the weights
        updated = PriorityWeightsDTO(
            project_id=1,
            valor_weight=0.5,
            risco_weight=0.2,
            esforco_weight=0.2,
            alinhamento_weight=0.1,
            confidence_weight=0.0
        )
        result = self.repository.save(updated)
        
        # Then: updated_at should be different
        self.assertIsNotNone(result.updated_at)
        self.assertIsNotNone(initial_updated_at)
        # Compare as strings since SQLite returns datetime strings
        self.assertNotEqual(str(initial_updated_at), str(result.updated_at))
    
    def test_cascade_delete_when_project_removed(self):
        """Should remove weights when project is deleted"""
        # Given: A project with priority settings
        weights = PriorityWeightsDTO(
            project_id=1,
            valor_weight=0.4167,
            risco_weight=0.25,
            esforco_weight=0.1667,
            alinhamento_weight=0.1667,
            confidence_weight=0.0
        )
        self.repository.save(weights)
        
        # When: Deleting the project
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM framework_projects WHERE id = ?", (1,))
        self.conn.commit()
        
        # Then: Priority settings should be deleted (CASCADE)
        result = self.repository.get_by_project_id(1)
        self.assertIsNone(result)
        
        # Verify record was actually deleted
        cursor.execute("SELECT COUNT(*) FROM framework_priority_settings WHERE project_id = ?", (1,))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)


if __name__ == '__main__':
    unittest.main()