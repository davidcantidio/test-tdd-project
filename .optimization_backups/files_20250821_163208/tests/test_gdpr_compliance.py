#!/usr/bin/env python3
"""
🧪 GDPR Compliance Tests

Comprehensive tests for GDPR compliance implementation:
- Data Subject Rights testing (Articles 15-22)
- Consent Management validation (Articles 6, 7)
- Data Audit Logging verification (Article 30)
- Data Retention Policy testing (Article 5)
- Privacy by Design validation (Article 25)
"""

import pytest
import tempfile
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Test imports
try:
    from duration_system.gdpr_compliance import (
        GDPRManager, ConsentRecord, DataSubjectRequest, DataProcessingRecord,
        DataBreachRecord, GDPRAuditLogger, DataRetentionManager,
        DataSubjectRightType, ConsentBasis, DataCategory
    )
    GDPR_AVAILABLE = True
except ImportError:
    GDPR_AVAILABLE = False
    pytest.skip("GDPR compliance module not available", allow_module_level=True)


class TestConsentRecord:
    """Test ConsentRecord functionality."""
    
    # TODO: Consider extracting this block into a separate method
    def test_consent_record_creation(self):
        """Test consent record creation and validation."""
        consent = ConsentRecord(
            data_subject_id="user_123",
            purpose="Service provision",
            legal_basis=ConsentBasis.CONSENT,
            data_categories=[DataCategory.IDENTITY, DataCategory.CONTACT],
            consent_given=True,
            retention_period=365
        )
        
        assert consent.data_subject_id == "user_123"
        assert consent.purpose == "Service provision"
        assert consent.legal_basis == ConsentBasis.CONSENT
        assert DataCategory.IDENTITY in consent.data_categories
        assert consent.consent_given is True
        assert consent.is_valid() is True
        assert consent.consent_withdrawn is False
    
# TODO: Consider extracting this block into a separate method
    
    def test_consent_withdrawal(self):
        """Test consent withdrawal functionality."""
        consent = ConsentRecord(
            data_subject_id="user_456",
            purpose="Marketing",
            consent_given=True
        )
        
        # Initially valid
        assert consent.is_valid() is True
        
        # Withdraw consent
        consent.withdraw_consent()
        
        assert consent.consent_withdrawn is True
        assert consent.withdrawal_timestamp is not None
        assert consent.is_valid() is False
    
    def test_consent_expiration(self):
        """Test consent expiration based on retention period."""
        # Create consent that expires immediately
        consent = ConsentRecord(
            data_subject_id="user_789",
            purpose="Testing",
            consent_given=True,
            retention_period=0  # Expires immediately
        )
        consent.consent_timestamp = datetime.now() - timedelta(days=1)
        
# TODO: Consider extracting this block into a separate method
        
        assert consent.is_valid() is False
    
    def test_consent_serialization(self):
        """Test consent record serialization to dictionary."""
        consent = ConsentRecord(
            data_subject_id="user_serialize",
            purpose="Serialization test",
            legal_basis=ConsentBasis.LEGITIMATE_INTERESTS,
            data_categories=[DataCategory.BEHAVIORAL, DataCategory.TECHNICAL],
            consent_given=True
        )
        
        consent_dict = consent.to_dict()
        
        assert consent_dict["data_subject_id"] == "user_serialize"
        assert consent_dict["legal_basis"] == "legitimate_interests"
        assert "behavioral" in consent_dict["data_categories"]
        assert "technical" in consent_dict["data_categories"]
        assert isinstance(consent_dict["consent_timestamp"], str)


