#!/usr/bin/env python3
"""
🔗 GDPR Integration Utilities

Integration layer connecting GDPR compliance with the existing Duration System framework.
Provides decorators and utilities for automatic GDPR compliance tracking.

Usage:
    from duration_system.gdpr_integration import gdpr_tracked, init_gdpr_for_framework
    
    # Initialize GDPR for the framework
    init_gdpr_for_framework()
    
    # Track data access automatically
    @gdpr_tracked("user_profile", data_categories=["identity", "contact"])
    def get_user_profile(user_id):
        return {"name": "John", "email": "john@example.com"}
"""

import functools
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path

try:
    from .gdpr_compliance import (
        GDPRManager, ConsentRecord, DataSubjectRequest, 
        DataCategory, ConsentBasis, DataSubjectRightType
    )
    GDPR_AVAILABLE = True
except ImportError:
    GDPR_AVAILABLE = False

# Global GDPR manager instance
_gdpr_manager: Optional[GDPRManager] = None

# Integration logger
integration_logger = logging.getLogger('gdpr.integration')
integration_logger.setLevel(logging.INFO)


def init_gdpr_for_framework(db_path: str = "framework_gdpr.db", 
                           audit_log: str = "framework_gdpr_audit.log") -> Optional[GDPRManager]:
    """
    Initialize GDPR compliance for the Duration System framework.
    
    Args:
        db_path: Path to GDPR compliance database
        audit_log: Path to GDPR audit log file
        
    Returns:
        GDPRManager instance or None if GDPR not available
    """
    global _gdpr_manager
    
    if not GDPR_AVAILABLE:
        integration_logger.warning("GDPR compliance module not available")
        return None
    
    try:
        _gdpr_manager = GDPRManager(db_path, audit_log)
        
        # Register framework-specific data processors
        _register_framework_processors()
        
        integration_logger.info("GDPR compliance initialized for Duration System framework")
        return _gdpr_manager
        
    except Exception as e:
        integration_logger.error(f"Failed to initialize GDPR compliance: {e}")
        return None


def get_gdpr_manager() -> Optional[GDPRManager]:
    """Get the global GDPR manager instance."""
    return _gdpr_manager


def _register_framework_processors():
    """Register data processors for Duration System framework data types."""
    if not _gdpr_manager:
        return
    
    # User profile processor
    def user_profile_processor(data_subject_id: str, operation: str) -> Optional[Dict[str, Any]]:
        """Process user profile data for GDPR requests."""
        if operation == "access":
            # In a real implementation, this would query the actual user database
            return {
                "user_id": data_subject_id,
                "profile_data": f"Profile data for {data_subject_id}",
                "last_accessed": datetime.now().isoformat()
            }
        elif operation == "delete":
            # In a real implementation, this would delete user data
            integration_logger.info(f"Deleting user profile data for {data_subject_id}")
            return {"deleted": True, "data_type": "user_profile", "timestamp": datetime.now().isoformat()}
        elif operation == "export":
            return {
                "user_id": data_subject_id,
                "exportable_profile": f"Exportable data for {data_subject_id}"
            }
        return None
    
    # Epic data processor
    def epic_data_processor(data_subject_id: str, operation: str) -> Optional[Dict[str, Any]]:
        """Process epic/task data for GDPR requests."""
        if operation == "access":
            return {
                "user_id": data_subject_id,
                "epics": f"Epic data for {data_subject_id}",
                "tasks": f"Task data for {data_subject_id}"
            }
        elif operation == "delete":
            integration_logger.info(f"Deleting epic/task data for {data_subject_id}")
            return {"deleted": True, "data_type": "epic_task_data", "timestamp": datetime.now().isoformat()}
        elif operation == "export":
            return {
                "user_id": data_subject_id,
                "epic_exports": f"Exportable epic/task data for {data_subject_id}"
            }
        return None
    
    # Time tracking processor
    def time_tracking_processor(data_subject_id: str, operation: str) -> Optional[Dict[str, Any]]:
        """Process time tracking data for GDPR requests."""
        if operation == "access":
            return {
                "user_id": data_subject_id,
                "work_sessions": f"Work session data for {data_subject_id}",
                "time_entries": f"Time tracking data for {data_subject_id}"
            }
        elif operation == "delete":
            integration_logger.info(f"Deleting time tracking data for {data_subject_id}")
            return {"deleted": True, "data_type": "time_tracking", "timestamp": datetime.now().isoformat()}
        elif operation == "export":
            return {
                "user_id": data_subject_id,
                "time_exports": f"Exportable time data for {data_subject_id}"
            }
        return None
    
    # Register processors
    _gdpr_manager.register_data_processor("user_profile", user_profile_processor)
    _gdpr_manager.register_data_processor("epic_task_data", epic_data_processor)
    _gdpr_manager.register_data_processor("time_tracking", time_tracking_processor)
    
    integration_logger.info("Framework data processors registered with GDPR system")


