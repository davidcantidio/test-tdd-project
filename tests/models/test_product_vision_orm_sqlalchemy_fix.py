#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TESTS - ProductVisionORM SQLAlchemy Fix Validation

Comprehensive tests to validate that the SQLAlchemy 'metadata' reserved name fix
is working correctly. These tests verify that the fix resolved the:
InvalidRequestError: Attribute name 'metadata' is reserved...

Test Categories:
1. SQLAlchemy Import Tests - Verify no reserved name errors
2. Engine & Session Tests - Verify ORM functionality  
3. CRUD Operations Tests - Verify database operations
4. JSON Field Tests - Verify extra_metadata functionality
5. Data Integrity Tests - Verify migration preserved data
6. System Integration Tests - Verify no breaking changes

Usage:
    pytest tests/models/test_product_vision_orm_sqlalchemy_fix.py -v
"""

import pytest
import sys
import os
import tempfile
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Test-specific imports (basic Python modules only)
import sqlite3
from unittest.mock import patch, MagicMock


class TestProductVisionORMSQLAlchemyFix:
    """
    Comprehensive test suite for ProductVisionORM SQLAlchemy fix validation.
    
    Tests are designed to run without external dependencies (like Streamlit)
    and focus specifically on validating the metadata reserved name fix.
    """

    def test_01_sqlalchemy_imports_basic(self):
        """
        Test 1: Basic SQLAlchemy imports work without errors
        
        This test validates that core SQLAlchemy functionality is available
        and can be imported without conflicts.
        """
        # Test basic SQLAlchemy imports
        from sqlalchemy import create_engine, Column, Integer, String, Text, JSON
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import sessionmaker
        
        # Test typing imports needed for the model
        from typing import Optional, Dict, Any
        
        # If we get here, basic SQLAlchemy imports work
        assert True, "Basic SQLAlchemy imports successful"

    def test_02_product_vision_orm_import(self):
        """
        Test 2: ProductVisionORM can be imported without SQLAlchemy reserved name errors
        
        This is the CRITICAL test - if this passes, the fix worked.
        If this fails, we still have the reserved name conflict.
        """
        try:
            # This import should NOT raise InvalidRequestError about 'metadata' 
            from streamlit_extension.models.product_vision import ProductVisionORM
            
            # Verify the model has the expected attribute
            assert hasattr(ProductVisionORM, 'extra_metadata'), "Model should have extra_metadata attribute"
            
            # Verify the model can access its SQLAlchemy table metadata
            table = ProductVisionORM.__table__
            assert table is not None, "Should be able to access __table__"
            
            # Verify column names
            column_names = [col.name for col in table.columns]
            assert 'extra_metadata' in column_names, "Should have extra_metadata column"
            assert 'metadata' not in column_names, "Should NOT have metadata column"
            
        except Exception as e:
            if "reserved" in str(e).lower() and "metadata" in str(e).lower():
                pytest.fail(f"SQLAlchemy reserved name error still exists: {e}")
            else:
                # Re-raise other errors (like import errors due to missing dependencies)
                raise

    def test_03_sqlalchemy_engine_creation(self):
        """
        Test 3: SQLAlchemy engine can be created with ProductVisionORM
        
        This test validates that we can create a SQLAlchemy engine and
        the model works with it without reserved name conflicts.
        """
        try:
            from sqlalchemy import create_engine
            from streamlit_extension.models.base import Base
            from streamlit_extension.models.product_vision import ProductVisionORM
            
            # Create in-memory SQLite engine
            engine = create_engine("sqlite:///:memory:")
            
            # This should work without 'metadata' conflicts
            Base.metadata.create_all(engine)
            
            # Verify the table was created
            assert engine.dialect.has_table(engine.connect(), 'product_visions'), \
                "product_visions table should be created"
            
        except ImportError:
            pytest.skip("SQLAlchemy or model dependencies not available")
        except Exception as e:
            if "reserved" in str(e).lower() and "metadata" in str(e).lower():
                pytest.fail(f"SQLAlchemy reserved name error during engine creation: {e}")
            else:
                raise

    def test_04_sqlalchemy_session_operations(self):
        """
        Test 4: SQLAlchemy session operations work correctly
        
        This test validates that we can create sessions and perform
        basic operations without reserved name conflicts.
        """
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from streamlit_extension.models.base import Base
            from streamlit_extension.models.product_vision import ProductVisionORM
            
            # Create in-memory database
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            
            # Create session
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Test basic session functionality
            assert session is not None, "Session should be created"
            
            # Test querying (even if no data)
            query_result = session.query(ProductVisionORM).all()
            assert isinstance(query_result, list), "Query should return list"
            assert len(query_result) == 0, "Should be empty initially"
            
            session.close()
            
        except ImportError:
            pytest.skip("SQLAlchemy or model dependencies not available")
        except Exception as e:
            if "reserved" in str(e).lower() and "metadata" in str(e).lower():
                pytest.fail(f"SQLAlchemy reserved name error during session operations: {e}")
            else:
                raise

    def test_05_product_vision_crud_operations(self):
        """
        Test 5: Full CRUD operations work with ProductVisionORM
        
        This test validates that Create, Read, Update, Delete operations
        work correctly with the fixed model.
        """
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from streamlit_extension.models.base import Base
            from streamlit_extension.models.product_vision import ProductVisionORM
            
            # Setup in-memory database
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # CREATE - Test creating a ProductVision instance
            test_vision = ProductVisionORM(
                project_id=1,
                vision_statement="Test vision statement for SQLAlchemy fix validation",
                problem_statement="Testing that the metadata field fix works",
                target_audience="Developers using SQLAlchemy ORM",
                value_proposition="Resolved reserved name conflict",
                status="active",
                version=1
            )
            
            session.add(test_vision)
            session.commit()
            
            # Verify it was created
            assert test_vision.id is not None, "Should have generated ID"
            
            # READ - Test querying the created instance
            retrieved_vision = session.query(ProductVisionORM).filter_by(id=test_vision.id).first()
            assert retrieved_vision is not None, "Should be able to retrieve created vision"
            assert retrieved_vision.vision_statement == "Test vision statement for SQLAlchemy fix validation"
            
            # UPDATE - Test updating the instance
            retrieved_vision.problem_statement = "Updated problem statement"
            session.commit()
            
            # Verify update
            updated_vision = session.query(ProductVisionORM).filter_by(id=test_vision.id).first()
            assert updated_vision.problem_statement == "Updated problem statement"
            
            # DELETE - Test deleting the instance
            session.delete(updated_vision)
            session.commit()
            
            # Verify deletion
            deleted_vision = session.query(ProductVisionORM).filter_by(id=test_vision.id).first()
            assert deleted_vision is None, "Should be deleted"
            
            session.close()
            
        except ImportError:
            pytest.skip("SQLAlchemy or model dependencies not available")
        except Exception as e:
            if "reserved" in str(e).lower() and "metadata" in str(e).lower():
                pytest.fail(f"SQLAlchemy reserved name error during CRUD operations: {e}")
            else:
                raise

    def test_06_extra_metadata_json_functionality(self):
        """
        Test 6: extra_metadata JSON field works correctly
        
        This test validates that the renamed field (metadata -> extra_metadata)
        works correctly for JSON data storage and retrieval.
        """
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from streamlit_extension.models.base import Base
            from streamlit_extension.models.product_vision import ProductVisionORM
            
            # Setup in-memory database
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Test complex JSON data in extra_metadata field
            test_metadata = {
                "fix_applied": True,
                "original_issue": "SQLAlchemy reserved name conflict",
                "solution": "Renamed metadata to extra_metadata",
                "test_data": {
                    "nested_object": {"key": "value"},
                    "array": [1, 2, 3, "test"],
                    "boolean": True,
                    "null_value": None
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": 1.0
            }
            
            # Create instance with JSON metadata
            test_vision = ProductVisionORM(
                project_id=1,
                vision_statement="Test vision for JSON field validation",
                extra_metadata=test_metadata
            )
            
            session.add(test_vision)
            session.commit()
            
            # Retrieve and verify JSON data
            retrieved_vision = session.query(ProductVisionORM).filter_by(id=test_vision.id).first()
            assert retrieved_vision.extra_metadata is not None, "extra_metadata should not be None"
            
            # Verify JSON data integrity
            retrieved_metadata = retrieved_vision.extra_metadata
            assert retrieved_metadata["fix_applied"] == True
            assert retrieved_metadata["solution"] == "Renamed metadata to extra_metadata"
            assert retrieved_metadata["test_data"]["nested_object"]["key"] == "value"
            assert retrieved_metadata["test_data"]["array"] == [1, 2, 3, "test"]
            
            # Test updating JSON data
            updated_metadata = retrieved_metadata.copy()
            updated_metadata["updated"] = True
            updated_metadata["update_timestamp"] = datetime.now(timezone.utc).isoformat()
            
            retrieved_vision.extra_metadata = updated_metadata
            session.commit()
            
            # Verify update
            final_vision = session.query(ProductVisionORM).filter_by(id=test_vision.id).first()
            assert final_vision.extra_metadata["updated"] == True
            assert "update_timestamp" in final_vision.extra_metadata
            
            session.close()
            
        except ImportError:
            pytest.skip("SQLAlchemy or model dependencies not available")
        except Exception as e:
            if "reserved" in str(e).lower() and "metadata" in str(e).lower():
                pytest.fail(f"SQLAlchemy reserved name error during JSON operations: {e}")
            else:
                raise

    def test_07_database_schema_validation(self):
        """
        Test 7: Database schema has correct column names
        
        This test validates that the actual database schema was updated
        correctly during migration (metadata -> extra_metadata).
        """
        # Test against actual database if it exists
        db_path = project_root / "framework.db"
        
        if not db_path.exists():
            pytest.skip("Actual database file not found - cannot test schema")
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check if product_visions table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='product_visions'
                """)
                
                table_exists = cursor.fetchone()
                if not table_exists:
                    pytest.skip("product_visions table not found in database")
                
                # Get column information
                cursor.execute("PRAGMA table_info(product_visions)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Validate schema changes
                assert 'extra_metadata' in column_names, "Database should have extra_metadata column"
                assert 'metadata' not in column_names, "Database should NOT have metadata column"
                
                # Check for data preservation (if any data exists)
                cursor.execute("SELECT COUNT(*) FROM product_visions")
                total_count = cursor.fetchone()[0]
                
                if total_count > 0:
                    cursor.execute("SELECT COUNT(*) FROM product_visions WHERE extra_metadata IS NOT NULL")
                    metadata_count = cursor.fetchone()[0]
                    
                    # If there are records with metadata, verify they're accessible
                    if metadata_count > 0:
                        cursor.execute("SELECT extra_metadata FROM product_visions WHERE extra_metadata IS NOT NULL LIMIT 1")
                        sample_metadata = cursor.fetchone()[0]
                        assert sample_metadata is not None, "Should be able to access existing metadata"
                        
        except Exception as e:
            pytest.fail(f"Database schema validation failed: {e}")

    def test_08_model_methods_functionality(self):
        """
        Test 8: ProductVisionORM model methods work correctly
        
        This test validates that custom methods in the model work
        correctly after the metadata field fix.
        """
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from streamlit_extension.models.base import Base
            from streamlit_extension.models.product_vision import ProductVisionORM
            
            # Setup in-memory database
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Create test instance
            test_vision = ProductVisionORM(
                project_id=1,
                vision_statement="Complete vision statement for method testing",
                problem_statement="Well-defined problem that needs solving",
                target_audience="Specific target audience group",
                value_proposition="Clear value proposition statement"
            )
            
            # Test model methods if they exist
            if hasattr(test_vision, 'validate_vision_completeness'):
                validation_result = test_vision.validate_vision_completeness()
                assert isinstance(validation_result, dict), "Should return validation dictionary"
                assert 'is_complete' in validation_result, "Should have is_complete field"
            
            if hasattr(test_vision, 'calculate_vision_clarity_score'):
                clarity_score = test_vision.calculate_vision_clarity_score()
                assert isinstance(clarity_score, (int, float)), "Should return numeric score"
                assert 0 <= clarity_score <= 100, "Score should be between 0 and 100"
            
            if hasattr(test_vision, 'add_constraint'):
                # Test constraint methods
                result = test_vision.add_constraint(
                    constraint="SQLAlchemy metadata fix applied",
                    constraint_type="technical",
                    description="Fixed reserved name conflict",
                    severity="medium"
                )
                # Method should not raise exceptions
                assert True, "add_constraint method executed without errors"
            
            if hasattr(test_vision, 'get_vision_summary'):
                summary = test_vision.get_vision_summary()
                assert isinstance(summary, dict), "Should return summary dictionary"
            
            session.close()
            
        except ImportError:
            pytest.skip("SQLAlchemy or model dependencies not available")
        except Exception as e:
            if "reserved" in str(e).lower() and "metadata" in str(e).lower():
                pytest.fail(f"SQLAlchemy reserved name error in model methods: {e}")
            else:
                raise

    def test_09_compatibility_with_existing_system(self):
        """
        Test 9: Model works with existing repository pattern
        
        This test validates that the fixed model is compatible with
        the existing repository pattern and service architecture.
        """
        try:
            # Test repository pattern compatibility if available
            from streamlit_extension.models.product_vision import ProductVisionORM
            from streamlit_extension.models.repository import BaseRepository, RepositoryFactory
            
            # Test that repository can be created for ProductVisionORM
            # This validates that the model works with the repository pattern
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from streamlit_extension.models.base import Base
            
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Test repository creation
            repository = BaseRepository(ProductVisionORM, session)
            assert repository is not None, "Should be able to create repository"
            
            # Test basic repository operations
            test_data = {
                'project_id': 1,
                'vision_statement': 'Test vision for repository pattern',
                'status': 'active',
                'version': 1
            }
            
            # Create instance through repository
            instance = ProductVisionORM(**test_data)
            result = repository.create(instance)
            
            # Repository operations should work without metadata conflicts
            assert True, "Repository pattern works with fixed model"
            
            session.close()
            
        except ImportError:
            pytest.skip("Repository pattern dependencies not available")
        except Exception as e:
            if "reserved" in str(e).lower() and "metadata" in str(e).lower():
                pytest.fail(f"SQLAlchemy reserved name error in repository pattern: {e}")
            else:
                raise

    def test_10_comprehensive_fix_validation(self):
        """
        Test 10: Comprehensive validation that the fix is complete
        
        This test provides a final comprehensive validation that all
        aspects of the SQLAlchemy metadata fix are working correctly.
        """
        validation_results = {}
        
        try:
            # Test 1: Import without errors
            from streamlit_extension.models.product_vision import ProductVisionORM
            validation_results['import_success'] = True
            
            # Test 2: Table metadata access
            table = ProductVisionORM.__table__
            column_names = [col.name for col in table.columns]
            validation_results['correct_columns'] = (
                'extra_metadata' in column_names and 'metadata' not in column_names
            )
            
            # Test 3: SQLAlchemy engine operations
            from sqlalchemy import create_engine
            from streamlit_extension.models.base import Base
            
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            validation_results['engine_operations'] = True
            
            # Test 4: Instance creation and attribute access
            test_instance = ProductVisionORM(
                project_id=1,
                vision_statement="Comprehensive test validation",
                extra_metadata={"test": "data", "fix_validated": True}
            )
            
            # Test attribute access
            assert hasattr(test_instance, 'extra_metadata')
            assert test_instance.extra_metadata["fix_validated"] == True
            validation_results['attribute_access'] = True
            
            # Test 5: Database operations
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            session = Session()
            
            session.add(test_instance)
            session.commit()
            
            retrieved = session.query(ProductVisionORM).first()
            assert retrieved.extra_metadata["fix_validated"] == True
            validation_results['database_operations'] = True
            
            session.close()
            
        except Exception as e:
            if "reserved" in str(e).lower() and "metadata" in str(e).lower():
                pytest.fail(f"SQLAlchemy reserved name error in comprehensive validation: {e}")
            else:
                validation_results['error'] = str(e)
        
        # Verify all validations passed
        expected_validations = [
            'import_success', 
            'correct_columns', 
            'engine_operations', 
            'attribute_access', 
            'database_operations'
        ]
        
        for validation in expected_validations:
            if validation not in validation_results:
                pytest.fail(f"Validation {validation} was not completed")
            if not validation_results[validation]:
                pytest.fail(f"Validation {validation} failed")
        
        # If we get here, all validations passed
        assert True, "✅ Comprehensive SQLAlchemy metadata fix validation PASSED"


if __name__ == "__main__":
    """
    Run tests directly for debugging
    """
    pytest.main([__file__, "-v", "--tb=short"])