class TestDataSubjectRequest:
    """Test DataSubjectRequest functionality."""
    
    def test_request_creation(self):
        """Test data subject request creation."""
        request = DataSubjectRequest(
            request_type=DataSubjectRightType.ACCESS,
            data_subject_id="user_request",
            email="user@test.com",
            verification_method="email"
        )
        
        assert request.request_type == DataSubjectRightType.ACCESS
        # TODO: Consider extracting this block into a separate method
        assert request.data_subject_id == "user_request"
        assert request.email == "user@test.com"
        assert request.processing_status == "pending"
        assert request.verification_completed is False
    
    def test_request_verification(self):
        """Test request verification process."""
        request = DataSubjectRequest(
            request_type=DataSubjectRightType.RECTIFICATION,
            data_subject_id="user_verify",
            email="verify@test.com"
        )
        
        # Initially not verified
        assert request.verification_completed is False
        assert request.processing_status == "pending"
        
        # Mark as verified
        request.mark_verified()
        
        assert request.verification_completed is True
        assert request.verification_timestamp is not None
        assert request.processing_status == "in_progress"
    
    def test_request_completion(self):
        """Test request completion with response data."""
        request = DataSubjectRequest(
            request_type=DataSubjectRightType.ERASURE,
            data_subject_id="user_complete",
            email="complete@test.com"
        )
        
        response_data = {"deleted": True, "timestamp": datetime.now().isoformat()}
        request.complete_request(response_data)
        
        assert request.processing_status == "completed"
        assert request.response_data == response_data
    
    def test_request_rejection(self):
        """Test request rejection with reason."""
        request = DataSubjectRequest(
            request_type=DataSubjectRightType.DATA_PORTABILITY,
            data_subject_id="user_reject",
            email="reject@test.com"
        )
        
        # TODO: Consider extracting this block into a separate method
        rejection_reason = "Insufficient verification"
        request.reject_request(rejection_reason)
        
        assert request.processing_status == "rejected"
        assert request.rejection_reason == rejection_reason
    
    def test_request_overdue_detection(self):
        """Test overdue request detection."""
        # Create request with past due date
        request = DataSubjectRequest(
            request_type=DataSubjectRightType.ACCESS,
            data_subject_id="user_overdue",
            email="overdue@test.com"
        )
        request.response_due_date = datetime.now() - timedelta(days=1)
        
        assert request.is_overdue() is True
        
        # Complete the request
        request.complete_request({"data": "test"})
        
        # Should no longer be overdue
        assert request.is_overdue() is False


class TestGDPRAuditLogger:
    """Test GDPR audit logging functionality."""
    
    @pytest.fixture
    def temp_log_file(self):
        """Create temporary log file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        yield log_file
        # Cleanup
        Path(log_file).unlink(missing_ok=True)
    
    # TODO: Consider extracting this block into a separate method
    def test_audit_logger_creation(self, temp_log_file):
        """Test audit logger creation and file handling."""
        logger = GDPRAuditLogger(temp_log_file)
        
        assert logger.log_file == temp_log_file
        assert logger.logger is not None
    
    def test_data_access_logging(self, temp_log_file):
        """Test data access audit logging."""
        logger = GDPRAuditLogger(temp_log_file)
        
        logger.log_data_access(
            data_subject_id="user_123",
            data_type="profile",
            accessed_by="admin",
            purpose="support_request"
        )
        
        # TODO: Consider extracting this block into a separate method
        # Verify log entry
        with open(temp_log_file, 'r') as f:
            log_content = f.read()
            assert "DATA_ACCESS" in log_content
            assert "user_123" in log_content
            assert "profile" in log_content
            assert "admin" in log_content
    
    def test_consent_change_logging(self, temp_log_file):
        """Test consent change audit logging."""
        logger = GDPRAuditLogger(temp_log_file)
        
        logger.log_consent_change(
            data_subject_id="user_456",
            consent_id="consent_789",
            action="withdrawn",
            purpose="marketing"
        )
        
        # Verify log entry
        with open(temp_log_file, 'r') as f:
            log_content = f.read()
            assert "CONSENT_CHANGE" in log_content
            assert "user_456" in log_content
            assert "withdrawn" in log_content


class TestDataRetentionManager:
    """Test data retention management functionality."""
    
    @pytest.fixture
    def temp_retention_db(self):
        """Create temporary retention database for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        yield db_path
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_retention_manager_creation(self, temp_retention_db):
        """Test retention manager creation and database initialization."""
        manager = DataRetentionManager(temp_retention_db)
        
