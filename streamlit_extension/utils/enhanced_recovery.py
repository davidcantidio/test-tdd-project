"""Enhanced error recovery strategies."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional

from ..middleware.context_manager import UserContext


# Custom exception types used in recovery strategies
class OperationalError(Exception):
    """Simulate database operational error."""


class AuthenticationError(Exception):
    """Simulate authentication error."""


class ValidationError(Exception):
    """Simulate validation error."""


@dataclass
class RecoveryResult:
    success: bool
    result: Optional[Any] = None
    fallback: Optional[Any] = None


class RecoveryStrategy(ABC):
    """Interface for recovery strategies."""

    @abstractmethod
    def can_recover(self, error: Exception, context: UserContext) -> bool:
        ...

    @abstractmethod
    def attempt_recovery(self, error: Exception, context: UserContext) -> RecoveryResult:
        ...

    @abstractmethod
    def get_fallback(self, error: Exception, context: UserContext) -> Any:
        ...


class DatabaseRecoveryStrategy(RecoveryStrategy):
    def can_recover(self, error: Exception, context: UserContext) -> bool:
        return isinstance(error, OperationalError)

    def attempt_recovery(self, error: Exception, context: UserContext) -> RecoveryResult:
        if not self.can_recover(error, context):
            return RecoveryResult(False)
        time.sleep(0.01)  # Simulate retry delay
        return RecoveryResult(True, result="db_recovered")

    def get_fallback(self, error: Exception, context: UserContext) -> Any:
        return "db_fallback"


class AuthenticationRecoveryStrategy(RecoveryStrategy):
    def can_recover(self, error: Exception, context: UserContext) -> bool:
        return isinstance(error, AuthenticationError)

    def attempt_recovery(self, error: Exception, context: UserContext) -> RecoveryResult:
        if not self.can_recover(error, context):
            return RecoveryResult(False)
        if context.user_id:
            return RecoveryResult(True, result="auth_recovered")
        return RecoveryResult(False, fallback="guest")

    def get_fallback(self, error: Exception, context: UserContext) -> Any:
        return "guest"


class ValidationRecoveryStrategy(RecoveryStrategy):
    def can_recover(self, error: Exception, context: UserContext) -> bool:
        return isinstance(error, ValidationError)

    def attempt_recovery(self, error: Exception, context: UserContext) -> RecoveryResult:
        if not self.can_recover(error, context):
            return RecoveryResult(False)
        return RecoveryResult(True, result="validated")

    def get_fallback(self, error: Exception, context: UserContext) -> Any:
        return "validation_fallback"


class RecoveryEngine:
    """Engine that orchestrates multiple recovery strategies."""

    def __init__(self, strategies: Optional[List[RecoveryStrategy]] = None) -> None:
        self.strategies = strategies or []

    def register_strategy(self, strategy: RecoveryStrategy) -> None:
        self.strategies.append(strategy)

    def attempt_recovery(self, error: Exception, context: UserContext) -> RecoveryResult:
        for strategy in self.strategies:
            if strategy.can_recover(error, context):
                result = strategy.attempt_recovery(error, context)
                if result.success:
                    return result
                fallback = strategy.get_fallback(error, context)
                return RecoveryResult(False, fallback=fallback)
        return RecoveryResult(False)