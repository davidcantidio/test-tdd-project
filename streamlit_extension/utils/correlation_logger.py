"""Correlation-aware structured logging."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..middleware.context_manager import UserContext
from .enhanced_recovery import RecoveryResult


class CorrelationLogger:
    """Log errors with correlation and context information."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.structured_logger = logger or logging.getLogger("correlation")

    def build_error_chain(self, error: Exception) -> List[str]:
        chain: List[str] = []
        current = error
        while current is not None:
            chain.append(type(current).__name__)
            current = current.__cause__
        return chain

    def trace_user_journey(self, context: UserContext) -> Dict[str, Any]:
        return {"user_id": context.user_id, "session_id": context.session_id}

    def capture_system_state(self) -> Dict[str, Any]:
        return {"timestamp": datetime.utcnow().isoformat()}

    def log_recovery_actions(self, recovery_result: Optional[RecoveryResult]) -> Dict[str, Any]:
        if recovery_result is None:
            return {}
        return {"success": recovery_result.success}

    def log_error_with_correlation(
        self, error: Exception, context: UserContext, recovery_result: Optional[RecoveryResult] = None
    ) -> Dict[str, Any]:
        log_entry = {
            "correlation_id": context.correlation_id,
            "error_chain": self.build_error_chain(error),
            "user_journey": self.trace_user_journey(context),
            "system_state": self.capture_system_state(),
            "recovery_actions": self.log_recovery_actions(recovery_result),
        }
        self.structured_logger.error(log_entry)
        return log_entry