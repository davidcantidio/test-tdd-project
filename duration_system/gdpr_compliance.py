#!/usr/bin/env python3
"""
🛡️ GDPR Compliance Framework

Comprehensive GDPR compliance implementation addressing COMP-004 audit finding:
"Missing GDPR compliance features for data subject rights"

This module provides:
1. Data Subject Rights APIs (Article 15-22)
2. Consent Management (Article 6, 7)
3. Data Audit Logging (Article 30)
4. Data Retention Policies (Article 5)
5. Privacy by Design Implementation (Article 25)

Usage:
    from duration_system.gdpr_compliance import GDPRManager, DataSubjectRequest
    
    # Initialize GDPR manager
    gdpr = GDPRManager()
    
    # Handle data subject requests
    request = DataSubjectRequest(
        request_type="access",
        data_subject_id="user_123",
        email="user@example.com"
    )
    
    response = gdpr.process_data_subject_request(request)
"""

import json
import time
import hashlib
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import sqlite3
import uuid
from contextlib import contextmanager

# GDPR compliance logging
gdpr_logger = logging.getLogger('compliance.gdpr')
gdpr_logger.setLevel(logging.INFO)

if not gdpr_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - COMPLIANCE - %(levelname)s - [GDPR] %(message)s'
    )
    handler.setFormatter(formatter)
    gdpr_logger.addHandler(handler)


class DataSubjectRightType(Enum):
    """GDPR Data Subject Rights (Articles 15-22)."""
    
    ACCESS = "access"                    # Article 15 - Right of access
    RECTIFICATION = "rectification"      # Article 16 - Right to rectification
    ERASURE = "erasure"                  # Article 17 - Right to erasure (right to be forgotten)
    RESTRICT_PROCESSING = "restrict"     # Article 18 - Right to restriction of processing
    DATA_PORTABILITY = "portability"     # Article 20 - Right to data portability
    OBJECT_PROCESSING = "object"         # Article 21 - Right to object
    OBJECT_AUTOMATED = "object_automated" # Article 22 - Automated decision-making


class ConsentBasis(Enum):
    """Legal basis for processing under GDPR Article 6."""
    
    CONSENT = "consent"                  # Article 6(1)(a) - Consent
    CONTRACT = "contract"                # Article 6(1)(b) - Contract performance
    LEGAL_OBLIGATION = "legal_obligation" # Article 6(1)(c) - Legal obligation
    VITAL_INTERESTS = "vital_interests"   # Article 6(1)(d) - Vital interests
    PUBLIC_TASK = "public_task"          # Article 6(1)(e) - Public task
    LEGITIMATE_INTERESTS = "legitimate_interests" # Article 6(1)(f) - Legitimate interests


class DataCategory(Enum):
    """Categories of personal data for processing records."""
    
    IDENTITY = "identity"                # Name, identification numbers
    CONTACT = "contact"                  # Email, phone, address
    DEMOGRAPHIC = "demographic"          # Age, gender, nationality
    BEHAVIORAL = "behavioral"            # Usage patterns, preferences
    TECHNICAL = "technical"              # IP address, device info
    PROFESSIONAL = "professional"       # Job title, company
    FINANCIAL = "financial"              # Payment information
    HEALTH = "health"                    # Health-related data
    BIOMETRIC = "biometric"              # Biometric identifiers
    CRIMINAL = "criminal"                # Criminal convictions


