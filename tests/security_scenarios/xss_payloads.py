"""Common XSS payloads used for testing."""

XSS_PAYLOADS = {
    "script": [
        "<script>alert('XSS')</script>",
        "<script>console.log('test')</script>",
    ],
    "html": [
        "<img src=x onerror=alert('XSS')>",
        "<div><p>Test</p></div>",
    ],
    "attribute": [
        "<a href='javascript:alert(\"XSS\")'>link</a>",
        "<body onload=alert('XSS')>",
    ],
    "event_handler": [
        "<button onclick='alert(1)'>click</button>",
    ],
    "dom_based": [
        "javascript:eval('alert(1)')",
    ],
}