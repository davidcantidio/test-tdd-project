"""
Duration System Module

This module provides duration calculations, security utilities, and data protection features
for the TDD project template.

Key Components:
- Duration Calculator: Business day calculations and duration formatting
- Security Utilities: Data protection, serialization security, GDPR compliance
- Database Security: Secure database operations and query builders
- Rate Limiting: Request rate limiting and DoS protection
- Cache Management: LRU cache with security features
- JSON Handling: Secure JSON operations with validation
"""

__version__ = "0.1.0"

# Core duration utilities
from .duration_calculator import DurationCalculator
from .duration_formatter import DurationFormatter
from .business_calendar import BusinessCalendar

# Security utilities
from .json_security import JSONSecurityValidator
from .secure_serialization import SecureSerializer
from .gdpr_compliance import GDPRCompliance

# Database utilities
from .secure_database import SecureDatabaseManager
from .database_transactions import TransactionManager

# Performance utilities
from .cache_fix import OptimizedCache
from .rate_limiter import RateLimiter

__all__ = [
    "DurationCalculator",
    "DurationFormatter", 
    "BusinessCalendar",
    "JSONSecurityValidator",
    "SecureSerializer",
    "GDPRCompliance",
    "SecureDatabaseManager",
    "TransactionManager",
    "OptimizedCache",
    "RateLimiter",
]