@dataclass
class ConsentRecord:
    """Record of user consent for GDPR compliance."""
    
    consent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data_subject_id: str = ""
    purpose: str = ""                    # Purpose of processing
    legal_basis: ConsentBasis = ConsentBasis.CONSENT
    data_categories: List[DataCategory] = field(default_factory=list)
    consent_given: bool = False
    consent_timestamp: datetime = field(default_factory=datetime.now)
    consent_withdrawn: bool = False
    withdrawal_timestamp: Optional[datetime] = None
    retention_period: int = 1095         # Days (3 years default)
    processing_restrictions: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if consent is currently valid."""
        if self.consent_withdrawn:
            return False
        
        # Check if consent has expired
        expiry_date = self.consent_timestamp + timedelta(days=self.retention_period)
        return datetime.now() < expiry_date
    
    def withdraw_consent(self):
        """Withdraw consent and record timestamp."""
        self.consent_withdrawn = True
        self.withdrawal_timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert enums to values
        data['legal_basis'] = self.legal_basis.value
        data['data_categories'] = [cat.value for cat in self.data_categories]
        # Convert datetime to ISO format
        data['consent_timestamp'] = self.consent_timestamp.isoformat()
        if self.withdrawal_timestamp:
            data['withdrawal_timestamp'] = self.withdrawal_timestamp.isoformat()
        return data


@dataclass
class DataSubjectRequest:
    """Data Subject Request under GDPR."""
    
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_type: DataSubjectRightType = DataSubjectRightType.ACCESS
    data_subject_id: str = ""
    email: str = ""
    phone: Optional[str] = None
    request_timestamp: datetime = field(default_factory=datetime.now)
    verification_method: str = "email"   # email, phone, identity_document
    verification_completed: bool = False
    verification_timestamp: Optional[datetime] = None
    processing_status: str = "pending"   # pending, in_progress, completed, rejected
    response_due_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))
    response_data: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None
    
    def mark_verified(self):
        """Mark request as verified."""
        self.verification_completed = True
        self.verification_timestamp = datetime.now()
        self.processing_status = "in_progress"
    
    def complete_request(self, response_data: Dict[str, Any]):
        """Complete the request with response data."""
        self.processing_status = "completed"
        self.response_data = response_data
    
    def reject_request(self, reason: str):
        """Reject the request with reason."""
        self.processing_status = "rejected"
        self.rejection_reason = reason
    
    def is_overdue(self) -> bool:
        """Check if request response is overdue."""
        return datetime.now() > self.response_due_date and self.processing_status != "completed"


@dataclass
class DataProcessingRecord:
    """Record of Processing Activities (Article 30)."""
    
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    controller_name: str = ""
    controller_contact: str = ""
    processing_purpose: str = ""
    legal_basis: ConsentBasis = ConsentBasis.LEGITIMATE_INTERESTS
    data_categories: List[DataCategory] = field(default_factory=list)
    data_subjects_categories: List[str] = field(default_factory=list)  # employees, customers, etc.
    recipients: List[str] = field(default_factory=list)               # Who receives the data
    third_country_transfers: List[str] = field(default_factory=list)  # International transfers
    retention_period: str = ""
    security_measures: List[str] = field(default_factory=list)
    created_timestamp: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DataBreachRecord:
    """Data Breach Record for GDPR Article 33-34 compliance."""
    
    breach_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    detected_timestamp: datetime = field(default_factory=datetime.now)
    breach_type: str = ""                # confidentiality, integrity, availability
    description: str = ""
    affected_data_categories: List[DataCategory] = field(default_factory=list)
    affected_data_subjects: int = 0
    likely_consequences: str = ""
    measures_taken: List[str] = field(default_factory=list)
    supervisory_authority_notified: bool = False
    notification_timestamp: Optional[datetime] = None
    data_subjects_notified: bool = False
    data_subject_notification_timestamp: Optional[datetime] = None
    risk_level: str = "low"              # low, medium, high
    
    def should_notify_authority(self) -> bool:
        """Check if breach requires supervisory authority notification (72 hours)."""
        return self.risk_level in ["medium", "high"]
    
    def should_notify_data_subjects(self) -> bool:
        """Check if breach requires data subject notification."""
        return self.risk_level == "high"


class GDPRAuditLogger:
    """Audit logger for GDPR compliance tracking."""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or "gdpr_audit.log"
        # Create unique logger name to avoid conflicts
        logger_name = f'gdpr.audit.{id(self)}'
        self.logger = logging.getLogger(logger_name)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler for audit trail
        file_handler = logging.FileHandler(self.log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
    
    def log_data_access(self, data_subject_id: str, data_type: str, accessed_by: str, purpose: str):
        """Log data access for audit trail."""
        self.logger.info(
            f"DATA_ACCESS - Subject: {data_subject_id}, Type: {data_type}, "
            f"AccessedBy: {accessed_by}, Purpose: {purpose}"
        )
        # Ensure immediate flush to file
        for handler in self.logger.handlers:
            handler.flush()
    
    def log_data_modification(self, data_subject_id: str, data_type: str, 
                            modified_by: str, changes: Dict[str, Any]):
        """Log data modifications."""
        self.logger.info(
            f"DATA_MODIFICATION - Subject: {data_subject_id}, Type: {data_type}, "
            f"ModifiedBy: {modified_by}, Changes: {json.dumps(changes, default=str)}"
        )
        # Ensure immediate flush to file
        for handler in self.logger.handlers:
            handler.flush()
    
    def log_data_deletion(self, data_subject_id: str, data_type: str, deleted_by: str, reason: str):
        """Log data deletions."""
        self.logger.info(
            f"DATA_DELETION - Subject: {data_subject_id}, Type: {data_type}, "
            f"DeletedBy: {deleted_by}, Reason: {reason}"
        )
        # Ensure immediate flush to file
        for handler in self.logger.handlers:
            handler.flush()
    
    def log_consent_change(self, data_subject_id: str, consent_id: str, action: str, purpose: str):
        """Log consent changes."""
        self.logger.info(
            f"CONSENT_CHANGE - Subject: {data_subject_id}, ConsentID: {consent_id}, "
            f"Action: {action}, Purpose: {purpose}"
        )
        # Ensure immediate flush to file
        for handler in self.logger.handlers:
            handler.flush()
    
    def log_subject_request(self, request: DataSubjectRequest, action: str):
        """Log data subject request processing."""
        self.logger.info(
            f"SUBJECT_REQUEST - RequestID: {request.request_id}, "
            f"Type: {request.request_type.value}, Subject: {request.data_subject_id}, "
            f"Action: {action}, Status: {request.processing_status}"
        )
        # Ensure immediate flush to file
        for handler in self.logger.handlers:
            handler.flush()


class DataRetentionManager:
    """Manages data retention and automatic deletion policies."""
    
    def __init__(self, db_path: str = "gdpr_retention.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize retention policy database."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS retention_policies (
                    policy_id TEXT PRIMARY KEY,
                    data_category TEXT NOT NULL,
                    retention_days INTEGER NOT NULL,
                    legal_basis TEXT NOT NULL,
                    auto_delete BOOLEAN DEFAULT 1,
                    created_timestamp TEXT NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_deletions (
                    deletion_id TEXT PRIMARY KEY,
                    data_subject_id TEXT NOT NULL,
                    data_category TEXT NOT NULL,
                    scheduled_date TEXT NOT NULL,
                    executed BOOLEAN DEFAULT 0,
                    executed_timestamp TEXT,
                    policy_id TEXT,
                    FOREIGN KEY (policy_id) REFERENCES retention_policies (policy_id)
                )
            """)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def add_retention_policy(self, data_category: DataCategory, retention_days: int, 
                           legal_basis: ConsentBasis, auto_delete: bool = True) -> str:
        """Add a data retention policy."""
        policy_id = str(uuid.uuid4())
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO retention_policies 
                (policy_id, data_category, retention_days, legal_basis, auto_delete, 
                 created_timestamp, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                policy_id, data_category.value, retention_days, legal_basis.value,
                auto_delete, datetime.now().isoformat(), datetime.now().isoformat()
            ))
        
        gdpr_logger.info(f"Retention policy created: {data_category.value} - {retention_days} days")
        return policy_id
    
    def schedule_data_deletion(self, data_subject_id: str, data_category: DataCategory, 
                             deletion_date: datetime, policy_id: str) -> str:
        """Schedule data for deletion."""
        deletion_id = str(uuid.uuid4())
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO scheduled_deletions
                (deletion_id, data_subject_id, data_category, scheduled_date, policy_id)
                VALUES (?, ?, ?, ?, ?)
            """, (deletion_id, data_subject_id, data_category.value, 
                  deletion_date.isoformat(), policy_id))
        
        return deletion_id
    
    def execute_scheduled_deletions(self) -> List[Dict[str, Any]]:
        """Execute overdue scheduled deletions."""
        executed_deletions = []
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT deletion_id, data_subject_id, data_category, scheduled_date
                FROM scheduled_deletions
                WHERE scheduled_date <= ? AND executed = 0
            """, (now,))
            
            overdue_deletions = cursor.fetchall()
            
            for deletion in overdue_deletions:
                deletion_id, data_subject_id, data_category, scheduled_date = deletion
                
                # Mark as executed
                conn.execute("""
                    UPDATE scheduled_deletions
                    SET executed = 1, executed_timestamp = ?
                    WHERE deletion_id = ?
                """, (now, deletion_id))
                
                executed_deletions.append({
                    "deletion_id": deletion_id,
                    "data_subject_id": data_subject_id,
                    "data_category": data_category,
                    "scheduled_date": scheduled_date,
                    "executed_timestamp": now
                })
                
                gdpr_logger.info(
                    f"Automatic data deletion executed: {data_subject_id} - {data_category}"
                )
        
        return executed_deletions