# TODO: Consider extracting this block into a separate method
        
        assert manager.db_path == temp_retention_db
        # Database should be created and accessible
        with manager._get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert "retention_policies" in tables
            assert "scheduled_deletions" in tables
    
    def test_add_retention_policy(self, temp_retention_db):
        """Test adding retention policies."""
        manager = DataRetentionManager(temp_retention_db)
        
        policy_id = manager.add_retention_policy(
            data_category=DataCategory.CONTACT,
            retention_days=1095,  # 3 years
            legal_basis=ConsentBasis.CONSENT,
            auto_delete=True
        )
        
        assert policy_id is not None
        
        # TODO: Consider extracting this block into a separate method
        # Verify policy was stored
        with manager._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM retention_policies WHERE policy_id = ?",
                (policy_id,)
            )
            policy = cursor.fetchone()
            assert policy is not None
            assert policy[1] == "contact"  # data_category
            assert policy[2] == 1095       # retention_days
    
    def test_schedule_data_deletion(self, temp_retention_db):
        """Test scheduling data for deletion."""
        manager = DataRetentionManager(temp_retention_db)
        
        # First create a policy
        policy_id = manager.add_retention_policy(
            data_category=DataCategory.BEHAVIORAL,
            retention_days=365,
            legal_basis=ConsentBasis.LEGITIMATE_INTERESTS
        )
        
        # Schedule deletion
        deletion_date = datetime.now() + timedelta(days=365)
        deletion_id = manager.schedule_data_deletion(
            data_subject_id="user_delete",
            data_category=DataCategory.BEHAVIORAL,
            deletion_date=deletion_date,
            policy_id=policy_id
        )
        
        # TODO: Consider extracting this block into a separate method
        assert deletion_id is not None
        
        # Verify scheduled deletion
        with manager._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM scheduled_deletions WHERE deletion_id = ?",
                (deletion_id,)
            )
            deletion = cursor.fetchone()
            assert deletion is not None
            assert deletion[1] == "user_delete"  # data_subject_id
    
    def test_execute_scheduled_deletions(self, temp_retention_db):
        """Test executing overdue scheduled deletions."""
        manager = DataRetentionManager(temp_retention_db)
        
        # Create policy
        policy_id = manager.add_retention_policy(
            data_category=DataCategory.TECHNICAL,
            retention_days=1,
            legal_basis=ConsentBasis.CONSENT
        )
        
        # Schedule deletion in the past (overdue)
        past_date = datetime.now() - timedelta(days=1)
        deletion_id = manager.schedule_data_deletion(
            data_subject_id="user_overdue",
            data_category=DataCategory.TECHNICAL,
            deletion_date=past_date,
            policy_id=policy_id
        )
        
        # Execute scheduled deletions
        executed = manager.execute_scheduled_deletions()
        
        assert len(executed) == 1
        assert executed[0]["deletion_id"] == deletion_id
        assert executed[0]["data_subject_id"] == "user_overdue"


