import time
import re
import pytest

from streamlit_extension.middleware.rate_limiting.middleware import RateLimitingMiddleware
from streamlit_extension.middleware.rate_limiting.core import RateLimiter


def _is_int_str(s: str) -> bool:
    return bool(re.fullmatch(r"\d+", str(s)))


def test_headers_present_and_consistent_memory_backend():
    mw = RateLimitingMiddleware()
    req = {"ip": "10.0.0.1", "user_id": "user-1", "tier": "free", "endpoint": "/api/auth/login"}

    for i in range(5):
        res = mw.process_request(req)
        assert res.allowed is True, f"Requisição {i+1} deveria ser permitida"

    res = mw.process_request(req)
    assert res.allowed is False
    assert res.status_code == 429
    assert "X-RateLimit-Limit" in res.headers
    assert "X-RateLimit-Remaining" in res.headers
    assert "X-RateLimit-Reset" in res.headers
    assert _is_int_str(res.headers["X-RateLimit-Limit"])
    assert _is_int_str(res.headers["X-RateLimit-Remaining"])
    assert _is_int_str(res.headers["X-RateLimit-Reset"])
    assert int(res.headers["X-RateLimit-Remaining"]) == 0


def test_headers_for_user_bucket_free_tier_snapshot():
    rl = RateLimiter()
    assert rl.check_user_rate_limit(user_id="u-free", tier="free") is True
    headers = rl.build_rate_limit_headers(ip=None, user_id="u-free", tier="free", endpoint="/not-listed", prefer="user")
    for k in ("X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"):
        assert k in headers
        assert _is_int_str(headers[k])
    limit = int(headers["X-RateLimit-Limit"])
    remaining = int(headers["X-RateLimit-Remaining"])
    assert limit >= 1
    assert 0 <= remaining <= limit


def test_headers_endpoint_fixed_window_with_block_and_reset_approximation(tmp_path):
    from streamlit_extension.middleware.rate_limiting.storage import SQLiteRateLimitStorage

    dbfile = tmp_path / "rate_limit_test.db"
    storage = SQLiteRateLimitStorage(path=str(dbfile))
    mw = RateLimitingMiddleware(config={"rate_limit_storage": storage})

    req = {"ip": "10.0.0.2", "user_id": "user-2", "tier": "free", "endpoint": "/api/bulk/export"}
    res1 = mw.process_request(req)
    assert res1.allowed is True
    assert "X-RateLimit-Limit" in res1.headers
    assert "X-RateLimit-Remaining" in res1.headers
    assert "X-RateLimit-Reset" in res1.headers

    res2 = mw.process_request(req)
    assert res2.allowed is False
    assert res2.status_code == 429
    assert "X-RateLimit-Reset" in res2.headers
    reset = int(res2.headers["X-RateLimit-Reset"])
    assert 0 <= reset <= 10


@pytest.mark.skipif(True, reason="Teste informativo de latência para reset; habilite localmente se quiser validar precisão.")
def test_reset_countdown_behaviour_window_login_precise():
    mw = RateLimitingMiddleware()
    req = {"ip": "10.0.0.3", "user_id": "user-3", "tier": "free", "endpoint": "/api/auth/login"}
    for _ in range(5):
        assert mw.process_request(req).allowed
    res_block = mw.process_request(req)
    assert not res_block.allowed
    reset1 = int(res_block.headers["X-RateLimit-Reset"])
    time.sleep(2)
    res_block2 = mw.process_request(req)
    reset2 = int(res_block2.headers["X-RateLimit-Reset"])
    assert reset2 <= max(0, reset1 - 1)

