"""Common CSRF scenarios used for testing."""

CSRF_SCENARIOS = {
    "form": "Forged form submission",
    "ajax": "Cross-origin AJAX request",
    "json": "Malicious JSON payload",
    "get": "GET request with side effects",
    "cross_origin": "Cross-origin request without proper CORS",
}