class TestGDPRManager:
    """Test main GDPR manager functionality."""
    
    @pytest.fixture
    def temp_gdpr_files(self):
        """Create temporary files for GDPR manager testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as db_file:
            db_path = db_file.name
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as log_file:
            log_path = log_file.name
        
        yield db_path, log_path
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
        Path(log_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def gdpr_manager(self, temp_gdpr_files):
        """Create GDPR manager for testing."""
        db_path, log_path = temp_gdpr_files
        return GDPRManager(db_path, log_path)
    
    def test_gdpr_manager_initialization(self, gdpr_manager):
        """Test GDPR manager initialization."""
        assert gdpr_manager.db_path is not None
        assert gdpr_manager.audit_logger is not None
        # TODO: Consider extracting this block into a separate method
        assert gdpr_manager.retention_manager is not None
        assert isinstance(gdpr_manager.data_processors, dict)
    
    def test_register_data_processor(self, gdpr_manager):
        """Test registering data processors."""
        def mock_processor(data_subject_id: str, operation: str):
            return {"mock": "data"}
        
        gdpr_manager.register_data_processor("mock_data", mock_processor)
        
        assert "mock_data" in gdpr_manager.data_processors
        assert gdpr_manager.data_processors["mock_data"] == mock_processor
    
    def test_record_and_retrieve_consent(self, gdpr_manager):
        """Test consent recording and retrieval."""
        consent = ConsentRecord(
            data_subject_id="user_consent",
            purpose="Testing consent",
            legal_basis=ConsentBasis.CONSENT,
            # TODO: Consider extracting this block into a separate method
            data_categories=[DataCategory.IDENTITY],
            consent_given=True
        )
        
        # Record consent
        consent_id = gdpr_manager.record_consent(consent)
        assert consent_id is not None
        
        # Retrieve valid consents
        valid_consents = gdpr_manager.get_valid_consents("user_consent")
        assert len(valid_consents) == 1
        assert valid_consents[0].consent_id == consent_id
        assert valid_consents[0].data_subject_id == "user_consent"
    
    def test_withdraw_consent(self, gdpr_manager):
        """Test consent withdrawal."""
        consent = ConsentRecord(
            data_subject_id="user_withdraw",
            purpose="Testing withdrawal",
            consent_given=True
        )
        
        consent_id = gdpr_manager.record_consent(consent)
        
        # Withdraw consent
        success = gdpr_manager.withdraw_consent("user_withdraw", consent_id)
        assert success is True
        
        # Should no longer appear in valid consents
        # TODO: Consider extracting this block into a separate method
        valid_consents = gdpr_manager.get_valid_consents("user_withdraw")
        assert len(valid_consents) == 0
    
    def test_submit_data_subject_request(self, gdpr_manager):
        """Test submitting data subject requests."""
        request = DataSubjectRequest(
            request_type=DataSubjectRightType.ACCESS,
            data_subject_id="user_request",
            email="request@test.com"
        )
        
        request_id = gdpr_manager.submit_data_subject_request(request)
        assert request_id is not None
        assert request_id == request.request_id
    
    def test_process_access_request(self, gdpr_manager):
        """Test processing access requests."""
        # Register mock data processor
        def mock_processor(data_subject_id: str, operation: str):
            if operation == "access":
                return {"user_data": f"data_for_{data_subject_id}"}
            return None
        
        gdpr_manager.register_data_processor("user_profile", mock_processor)
        
        # Create and submit request
        request = DataSubjectRequest(
            request_type=DataSubjectRightType.ACCESS,
            # TODO: Consider extracting this block into a separate method
            data_subject_id="user_access",
            email="access@test.com"
        )
        request.mark_verified()  # Mark as verified
        
        request_id = gdpr_manager.submit_data_subject_request(request)
        
        # Process the request
        response = gdpr_manager.process_data_subject_request(request_id)
        
        assert response is not None
        assert "data_subject_id" in response
        assert response["data_subject_id"] == "user_access"
        assert "user_profile" in response
        assert response["user_profile"]["user_data"] == "data_for_user_access"
    
    def test_process_erasure_request(self, gdpr_manager):
        """Test processing erasure requests."""
        # Register mock data processor
        def mock_processor(data_subject_id: str, operation: str):
            if operation == "delete":
                return {"deleted": True, "timestamp": datetime.now().isoformat()}
            return None
        
        gdpr_manager.register_data_processor("user_data", mock_processor)
        
        # Create consent first
        consent = ConsentRecord(
            data_subject_id="user_erasure",
            purpose="Testing erasure",
            consent_given=True
        )
        gdpr_manager.record_consent(consent)
        
        # Create and submit erasure request
        request = DataSubjectRequest(
            request_type=DataSubjectRightType.ERASURE,
            data_subject_id="user_erasure",
            # TODO: Consider extracting this block into a separate method
            email="erasure@test.com"
        )
        request.mark_verified()
        
        request_id = gdpr_manager.submit_data_subject_request(request)
        
        # Process the request
        response = gdpr_manager.process_data_subject_request(request_id)
        
        assert response is not None
        assert "deletion_timestamp" in response
        assert "user_data" in response["deleted_data_types"]
        
        # Verify consents were withdrawn
        valid_consents = gdpr_manager.get_valid_consents("user_erasure")
        assert len(valid_consents) == 0
    
    def test_get_compliance_report(self, gdpr_manager):
        """Test generating compliance reports."""
        # Add some test data
        consent = ConsentRecord(
            data_subject_id="user_report",
            purpose="Testing report",
            consent_given=True
        )
        gdpr_manager.record_consent(consent)
        
# TODO: Consider extracting this block into a separate method
        
        request = DataSubjectRequest(
            request_type=DataSubjectRightType.ACCESS,
            data_subject_id="user_report",
            email="report@test.com"
        )
        gdpr_manager.submit_data_subject_request(request)
        
        # Generate report
        report = gdpr_manager.get_compliance_report()
        
        assert "compliance_status" in report
        assert "active_consents" in report
        assert "pending_requests" in report
        assert "overdue_requests" in report
        assert report["active_consents"] >= 1
        assert report["pending_requests"] >= 1
    
    def test_unverified_request_processing(self, gdpr_manager):
        """Test that unverified requests are not processed."""
        request = DataSubjectRequest(
            request_type=DataSubjectRightType.ACCESS,
            data_subject_id="user_unverified",
            email="unverified@test.com"
        )
        # Don't mark as verified
        
        request_id = gdpr_manager.submit_data_subject_request(request)
        
        # Attempt to process unverified request
        response = gdpr_manager.process_data_subject_request(request_id)
        
        assert response is not None
        assert "error" in response
        # TODO: Consider extracting this block into a separate method
        assert "not verified" in response["error"].lower()


class TestGDPRIntegration:
    """Test GDPR integration scenarios."""
    
    @pytest.fixture
    def temp_gdpr_files(self):
        """Create temporary files for integration testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as db_file:
            db_path = db_file.name
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as log_file:
            log_path = log_file.name
        
        yield db_path, log_path
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
        Path(log_path).unlink(missing_ok=True)
    
    def test_full_gdpr_workflow(self, temp_gdpr_files):
        """Test complete GDPR workflow from consent to data deletion."""
        db_path, log_path = temp_gdpr_files
        gdpr = GDPRManager(db_path, log_path)
        
        # Register data processor
        def user_processor(data_subject_id: str, operation: str):
            if operation == "access":
                return {"profile": f"profile_data_for_{data_subject_id}"}
            elif operation == "delete":
                return {"deleted": True, "data_type": "user_profile"}
            elif operation == "export":
                return {"exportable": f"export_data_for_{data_subject_id}"}
            return None
        
        gdpr.register_data_processor("user_profile", user_processor)
        
        # 1. Record consent
        consent = ConsentRecord(
            data_subject_id="workflow_user",
            purpose="Service provision",
            legal_basis=ConsentBasis.CONSENT,
            data_categories=[DataCategory.IDENTITY, DataCategory.CONTACT],
            consent_given=True
        )
        consent_id = gdpr.record_consent(consent)
        
        # 2. Submit access request
        access_request = DataSubjectRequest(
            request_type=DataSubjectRightType.ACCESS,
            data_subject_id="workflow_user",
            email="workflow@test.com"
        )
        access_request.mark_verified()
        
        access_request_id = gdpr.submit_data_subject_request(access_request)
        access_response = gdpr.process_data_subject_request(access_request_id)
        
        # Verify access response
        assert access_response["data_subject_id"] == "workflow_user"
        assert "user_profile" in access_response
        
        # 3. Submit portability request
        portability_request = DataSubjectRequest(
            request_type=DataSubjectRightType.DATA_PORTABILITY,
            data_subject_id="workflow_user",
            email="workflow@test.com"
        )
        portability_request.mark_verified()
        
        portability_request_id = gdpr.submit_data_subject_request(portability_request)
        portability_response = gdpr.process_data_subject_request(portability_request_id)
        
        # Verify portability response
        assert "export_timestamp" in portability_response
        assert "data" in portability_response
        
        # 4. Submit erasure request
        erasure_request = DataSubjectRequest(
            request_type=DataSubjectRightType.ERASURE,
            data_subject_id="workflow_user",
            email="workflow@test.com"
        )
        erasure_request.mark_verified()
        
        erasure_request_id = gdpr.submit_data_subject_request(erasure_request)
        erasure_response = gdpr.process_data_subject_request(erasure_request_id)
        
        # Verify erasure response
        assert "deletion_timestamp" in erasure_response
        assert "user_profile" in erasure_response["deleted_data_types"]
        
        # 5. Verify consent was withdrawn
        valid_consents = gdpr.get_valid_consents("workflow_user")
        assert len(valid_consents) == 0
        
        # 6. Generate final compliance report
        report = gdpr.get_compliance_report()
        assert report["compliance_status"] in ["compliant", "non_compliant"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])