def gdpr_tracked(data_type: str, 
                data_categories: Optional[List[str]] = None,
                requires_consent: bool = True,
                audit_access: bool = True):
    """
    Decorator to automatically track data access for GDPR compliance.
    
    Args:
        data_type: Type of data being accessed
        data_categories: Categories of personal data
        requires_consent: Whether valid consent is required
        audit_access: Whether to log data access
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not _gdpr_manager:
                # GDPR not initialized, just execute function
                return func(*args, **kwargs)
            
            # Extract user/data subject ID from arguments
            user_id = _extract_user_id(args, kwargs)
            if not user_id:
                # No user ID found, just execute function
                return func(*args, **kwargs)
            
            try:
                # Check consent if required
                if requires_consent:
                    valid_consents = _gdpr_manager.get_valid_consents(user_id)
                    
                    # Convert string categories to DataCategory enums
                    required_categories = []
                    if data_categories:
                        for cat in data_categories:
                            try:
                                required_categories.append(DataCategory(cat.lower()))
                            except ValueError:
                                integration_logger.warning(f"Unknown data category: {cat}")
                    
                    # Check if we have consent for the required categories
                    has_consent = False
                    for consent in valid_consents:
                        if any(cat in consent.data_categories for cat in required_categories):
                            has_consent = True
                            break
                    
                    if not has_consent and required_categories:
                        integration_logger.warning(
                            f"No valid consent for {data_type} access by user {user_id}"
                        )
                        # In a real implementation, you might want to raise an exception
                        # or redirect to a consent page
                
                # Log data access if enabled
                if audit_access:
                    _gdpr_manager.audit_logger.log_data_access(
                        data_subject_id=user_id,
                        data_type=data_type,
                        accessed_by=func.__name__,
                        purpose="framework_operation"
                    )
                
                # Execute the original function
                result = func(*args, **kwargs)
                
                return result
                
            except Exception as e:
                integration_logger.error(f"GDPR tracking error in {func.__name__}: {e}")
                # Don't let GDPR errors break the application
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def _extract_user_id(args, kwargs) -> Optional[str]:
    """Extract user ID from function arguments."""
    # Check common parameter names
    user_id_params = ['user_id', 'data_subject_id', 'subject_id', 'id']
    
    for param in user_id_params:
        if param in kwargs:
            return str(kwargs[param])
    
    # Check if first argument looks like a user ID
    if args and len(args) > 0:
        first_arg = args[0]
        if isinstance(first_arg, (str, int)) and str(first_arg).startswith(('user_', 'subject_')):
            return str(first_arg)
    
    return None


def record_framework_consent(user_id: str, 
                            purpose: str = "Framework usage",
                            data_categories: Optional[List[str]] = None,
                            legal_basis: str = "consent") -> Optional[str]:
    """
    Record user consent for framework usage.
    
    Args:
        user_id: User identifier
        purpose: Purpose of data processing
        data_categories: Categories of data being processed
        legal_basis: Legal basis for processing
        
    Returns:
        Consent ID or None if GDPR not available
    """
    if not _gdpr_manager:
        return None
    
    try:
        # Convert string categories to DataCategory enums
        categories = []
        if data_categories:
            for cat in data_categories:
                try:
                    categories.append(DataCategory(cat.lower()))
                except ValueError:
                    integration_logger.warning(f"Unknown data category: {cat}")
        
        # Create consent record
        consent = ConsentRecord(
            data_subject_id=user_id,
            purpose=purpose,
            legal_basis=ConsentBasis(legal_basis.lower()),
            data_categories=categories,
            consent_given=True
        )
        
        consent_id = _gdpr_manager.record_consent(consent)
        integration_logger.info(f"Consent recorded for user {user_id}: {consent_id}")
        
        return consent_id
        
    except Exception as e:
        integration_logger.error(f"Failed to record consent for {user_id}: {e}")
        return None


def process_framework_data_request(request_type: str,
                                 user_id: str,
                                 email: str) -> Optional[Dict[str, Any]]:
    """
    Process a data subject request for framework data.
    
    Args:
        request_type: Type of request (access, erasure, portability, etc.)
        user_id: User identifier
        email: User email for verification
        
    Returns:
        Request response or None if GDPR not available
    """
    if not _gdpr_manager:
        return None
    
    try:
        # Map string request type to enum
        request_type_map = {
            "access": DataSubjectRightType.ACCESS,
            "erasure": DataSubjectRightType.ERASURE,
            "delete": DataSubjectRightType.ERASURE,
            "portability": DataSubjectRightType.DATA_PORTABILITY,
            "export": DataSubjectRightType.DATA_PORTABILITY
        }
        
        if request_type.lower() not in request_type_map:
            integration_logger.error(f"Unknown request type: {request_type}")
            return None
        
        # Create and submit request
        request = DataSubjectRequest(
            request_type=request_type_map[request_type.lower()],
            data_subject_id=user_id,
            email=email
        )
        
        # Auto-verify for framework integration (in production, this would require proper verification)
        request.mark_verified()
        
        request_id = _gdpr_manager.submit_data_subject_request(request)
        response = _gdpr_manager.process_data_subject_request(request_id)
        
        integration_logger.info(f"Processed {request_type} request for user {user_id}")
        return response
        
    except Exception as e:
        integration_logger.error(f"Failed to process {request_type} request for {user_id}: {e}")
        return None


def get_framework_compliance_status() -> Dict[str, Any]:
    """
    Get GDPR compliance status for the framework.
    
    Returns:
        Compliance status dictionary
    """
    if not _gdpr_manager:
        return {"gdpr_available": False, "status": "not_initialized"}
    
    try:
        base_status = _gdpr_manager.get_compliance_report()
        
        # Add framework-specific information
        framework_status = {
            "gdpr_available": True,
            "framework_integration": "active",
            "registered_processors": len(_gdpr_manager.data_processors),
            "audit_logging": "enabled",
            **base_status
        }
        
        return framework_status
        
    except Exception as e:
        integration_logger.error(f"Failed to get compliance status: {e}")
        return {"gdpr_available": True, "status": "error", "error": str(e)}


# Example usage decorators for common framework operations
def track_user_access(func):
    """Shorthand decorator for tracking user data access."""
    return gdpr_tracked("user_data", ["identity", "contact"])(func)


def track_epic_access(func):
    """Shorthand decorator for tracking epic/task data access."""
    return gdpr_tracked("epic_task_data", ["behavioral", "professional"])(func)


def track_time_access(func):
    """Shorthand decorator for tracking time tracking data access."""
    return gdpr_tracked("time_tracking", ["behavioral", "professional"])(func)


if __name__ == "__main__":
    # Example usage
    print("Testing GDPR Integration...")
    
    # Initialize GDPR
    manager = init_gdpr_for_framework()
    if manager:
        print("✓ GDPR initialized successfully")
        
        # Record consent
        consent_id = record_framework_consent(
            user_id="test_user_123",
            purpose="Framework testing",
            data_categories=["identity", "contact", "behavioral"]
        )
        print(f"✓ Consent recorded: {consent_id}")
        
        # Test tracked function
        @gdpr_tracked("test_data", ["identity"])
        def get_test_data(user_id):
            return {"test": f"data for {user_id}"}
        
        result = get_test_data("test_user_123")
        print(f"✓ Tracked function executed: {result}")
        
        # Get compliance status
        status = get_framework_compliance_status()
        print(f"✓ Compliance status: {status['compliance_status']}")
        
    else:
        print("✗ GDPR initialization failed")