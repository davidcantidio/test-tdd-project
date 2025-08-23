#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TESTS - ORM Integration Tests

Comprehensive integration tests for SQLAlchemy ORM models, repository pattern,
and service layer integration with user corrections validation.

Features:
- ORM model creation and persistence validation
- Repository pattern functionality testing
- User corrections validation (constraints, JSON fields, etc.)
- Service layer integration verification
- Relationship mapping validation
- Transaction handling verification

Usage:
    pytest tests/models/test_orm_integration.py -v
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, Any

# SQLAlchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Test imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Model imports
from streamlit_extension.models.base import Base
from streamlit_extension.models.sprint import SprintORM, SprintStatus, SprintHealthStatus
from streamlit_extension.models.task_dependency import TaskDependencyORM, DependencyType, DependencyStrength, RiskLevel
from streamlit_extension.models.task_labels import TaskLabelORM, TaskLabelAssignmentORM, LabelVisibility, AssignmentContext
from streamlit_extension.models.sprint_milestone import SprintMilestoneORM, MilestoneType, MilestoneStatus, QualityStatus
from streamlit_extension.models.ai_generation import AiGenerationORM, ChangeLogORM, GenerationType, ContextType

# Repository imports
from streamlit_extension.models.repository import (
    BaseRepository, RepositoryFactory, RepositoryManager,
    RepositoryResult, RepositoryListResult
)


# =============================================================================
# Test Configuration
# =============================================================================

