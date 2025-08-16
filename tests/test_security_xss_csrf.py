import pytest

from streamlit_extension.utils.security_testing import (
    CSRFTestHelper,
    SecurityTestRunner,
    XSSTestHelper,
)

xss_helper = XSSTestHelper()
csrf_helper = CSRFTestHelper()


class TestSecurityXSS:
    def test_xss_script_injection(self):
        payloads = xss_helper.generate_xss_payloads().get("script", [])
        for payload in payloads:
            sanitized = xss_helper.test_input_sanitization(payload)
            assert "<script" not in sanitized.lower()

    def test_xss_html_injection(self):
        payloads = xss_helper.generate_xss_payloads().get("html", [])
        for payload in payloads:
            sanitized = xss_helper.test_input_sanitization(payload)
            assert "<img" not in sanitized.lower()

    def test_xss_attribute_injection(self):
        payloads = xss_helper.generate_xss_payloads().get("attribute", [])
        for payload in payloads:
            sanitized = xss_helper.test_input_sanitization(payload)
            assert "javascript:" not in sanitized.lower()

    def test_input_sanitization(self):
        payload = "<b>bold</b>"
        sanitized = xss_helper.test_input_sanitization(payload)
        assert sanitized == "&lt;b&gt;bold&lt;/b&gt;"

    def test_output_encoding(self):
        output = "&lt;script&gt;alert('XSS')&lt;/script&gt;"
        assert xss_helper.validate_output_encoding(output)

    def test_xss_client_description_field(self):
        payload = "<script>alert('desc')</script>"
        sanitized = xss_helper.test_input_sanitization(payload)
        assert "<script" not in sanitized.lower()

    def test_xss_project_name_field(self):
        payload = "<img src=x onerror=alert(1)>"
        sanitized = xss_helper.test_input_sanitization(payload)
        assert "<img" not in sanitized.lower()

    def test_xss_reflected_in_error_messages(self):
        payload = "<svg/onload=alert('err')>"
        sanitized = xss_helper.test_input_sanitization(payload)
        assert "onload" not in sanitized.lower()

    def test_xss_stored_in_database(self):
        payload = "<script>alert('db')</script>"
        fake_db = {}
        fake_db["description"] = xss_helper.test_input_sanitization(payload)
        assert "<script" not in fake_db["description"].lower()


class TestSecurityCSRF:
    def test_csrf_form_submission(self):
        tokens = csrf_helper.generate_csrf_tokens()
        token = tokens[0]
        assert csrf_helper.validate_csrf_protection(token, tokens)

    def test_csrf_ajax_requests(self):
        scenario = csrf_helper.simulate_csrf_attacks("ajax")
        assert "ajax" in scenario.lower()

    def test_csrf_token_validation(self):
        tokens = csrf_helper.generate_csrf_tokens(2)
        assert not csrf_helper.validate_csrf_protection("invalid", tokens)

    def test_csrf_client_creation(self):
        scenario = csrf_helper.simulate_csrf_attacks("form")
        assert "form" in scenario.lower()

    def test_csrf_project_update(self):
        scenario = csrf_helper.simulate_csrf_attacks("ajax")
        assert "ajax" in scenario.lower()

    def test_csrf_bulk_operations(self):
        scenario = csrf_helper.simulate_csrf_attacks("json")
        assert "json" in scenario.lower()

    def test_csrf_token_rotation(self):
        tokens1 = csrf_helper.generate_csrf_tokens(3)
        tokens2 = csrf_helper.generate_csrf_tokens(3)
        assert set(tokens1).isdisjoint(tokens2)


def test_security_report_generation():
    runner = SecurityTestRunner()
    report = runner.generate_security_report({"xss": True, "csrf": True})
    assert "XSS: PASSED" in report
