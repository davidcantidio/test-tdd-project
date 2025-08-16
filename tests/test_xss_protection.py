"""
XSS Protection Test Suite
Tests various inputs for XSS vulnerability handling.
"""

from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from streamlit_extension.utils.security import sanitize_input


class TestXSSProtection:
    """XSS protection test cases"""

    @pytest.mark.parametrize("xss_payload", [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "' OR 1=1 --",
        "<iframe src=javascript:alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<style>@import'javascript:alert(\"XSS\")';</style>",
        "<div onclick=alert('XSS')>Click me</div>",
        "<a href=javascript:alert('XSS')>Click</a>"
    ])
    def test_sanitize_input_xss_payloads(self, xss_payload):
        """Test sanitization of various XSS payloads"""
        sanitized = sanitize_input(xss_payload)
        assert "<script>" not in sanitized

    def test_client_form_xss_protection(self):
        """Test XSS protection in client form fields"""
        xss_data = {
            "name": "<script>alert('name_xss')</script>",
            "description": "<img src=x onerror=alert('desc_xss')>",
            "industry": "javascript:alert('industry_xss')",
            "primary_contact_name": "<svg onload=alert('contact_xss')>"
        }
        for value in xss_data.values():
            sanitized = sanitize_input(value)
            assert "<script>" not in sanitized

    def test_project_form_xss_protection(self):
        """Test XSS protection in project form fields"""
        xss_data = {
            "name": "<script>alert('proj_xss')</script>",
            "description": "<iframe src=javascript:alert('XSS')>",
            "project_type": "<body onload=alert('type_xss')>"
        }
        for value in xss_data.values():
            sanitized = sanitize_input(value)
            assert "<script>" not in sanitized