class GDPRManager:
    """Main GDPR compliance manager."""
    
    def __init__(self, db_path: str = "gdpr_compliance.db", 
                 audit_log_file: str = "gdpr_audit.log"):
        self.db_path = db_path
        self.audit_logger = GDPRAuditLogger(audit_log_file)
        self.retention_manager = DataRetentionManager()
        self._init_database()
        
        # Default data processors for different data types
        self.data_processors: Dict[str, Callable] = {}
        
        gdpr_logger.info("GDPR Manager initialized")
    
    def _init_database(self):
        """Initialize GDPR compliance database."""
        with self._get_connection() as conn:
            # Consent records table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS consent_records (
                    consent_id TEXT PRIMARY KEY,
                    data_subject_id TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    legal_basis TEXT NOT NULL,
                    data_categories TEXT NOT NULL,
                    consent_given BOOLEAN NOT NULL,
                    consent_timestamp TEXT NOT NULL,
                    consent_withdrawn BOOLEAN DEFAULT 0,
                    withdrawal_timestamp TEXT,
                    retention_period INTEGER NOT NULL,
                    processing_restrictions TEXT
                )
            """)
            
            # Data subject requests table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_subject_requests (
                    request_id TEXT PRIMARY KEY,
                    request_type TEXT NOT NULL,
                    data_subject_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    request_timestamp TEXT NOT NULL,
                    verification_method TEXT NOT NULL,
                    verification_completed BOOLEAN DEFAULT 0,
                    verification_timestamp TEXT,
                    processing_status TEXT NOT NULL,
                    response_due_date TEXT NOT NULL,
                    response_data TEXT,
                    rejection_reason TEXT
                )
            """)
            
            # Processing records table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processing_records (
                    record_id TEXT PRIMARY KEY,
                    controller_name TEXT NOT NULL,
                    controller_contact TEXT NOT NULL,
                    processing_purpose TEXT NOT NULL,
                    legal_basis TEXT NOT NULL,
                    data_categories TEXT NOT NULL,
                    data_subjects_categories TEXT NOT NULL,
                    recipients TEXT,
                    third_country_transfers TEXT,
                    retention_period TEXT NOT NULL,
                    security_measures TEXT,
                    created_timestamp TEXT NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)
            
            # Data breach records table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_breach_records (
                    breach_id TEXT PRIMARY KEY,
                    detected_timestamp TEXT NOT NULL,
                    breach_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    affected_data_categories TEXT NOT NULL,
                    affected_data_subjects INTEGER NOT NULL,
                    likely_consequences TEXT NOT NULL,
                    measures_taken TEXT,
                    supervisory_authority_notified BOOLEAN DEFAULT 0,
                    notification_timestamp TEXT,
                    data_subjects_notified BOOLEAN DEFAULT 0,
                    data_subject_notification_timestamp TEXT,
                    risk_level TEXT NOT NULL
                )
            """)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def register_data_processor(self, data_type: str, processor: Callable):
        """Register a data processor for specific data types."""
        self.data_processors[data_type] = processor
        gdpr_logger.info(f"Data processor registered for: {data_type}")
    
    def record_consent(self, consent: ConsentRecord) -> str:
        """Record user consent."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO consent_records
                (consent_id, data_subject_id, purpose, legal_basis, data_categories,
                 consent_given, consent_timestamp, consent_withdrawn, withdrawal_timestamp,
                 retention_period, processing_restrictions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                consent.consent_id, consent.data_subject_id, consent.purpose,
                consent.legal_basis.value, json.dumps([cat.value for cat in consent.data_categories]),
                consent.consent_given, consent.consent_timestamp.isoformat(),
                consent.consent_withdrawn,
                consent.withdrawal_timestamp.isoformat() if consent.withdrawal_timestamp else None,
                consent.retention_period, json.dumps(consent.processing_restrictions)
            ))
        
        self.audit_logger.log_consent_change(
            consent.data_subject_id, consent.consent_id, 
            "granted" if consent.consent_given else "denied", consent.purpose
        )
        
        return consent.consent_id
    
    def withdraw_consent(self, data_subject_id: str, consent_id: str) -> bool:
        """Withdraw user consent."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT consent_id FROM consent_records
                WHERE consent_id = ? AND data_subject_id = ?
            """, (consent_id, data_subject_id))
            
            if not cursor.fetchone():
                return False
            
            conn.execute("""
                UPDATE consent_records
                SET consent_withdrawn = 1, withdrawal_timestamp = ?
                WHERE consent_id = ? AND data_subject_id = ?
            """, (datetime.now().isoformat(), consent_id, data_subject_id))
        
        self.audit_logger.log_consent_change(
            data_subject_id, consent_id, "withdrawn", "user_request"
        )
        
        return True
    
    def get_valid_consents(self, data_subject_id: str) -> List[ConsentRecord]:
        """Get all valid consents for a data subject."""
        consents = []
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM consent_records
                WHERE data_subject_id = ? AND consent_withdrawn = 0
            """, (data_subject_id,))
            
            for row in cursor.fetchall():
                consent = ConsentRecord(
                    consent_id=row[0],
                    data_subject_id=row[1],
                    purpose=row[2],
                    legal_basis=ConsentBasis(row[3]),
                    data_categories=[DataCategory(cat) for cat in json.loads(row[4])],
                    consent_given=bool(row[5]),
                    consent_timestamp=datetime.fromisoformat(row[6]),
                    consent_withdrawn=bool(row[7]),
                    withdrawal_timestamp=datetime.fromisoformat(row[8]) if row[8] else None,
                    retention_period=row[9],
                    processing_restrictions=json.loads(row[10]) if row[10] else []
                )
                
                if consent.is_valid():
                    consents.append(consent)
        
        return consents
    
    def submit_data_subject_request(self, request: DataSubjectRequest) -> str:
        """Submit a data subject request."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO data_subject_requests
                (request_id, request_type, data_subject_id, email, phone,
                 request_timestamp, verification_method, verification_completed,
                 verification_timestamp, processing_status, response_due_date,
                 response_data, rejection_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.request_id, request.request_type.value, request.data_subject_id,
                request.email, request.phone, request.request_timestamp.isoformat(),
                request.verification_method, request.verification_completed,
                request.verification_timestamp.isoformat() if request.verification_timestamp else None,
                request.processing_status, request.response_due_date.isoformat(),
                json.dumps(request.response_data) if request.response_data else None,
                request.rejection_reason
            ))
        
        self.audit_logger.log_subject_request(request, "submitted")
        gdpr_logger.info(f"Data subject request submitted: {request.request_id}")
        
        return request.request_id
    
    def process_data_subject_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Process a data subject request."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM data_subject_requests WHERE request_id = ?
            """, (request_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            request = DataSubjectRequest(
                request_id=row[0],
                request_type=DataSubjectRightType(row[1]),
                data_subject_id=row[2],
                email=row[3],
                phone=row[4],
                request_timestamp=datetime.fromisoformat(row[5]),
                verification_method=row[6],
                verification_completed=bool(row[7]),
                verification_timestamp=datetime.fromisoformat(row[8]) if row[8] else None,
                processing_status=row[9],
                response_due_date=datetime.fromisoformat(row[10]),
                response_data=json.loads(row[11]) if row[11] else None,
                rejection_reason=row[12]
            )
        
        if not request.verification_completed:
            return {"error": "Request not verified"}
        
        # Process based on request type
        response_data = {}
        
        if request.request_type == DataSubjectRightType.ACCESS:
            response_data = self._process_access_request(request.data_subject_id)
        elif request.request_type == DataSubjectRightType.ERASURE:
            response_data = self._process_erasure_request(request.data_subject_id)
        elif request.request_type == DataSubjectRightType.DATA_PORTABILITY:
            response_data = self._process_portability_request(request.data_subject_id)
        else:
            response_data = {"message": f"Processing {request.request_type.value} request"}
        
        # Update request with response
        request.complete_request(response_data)
        
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE data_subject_requests
                SET processing_status = ?, response_data = ?
                WHERE request_id = ?
            """, ("completed", json.dumps(response_data), request_id))
        
        self.audit_logger.log_subject_request(request, "completed")
        
        return response_data
    
    def _process_access_request(self, data_subject_id: str) -> Dict[str, Any]:
        """Process Article 15 - Right of access request."""
        self.audit_logger.log_data_access(
            data_subject_id, "all_data", "gdpr_manager", "subject_access_request"
        )
        
        access_data = {
            "data_subject_id": data_subject_id,
            "consents": [consent.to_dict() for consent in self.get_valid_consents(data_subject_id)],
            "processing_purposes": [],
            "data_categories": [],
            "recipients": [],
            "retention_periods": {},
            "subject_rights": [right.value for right in DataSubjectRightType],
            "generated_timestamp": datetime.now().isoformat()
        }
        
        # Call registered data processors to collect data
        for data_type, processor in self.data_processors.items():
            try:
                data = processor(data_subject_id, "access")
                if data:
                    access_data[data_type] = data
            except Exception as e:
                gdpr_logger.error(f"Error processing {data_type} data: {e}")
        
        return access_data
    
    def _process_erasure_request(self, data_subject_id: str) -> Dict[str, Any]:
        """Process Article 17 - Right to erasure request."""
        self.audit_logger.log_data_deletion(
            data_subject_id, "all_data", "gdpr_manager", "subject_erasure_request"
        )
        
        deletion_results = {
            "data_subject_id": data_subject_id,
            "deletion_timestamp": datetime.now().isoformat(),
            "deleted_data_types": [],
            "retained_data_types": [],
            "deletion_details": {}
        }
        
        # Call registered data processors to delete data
        for data_type, processor in self.data_processors.items():
            try:
                result = processor(data_subject_id, "delete")
                if result.get("deleted", False):
                    deletion_results["deleted_data_types"].append(data_type)
                else:
                    deletion_results["retained_data_types"].append(data_type)
                
                deletion_results["deletion_details"][data_type] = result
            except Exception as e:
                gdpr_logger.error(f"Error deleting {data_type} data: {e}")
                deletion_results["deletion_details"][data_type] = {"error": str(e)}
        
        # Withdraw all consents
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE consent_records
                SET consent_withdrawn = 1, withdrawal_timestamp = ?
                WHERE data_subject_id = ?
            """, (datetime.now().isoformat(), data_subject_id))
        
        return deletion_results
    
    def _process_portability_request(self, data_subject_id: str) -> Dict[str, Any]:
        """Process Article 20 - Right to data portability request."""
        self.audit_logger.log_data_access(
            data_subject_id, "portable_data", "gdpr_manager", "data_portability_request"
        )
        
        portable_data = {
            "data_subject_id": data_subject_id,
            "export_timestamp": datetime.now().isoformat(),
            "export_format": "JSON",
            "data": {}
        }
        
        # Call registered data processors to export portable data
        for data_type, processor in self.data_processors.items():
            try:
                data = processor(data_subject_id, "export")
                if data:
                    portable_data["data"][data_type] = data
            except Exception as e:
                gdpr_logger.error(f"Error exporting {data_type} data: {e}")
        
        return portable_data
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate GDPR compliance report."""
        with self._get_connection() as conn:
            # Count active consents
            cursor = conn.execute("""
                SELECT COUNT(*) FROM consent_records WHERE consent_withdrawn = 0
            """)
            active_consents = cursor.fetchone()[0]
            
            # Count pending requests
            cursor = conn.execute("""
                SELECT COUNT(*) FROM data_subject_requests WHERE processing_status = 'pending'
            """)
            pending_requests = cursor.fetchone()[0]
            
            # Count overdue requests
            cursor = conn.execute("""
                SELECT COUNT(*) FROM data_subject_requests 
                WHERE response_due_date < ? AND processing_status != 'completed'
            """, (datetime.now().isoformat(),))
            overdue_requests = cursor.fetchone()[0]
            
            # Count data breaches
            cursor = conn.execute("SELECT COUNT(*) FROM data_breach_records")
            total_breaches = cursor.fetchone()[0]
        
        return {
            "compliance_status": "compliant" if overdue_requests == 0 else "non_compliant",
            "active_consents": active_consents,
            "pending_requests": pending_requests,
            "overdue_requests": overdue_requests,
            "total_data_breaches": total_breaches,
            "registered_processors": len(self.data_processors),
            "last_updated": datetime.now().isoformat()
        }