@pytest.fixture(scope="session")
def test_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create test session with automatic cleanup."""
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_sprint_data():
    """Sample sprint data for testing."""
    return {
        'project_id': 1,
        'sprint_key': 'TEST-2025-01',
        'sprint_name': 'Test Sprint',
        'sprint_goal': 'Complete authentication system testing',
        'start_date': date(2025, 8, 23),
        'end_date': date(2025, 9, 6),
        'story_points_committed': 25,
        'capacity_points': 30,
        'planned_velocity': 20
    }


@pytest.fixture
def sample_task_dependency_data():
    """Sample task dependency data for testing."""
    return {
        'task_id': 1,
        'depends_on_task_id': 2,
        'dependency_type': DependencyType.FINISH_TO_START.value,
        'dependency_strength': DependencyStrength.HARD.value,
        'dependency_reason': 'User authentication must complete before dashboard implementation',
        'lead_lag_days': 0,
        'risk_level': RiskLevel.MEDIUM.value
    }


# =============================================================================
# Sprint ORM Tests
# =============================================================================

class TestSprintORM:
    """Test SprintORM model with user corrections validation."""
    
    def test_sprint_creation(self, test_session, sample_sprint_data):
        """Test basic sprint creation and persistence."""
        sprint = SprintORM(**sample_sprint_data)
        test_session.add(sprint)
        test_session.commit()
        
        assert sprint.id is not None
        assert sprint.sprint_key == 'TEST-2025-01'
        assert sprint.status == SprintStatus.PLANNING.value
        assert sprint.health_status == SprintHealthStatus.GREEN.value
    
    def test_sprint_enum_properties(self, test_session, sample_sprint_data):
        """Test enum property access with user corrections fallback handling."""
        sprint = SprintORM(**sample_sprint_data)
        
        # Test normal enum conversion
        assert sprint.status_enum == SprintStatus.PLANNING
        assert sprint.health_status_enum == SprintHealthStatus.GREEN
        
        # Test fallback for invalid values (user correction)
        sprint.status = 'invalid_status'
        assert sprint.status_enum == SprintStatus.PLANNING  # Should fallback
        
        sprint.health_status = 'invalid_health'
        assert sprint.health_status_enum == SprintHealthStatus.GREEN  # Should fallback
    
    def test_sprint_lifecycle_methods(self, test_session, sample_sprint_data):
        """Test sprint lifecycle methods with validation."""
        sprint = SprintORM(**sample_sprint_data)
        test_session.add(sprint)
        test_session.commit()
        
        # Test sprint start
        assert sprint.can_be_started() is True
        result = sprint.start_sprint()
        assert result is True
        assert sprint.status_enum == SprintStatus.ACTIVE
        assert sprint.is_current is True
        assert sprint.started_at is not None
    
    def test_sprint_team_management(self, test_session, sample_sprint_data):
        """Test team management JSON field handling."""
        sprint = SprintORM(**sample_sprint_data)
        test_session.add(sprint)
        test_session.commit()
        
        # Test adding team members
        assert sprint.add_team_member(101) is True
        assert sprint.add_team_member(102) is True
        assert sprint.add_team_member(101) is False  # Duplicate should return False
        
        members = sprint.get_team_members_list()
        assert 101 in members
        assert 102 in members
        assert len(members) == 2
        
        # Test removing team member
        assert sprint.remove_team_member(101) is True
        assert sprint.remove_team_member(101) is False  # Already removed
        
        members_after = sprint.get_team_members_list()
        assert 101 not in members_after
        assert 102 in members_after
        assert len(members_after) == 1
    
    def test_sprint_risk_management(self, test_session, sample_sprint_data):
        """Test risk management JSON field operations."""
        sprint = SprintORM(**sample_sprint_data)
        test_session.add(sprint)
        test_session.commit()
        
        # Add risk factor
        sprint.add_risk_factor("Database migration delays", "high", "Team unavailable due to holidays")
        
        risks = sprint.get_risk_factors_list()
        assert len(risks) == 1
        assert risks[0]['description'] == "Database migration delays"
        assert risks[0]['severity'] == "high"
        assert risks[0]['status'] == "active"
    
    def test_sprint_portuguese_documentation_features(self, test_session, sample_sprint_data):
        """Test features documented in Portuguese (user corrections)."""
        sprint = SprintORM(**sample_sprint_data)
        test_session.add(sprint)
        test_session.commit()
        
        # Test TDAH recommendations (Portuguese documentation feature)
        recommendations = sprint.get_tdah_friendly_recommendations()
        assert isinstance(recommendations, list)
        
        # Test cognitive load calculation
        cognitive_load = sprint.calculate_cognitive_load_score()
        assert isinstance(cognitive_load, float)
        assert 1.0 <= cognitive_load <= 10.0
    
    def test_sprint_unique_constraints(self, test_session, sample_sprint_data):
        """Test unique constraint on project_id + sprint_key."""
        sprint1 = SprintORM(**sample_sprint_data)
        test_session.add(sprint1)
        test_session.commit()
        
        # Try to create another sprint with same project_id + sprint_key
        sprint2_data = sample_sprint_data.copy()
        sprint2 = SprintORM(**sprint2_data)
        test_session.add(sprint2)
        
        with pytest.raises(IntegrityError):
            test_session.commit()


# =============================================================================
# Task Dependency ORM Tests
# =============================================================================

class TestTaskDependencyORM:
    """Test TaskDependencyORM with critical constraint corrections validation."""
    
    def test_task_dependency_creation(self, test_session, sample_task_dependency_data):
        """Test basic task dependency creation."""
        dependency = TaskDependencyORM(**sample_task_dependency_data)
        test_session.add(dependency)
        test_session.commit()
        
        assert dependency.id is not None
        assert dependency.task_id == 1
        assert dependency.depends_on_task_id == 2
        assert dependency.dependency_type == DependencyType.FINISH_TO_START.value
    
    def test_self_dependency_constraint_correction(self, test_session):
        """Test critical constraint correction for self-dependencies."""
        # Normal self-dependency should fail
        dependency = TaskDependencyORM(
            task_id=1,
            depends_on_task_id=1,  # Self-dependency
            dependency_type=DependencyType.FINISH_TO_START.value,
            external_dependency=False  # Not external
        )
        test_session.add(dependency)
        
        with pytest.raises(IntegrityError):
            test_session.commit()
        
        test_session.rollback()
        
        # External self-dependency should work (user correction)
        external_dependency = TaskDependencyORM(
            task_id=1,
            depends_on_task_id=1,  # Self-dependency
            dependency_type=DependencyType.FINISH_TO_START.value,
            external_dependency=True,  # External allows self-dependency
            external_system="jira",
            external_reference="PROJ-123"
        )
        test_session.add(external_dependency)
        test_session.commit()  # Should not raise
        
        assert external_dependency.id is not None
        assert external_dependency.is_external is True
    
    def test_dependency_enum_properties(self, test_session, sample_task_dependency_data):
        """Test enum properties with fallback handling."""
        dependency = TaskDependencyORM(**sample_task_dependency_data)
        
        # Test normal enum conversion
        assert dependency.dependency_type_enum == DependencyType.FINISH_TO_START
        assert dependency.dependency_strength_enum == DependencyStrength.HARD
        assert dependency.risk_level_enum == RiskLevel.MEDIUM
        
        # Test fallback for invalid values
        dependency.dependency_type = 'invalid_type'
        assert dependency.dependency_type_enum == DependencyType.FINISH_TO_START  # Should fallback
    
    def test_dependency_validation_logic(self, test_session, sample_task_dependency_data):
        """Test dependency validation with user corrections."""
        dependency = TaskDependencyORM(**sample_task_dependency_data)
        
        validation_result = dependency.validate_dependency()
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0
        
        # Test critical risk validation
        dependency.risk_level = RiskLevel.CRITICAL.value
        validation_result = dependency.validate_dependency()
        assert validation_result.is_valid is False
        assert "Critical risk dependency must have mitigation plan" in validation_result.errors
        
        # Add mitigation plan should fix validation
        dependency.create_mitigation_plan("Use alternative API endpoint")
        validation_result = dependency.validate_dependency()
        assert validation_result.is_valid is True
    
    def test_external_dependency_management(self, test_session):
        """Test external dependency features with JSON contact info."""
        dependency = TaskDependencyORM.create_external_dependency(
            task_id=1,
            system="jira",
            reference="PROJ-123",
            reason="External API dependency",
            contact_info={
                "contact_name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890"
            },
            created_by=1
        )
        test_session.add(dependency)
        test_session.commit()
        
        assert dependency.external_dependency is True
        assert dependency.external_system == "jira"
        assert dependency.external_reference == "PROJ-123"
        
        contact_info = dependency.get_external_contact_info()
        assert contact_info['contact_name'] == "John Doe"
        assert contact_info['email'] == "john@example.com"
    
    def test_dependency_timing_calculations(self, test_session, sample_task_dependency_data):
        """Test timing calculation methods."""
        dependency = TaskDependencyORM(**sample_task_dependency_data)
        dependency.lead_lag_days = 3  # 3 day lag
        
        predecessor_end = datetime(2025, 8, 25, 17, 0, 0, tzinfo=timezone.utc)
        calculated_start = dependency.calculate_timing_impact(predecessor_end)
        
        # Should add 3 days lag
        expected = datetime(2025, 8, 28, 17, 0, 0, tzinfo=timezone.utc)
        assert calculated_start == expected


# =============================================================================
# Task Labels ORM Tests  
# =============================================================================

class TestTaskLabelsORM:
    """Test TaskLabelORM with extensive Portuguese documentation features."""
    
    def test_label_creation_and_lifecycle(self, test_session):
        """Test label creation with Portuguese documentation features."""
        label = TaskLabelORM(
            label_name="bug",
            label_description="Bugs and defects",
            label_color="#ff0000",
            label_category="issue",
            visibility=LabelVisibility.PUBLIC.value
        )
        test_session.add(label)
        test_session.commit()
        
        assert label.id is not None
        assert label.label_name == "bug"
        assert label.visibility_enum == LabelVisibility.PUBLIC
        assert label.is_deleted is False
    
    def test_label_auto_assignment_rules(self, test_session):
        """Test auto-assignment rule functionality with confidence scoring."""
        label = TaskLabelORM(
            label_name="authentication",
            label_description="Authentication related tasks"
        )
        
        # Add auto-assignment rule
        label.add_auto_apply_rule(
            condition_type="title_contains",
            condition_value="auth",
            confidence_threshold=0.8,
            rule_priority=8
        )
        test_session.add(label)
        test_session.commit()
        
        # Test rule retrieval
        rules = label.get_auto_apply_rules()
        assert len(rules) == 1
        assert rules[0].condition_type == "title_contains"
        assert rules[0].condition_value == "auth"
        assert rules[0].confidence_threshold == 0.8
        
        # Test auto-assignment matching
        confidence = label.check_auto_apply_match(
            task_title="Implement OAuth authentication",
            task_description="Add OAuth 2.0 authentication system",
            task_type="feature"
        )
        assert confidence > 0.7  # Should match "auth" in title
    
    def test_label_hierarchy_and_permissions(self, test_session):
        """Test label hierarchy and access control."""
        parent_label = TaskLabelORM(
            label_name="backend",
            label_description="Backend development tasks",
            visibility=LabelVisibility.PUBLIC.value
        )
        test_session.add(parent_label)
        test_session.commit()
        
        child_label = TaskLabelORM(
            label_name="api",
            label_description="API development",
            parent_label_id=parent_label.id,
            visibility=LabelVisibility.TEAM.value
        )
        child_label.set_team_restrictions([101, 102, 103])
        test_session.add(child_label)
        test_session.commit()
        
        # Test hierarchy
        assert child_label.parent_label_id == parent_label.id
        assert child_label.get_hierarchy_level() == 1
        assert "backend > api" in child_label.get_full_path()
        
        # Test access control
        assert child_label.can_be_used_by(101) is True  # In team
        assert child_label.can_be_used_by(999) is False  # Not in team
        
        restrictions = child_label.get_team_restrictions()
        assert 101 in restrictions
        assert len(restrictions) == 3


class TestTaskLabelAssignmentORM:
    """Test TaskLabelAssignmentORM with confidence and validation features."""
    
    def test_manual_assignment_creation(self, test_session):
        """Test manual assignment creation with high confidence."""
        assignment = TaskLabelAssignmentORM.create_manual_assignment(
            task_id=1,
            label_id=1,
            assigned_by=101,
            reason="Task clearly relates to authentication"
        )
        test_session.add(assignment)
        test_session.commit()
        
        assert assignment.id is not None
        assert assignment.assignment_context_enum == AssignmentContext.MANUAL
        assert assignment.is_validated is True
        assert assignment.confidence_score == Decimal("1.00")
        assert assignment.is_high_confidence is True
    
    def test_auto_assignment_creation(self, test_session):
        """Test automatic assignment with validation workflow."""
        assignment = TaskLabelAssignmentORM.create_auto_assignment(
            task_id=1,
            label_id=1,
            confidence_score=0.85,
            rule_reason="Title contains 'auth' keyword"
        )
        test_session.add(assignment)
        test_session.commit()
        
        assert assignment.assignment_context_enum == AssignmentContext.AUTOMATIC
        assert assignment.is_validated is False  # Auto-assignments need validation
        assert assignment.confidence_score == Decimal("0.85")
        assert assignment.is_high_confidence is True
        
        # Test validation workflow
        result = assignment.validate_assignment(
            validated_by=102,
            notes="Confirmed by manual review"
        )
        assert result is True
        assert assignment.is_validated is True
        assert assignment.validated_by == 102
        assert "VALIDATED: Confirmed by manual review" in assignment.assigned_reason
    
    def test_confidence_constraint_validation(self, test_session):
        """Test confidence_score constraint (0-1 range)."""
        # Valid confidence score
        assignment = TaskLabelAssignmentORM(
            task_id=1,
            label_id=1,
            confidence_score=Decimal("0.75")
        )
        test_session.add(assignment)
        test_session.commit()  # Should work
        
        test_session.rollback()
        
        # Test confidence update with clamping
        assignment = TaskLabelAssignmentORM(task_id=1, label_id=1)
        assignment.update_confidence(1.5, "Test clamping")  # Over 1.0
        assert assignment.confidence_score == Decimal("1.00")  # Should be clamped
        
        assignment.update_confidence(-0.5, "Test lower clamp")  # Below 0.0
        assert assignment.confidence_score == Decimal("0.00")  # Should be clamped


# =============================================================================
# Repository Pattern Tests
# =============================================================================

class TestRepositoryPattern:
    """Test repository pattern implementation and integration."""
    
    def test_base_repository_crud_operations(self, test_session, sample_sprint_data):
        """Test basic CRUD operations through repository pattern."""
        repository = BaseRepository(SprintORM, test_session)
        
        # Test create
        sprint = SprintORM(**sample_sprint_data)
        result = repository.create(sprint)
        assert result.success is True
        assert result.data.id is not None
        
        created_id = result.data.id
        
        # Test get by ID
        result = repository.get_by_id(created_id)
        assert result.success is True
        assert result.data.sprint_key == 'TEST-2025-01'
        
        # Test update
        result.data.sprint_name = "Updated Test Sprint"
        update_result = repository.update(result.data)
        assert update_result.success is True
        assert update_result.data.sprint_name == "Updated Test Sprint"
        
        # Test get all
        list_result = repository.get_all()
        assert list_result.success is True
        assert len(list_result.data) >= 1
        
        # Test delete
        delete_result = repository.delete(created_id)
        assert delete_result.success is True
        assert delete_result.data is True
    
    def test_repository_error_handling(self, test_session):
        """Test repository error handling and Result pattern."""
        repository = BaseRepository(SprintORM, test_session)
        
        # Test get non-existent entity
        result = repository.get_by_id(999)
        assert result.success is False
        assert "not found" in result.error
        
        # Test update without ID
        sprint = SprintORM(sprint_name="Test Sprint")
        result = repository.update(sprint)
        assert result.success is False
        assert "must have ID" in result.error
    
    def test_repository_factory_and_manager(self, test_session, sample_sprint_data):
        """Test repository factory and manager patterns."""
        # Test repository factory
        sprint_repo = RepositoryFactory.create_repository(SprintORM, test_session)
        assert isinstance(sprint_repo, BaseRepository)
        
        # Test repository manager with shared transactions
        manager = RepositoryManager(test_session)
        
        with manager.transaction():
            sprint_repo = manager.get_repository(SprintORM)
            label_repo = manager.get_repository(TaskLabelORM)
            
            # Create entities in same transaction
            sprint = SprintORM(**sample_sprint_data)
            sprint_result = sprint_repo.create(sprint)
            assert sprint_result.success is True
            
            label = TaskLabelORM(label_name="test-label")
            label_result = label_repo.create(label)
            assert label_result.success is True
    
    def test_repository_filtering_and_counting(self, test_session, sample_sprint_data):
        """Test repository filtering and counting capabilities."""
        repository = BaseRepository(SprintORM, test_session)
        
        # Create test data
        sprint1 = SprintORM(**sample_sprint_data)
        sprint1.status = SprintStatus.PLANNING.value
        repository.create(sprint1)
        
        sprint2_data = sample_sprint_data.copy()
        sprint2_data['sprint_key'] = 'TEST-2025-02'
        sprint2 = SprintORM(**sprint2_data)
        sprint2.status = SprintStatus.ACTIVE.value
        repository.create(sprint2)
        
        # Test filtering
        active_sprints = repository.find_by(status=SprintStatus.ACTIVE.value)
        assert active_sprints.success is True
        assert len(active_sprints.data) == 1
        assert active_sprints.data[0].sprint_key == 'TEST-2025-02'
        
        # Test counting
        count_result = repository.count({'status': SprintStatus.PLANNING.value})
        assert count_result.success is True
        assert count_result.data == 1


# =============================================================================
# Service Layer Integration Tests
# =============================================================================

class TestServiceLayerIntegration:
    """Test integration between ORM models and existing service layer."""
    
    def test_result_pattern_compatibility(self, test_session, sample_sprint_data):
        """Test that repository Results are compatible with ServiceResult pattern."""
        repository = BaseRepository(SprintORM, test_session)
        
        # Create sprint
        sprint = SprintORM(**sample_sprint_data)
        result = repository.create(sprint)
        
        # Verify Result pattern compatibility
        assert hasattr(result, 'success')
        assert hasattr(result, 'data')
        assert hasattr(result, 'error')
        assert hasattr(result, 'errors')
        
        # Test error case
        error_result = repository.get_by_id(999)
        assert error_result.success is False
        assert len(error_result.errors) == 1
    
    def test_json_field_serialization_integration(self, test_session, sample_sprint_data):
        """Test JSON field serialization matches existing patterns."""
        sprint = SprintORM(**sample_sprint_data)
        test_session.add(sprint)
        test_session.commit()
        
        # Test JSON field operations (using mixins)
        test_data = {'key1': 'value1', 'key2': 'value2'}
        result = sprint.set_json_field('team_members', [101, 102, 103])
        assert result is True
        
        retrieved_data = sprint.get_json_field('team_members', [])
        assert retrieved_data == [101, 102, 103]
    
    def test_audit_mixin_integration(self, test_session):
        """Test audit mixin integration with ORM models."""
        label = TaskLabelORM(
            label_name="integration-test",
            label_description="Integration test label",
            created_by=101
        )
        test_session.add(label)
        test_session.commit()
        
        # Test audit fields are set
        assert label.created_by == 101
        assert hasattr(label, 'created_at')
        assert hasattr(label, 'updated_at')


# =============================================================================
# Portuguese Documentation Features Tests
# =============================================================================

class TestPortugueseDocumentationFeatures:
    """Test features specifically documented in Portuguese (user corrections)."""
    
    def test_tdah_optimization_features(self, test_session, sample_sprint_data):
        """Test TDAH optimization features documented in Portuguese."""
        sprint = SprintORM(**sample_sprint_data)
        sprint.story_points_committed = 60  # High workload
        test_session.add(sprint)
        test_session.commit()
        
        # Test TDAH-friendly recommendations
        recommendations = sprint.get_tdah_friendly_recommendations()
        assert isinstance(recommendations, list)
        assert any("complexidade" in rec for rec in recommendations)  # Portuguese text
        
        # Test cognitive load calculation
        cognitive_load = sprint.calculate_cognitive_load_score()
        assert cognitive_load > 5.0  # Should be high due to high story points
    
    def test_label_portuguese_features(self, test_session):
        """Test label features with Portuguese documentation."""
        label = TaskLabelORM(
            label_name="autenticacao",
            label_description="Tarefas relacionadas à autenticação",
            label_category="seguranca"
        )
        test_session.add(label)
        test_session.commit()
        
        # Test Portuguese auto-assignment rules
        label.add_auto_apply_rule(
            condition_type="title_contains",
            condition_value="login",
            confidence_threshold=0.8
        )
        
        confidence = label.check_auto_apply_match(
            task_title="Implementar sistema de login",
            task_description="Criar tela de login com validação",
            task_type="feature"
        )
        assert confidence > 0.7  # Should match "login" in title


# =============================================================================
# Performance and Edge Case Tests
# =============================================================================

class TestPerformanceAndEdgeCases:
    """Test performance characteristics and edge cases."""
    
    def test_json_field_error_handling(self, test_session):
        """Test JSON field error handling with malformed data."""
        sprint = SprintORM(
            project_id=1,
            sprint_key='TEST-ERROR',
            sprint_name='Error Test Sprint',
            start_date=date(2025, 8, 23),
            end_date=date(2025, 9, 6)
        )
        
        # Test with invalid JSON data (should handle gracefully)
        sprint.team_members = "invalid json"  # Direct assignment of non-JSON
        
        # Should return empty list as fallback
        members = sprint.get_team_members_list()
        assert members == []
    
    def test_enum_fallback_handling(self, test_session, sample_sprint_data):
        """Test enum fallback handling for invalid database values."""
        sprint = SprintORM(**sample_sprint_data)
        test_session.add(sprint)
        test_session.commit()
        
        # Simulate database corruption with invalid enum value
        test_session.execute(
            "UPDATE sprints SET status = 'corrupted_status' WHERE id = ?",
            (sprint.id,)
        )
        test_session.commit()
        
        # Refresh from database
        test_session.refresh(sprint)
        
        # Should fallback to default enum value
        assert sprint.status_enum == SprintStatus.PLANNING  # Fallback value
    
    def test_repository_transaction_rollback(self, test_session):
        """Test repository transaction rollback on errors."""
        repository = BaseRepository(SprintORM, test_session)
        manager = RepositoryManager(test_session)
        
        try:
            with manager.transaction():
                # Create valid sprint
                sprint = SprintORM(
                    project_id=1,
                    sprint_key='TEST-ROLLBACK',
                    sprint_name='Rollback Test Sprint',
                    start_date=date(2025, 8, 23),
                    end_date=date(2025, 9, 6)
                )
                result = repository.create(sprint)
                assert result.success is True
                
                # Force an error to trigger rollback
                raise Exception("Forced error for rollback test")
                
        except Exception:
            # Transaction should have been rolled back
            pass
        
        # Verify sprint was not persisted due to rollback
        check_result = repository.find_by(sprint_key='TEST-ROLLBACK')
        assert len(check_result.data) == 0


if __name__ == '__main__':
    # Run specific test groups
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-x'  # Stop on first failure for debugging
    ])