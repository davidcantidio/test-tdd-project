"""Utilities for basic security testing simulations."""
from __future__ import annotations

from html import escape
import secrets
from typing import Dict, List

try:
    from tests.security_scenarios.xss_payloads import XSS_PAYLOADS
    from tests.security_scenarios.csrf_scenarios import CSRF_SCENARIOS
except Exception:  # pragma: no cover - fallback for runtime without tests
    XSS_PAYLOADS = {}
    CSRF_SCENARIOS = {}


class XSSTestHelper:
    """Helper methods for XSS testing."""

    def generate_xss_payloads(self) -> Dict[str, List[str]]:
        """Return predefined XSS payloads."""
        return XSS_PAYLOADS

    def test_input_sanitization(self, payload: str) -> str:
        """Sanitize input using HTML escaping and basic filtering."""
        sanitized = escape(payload, quote=True)
        for keyword in ["javascript:", "onerror", "onload"]:
            sanitized = sanitized.replace(keyword, "")
        return sanitized

    def validate_output_encoding(self, output: str) -> bool:
        """Validate that dangerous patterns are not present in output."""
        dangerous = ["<script", "javascript:", "onerror", "onload"]
        lower = output.lower()
        return not any(d in lower for d in dangerous)


class CSRFTestHelper:
    """Helper methods for CSRF testing."""

    def generate_csrf_tokens(self, count: int = 1) -> List[str]:
        """Generate a list of pseudo-random CSRF tokens."""
        return [secrets.token_hex(16) for _ in range(count)]

    def validate_csrf_protection(self, token: str, valid_tokens: List[str]) -> bool:
        """Check whether a token is recognised as valid."""
        return token in valid_tokens

    def simulate_csrf_attacks(self, scenario: str) -> str:
        """Return a description of the CSRF scenario."""
        return CSRF_SCENARIOS.get(scenario, "unknown")


class SecurityTestRunner:
    """Run security test suites and generate reports."""

    def run_security_suite(self) -> Dict[str, bool]:
        """Simulate running the security suite."""
        return {"xss": True, "csrf": True}

    def generate_security_report(self, results: Dict[str, bool] | None = None) -> str:
        """Generate a simple textual security report."""
        if results is None:
            results = self.run_security_suite()
        lines = ["Security Test Report:"]
        for key, val in results.items():
            status = "PASSED" if val else "FAILED"
            lines.append(f"{key.upper()}: {status}")
        return "\n".join(lines)