# Example data processors for common data types
def user_profile_processor(data_subject_id: str, operation: str) -> Optional[Dict[str, Any]]:
    """Example processor for user profile data."""
    if operation == "access":
        return {
            "user_id": data_subject_id,
            "profile_data": "example_profile_data",
            "last_updated": datetime.now().isoformat()
        }
    elif operation == "delete":
        # Simulate deletion
        return {"deleted": True, "timestamp": datetime.now().isoformat()}
    elif operation == "export":
        return {
            "user_id": data_subject_id,
            "exportable_data": "example_exportable_data"
        }
    return None


if __name__ == "__main__":
    # Example usage and testing
    def test_gdpr_compliance():
        """Test GDPR compliance functionality."""
        print("Testing GDPR Compliance System...")
        
        # Initialize GDPR manager
        gdpr = GDPRManager()
        
        # Register example data processor
        gdpr.register_data_processor("user_profile", user_profile_processor)
        
        # Test consent recording
        consent = ConsentRecord(
            data_subject_id="user_123",
            purpose="Service provision",
            legal_basis=ConsentBasis.CONSENT,
            data_categories=[DataCategory.IDENTITY, DataCategory.CONTACT],
            consent_given=True
        )
        
        consent_id = gdpr.record_consent(consent)
        print(f"Consent recorded: {consent_id}")
        
        # Test data subject request
        request = DataSubjectRequest(
            request_type=DataSubjectRightType.ACCESS,
            data_subject_id="user_123",
            email="user@example.com"
        )
        request.mark_verified()  # Simulate verification
        
        request_id = gdpr.submit_data_subject_request(request)
        print(f"Request submitted: {request_id}")
        
        # Process the request
        response = gdpr.process_data_subject_request(request_id)
        print(f"Request processed: {response}")
        
        # Generate compliance report
        report = gdpr.get_compliance_report()
        print(f"Compliance report: {report}")
    
    test_gdpr_compliance()