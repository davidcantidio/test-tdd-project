from datetime import datetime
import time
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from streamlit_extension.middleware.context_manager import UserContext
from streamlit_extension.utils.enhanced_recovery import (
    AuthenticationError,
    AuthenticationRecoveryStrategy,
    DatabaseRecoveryStrategy,
    OperationalError,
    RecoveryEngine,
    ValidationError,
    ValidationRecoveryStrategy,
)


def create_context(user_id: str = "user") -> UserContext:
    return UserContext(
        user_id=user_id,
        session_id="sess",
        request_id="req",
        correlation_id="cid",
        ip_address="0.0.0.0",
        user_agent="test",
        timestamp=datetime.now(),
        permissions=[],
        preferences={},
        performance_budget={},
    )


def test_multi_strategy_recovery() -> None:
    engine = RecoveryEngine([DatabaseRecoveryStrategy(), ValidationRecoveryStrategy()])
    context = create_context()
    result = engine.attempt_recovery(ValidationError("bad"), context)
    assert result.success and result.result == "validated"


def test_context_aware_recovery() -> None:
    engine = RecoveryEngine([AuthenticationRecoveryStrategy()])
    context = create_context(user_id="user123")
    result = engine.attempt_recovery(AuthenticationError("auth"), context)
    assert result.success and result.result == "auth_recovered"


def test_recovery_performance_impact() -> None:
    engine = RecoveryEngine([DatabaseRecoveryStrategy()])
    context = create_context()
    start = time.time()
    engine.attempt_recovery(OperationalError("db"), context)
    duration = time.time() - start
    assert duration < 0.5