import pytest

from streamlit_extension.middleware.rate_limiting.core import RateLimiter
from streamlit_extension.middleware.rate_limiting.middleware import RateLimitingMiddleware
from streamlit_extension.middleware.rate_limiting.storage import (
    MemoryRateLimitStorage,
    SQLiteRateLimitStorage,
)


def test_memory_storage_basic_flow():
    storage = MemoryRateLimitStorage()
    rl = RateLimiter(storage=storage)
    ip = "192.168.0.10"
    for i in range(100):
        assert rl.check_ip_rate_limit(ip)
    assert rl.check_ip_rate_limit(ip) is False


def test_sqlite_storage_basic_flow(tmp_path):
    dbfile = tmp_path / "rate_limit.db"
    storage = SQLiteRateLimitStorage(path=str(dbfile))
    rl = RateLimiter(storage=storage)
    assert rl.check_endpoint_rate_limit("/api/bulk/run") is True
    assert rl.check_endpoint_rate_limit("/api/bulk/run") is False


def test_sqlite_storage_through_middleware_headers(tmp_path):
    dbfile = tmp_path / "rate_limit2.db"
    storage = SQLiteRateLimitStorage(path=str(dbfile))
    mw = RateLimitingMiddleware(config={"rate_limit_storage": storage})
    req = {"ip": "172.16.0.2", "user_id": "sqlite-u1", "tier": "free", "endpoint": "/api/search"}
    res = mw.process_request(req)
    assert res.allowed is True
    assert "X-RateLimit-Limit" in res.headers
    assert "X-RateLimit-Remaining" in res.headers
    assert "X-RateLimit-Reset" in res.headers


@pytest.mark.skipif(
    pytest.importorskip("redis", reason="Redis client não instalado") is None,
    reason="Redis client ausente",
)
def test_redis_storage_available_if_installed():
    import redis  # type: ignore
    from streamlit_extension.middleware.rate_limiting.storage import RedisRateLimitStorage

    class FakeRedis:
        def __init__(self) -> None:
            self.hashes = {}
            self.zsets = {}

        def hgetall(self, key):
            return self.hashes.get(key, {})

        def hset(self, key, mapping=None, **kwargs):
            m = mapping or kwargs
            h = self.hashes.setdefault(key, {})
            for k, v in m.items():
                h[str(k).encode()] = str(v).encode()

        def zadd(self, key, mapping):
            z = self.zsets.setdefault(key, set())
            for score, member in mapping.items():
                z.add(float(member))

        def zcard(self, key):
            return len(self.zsets.get(key, set()))

        def zremrangebyscore(self, key, min_score, max_score):
            z = self.zsets.setdefault(key, set())
            if max_score == "+inf":
                max_val = float("inf")
            else:
                max_val = float(max_score)
            if min_score == "-inf":
                min_val = float("-inf")
            else:
                min_val = float(min_score)
            self.zsets[key] = {ts for ts in z if not (min_val <= ts <= max_val)}

    fake = FakeRedis()
    storage = RedisRateLimitStorage(fake)
    mw = RateLimitingMiddleware(config={"rate_limit_storage": storage})
    req = {"ip": "10.5.5.5", "user_id": "ru1", "tier": "free", "endpoint": "/api/search"}
    res = mw.process_request(req)
    assert res.allowed is True
    assert "X-RateLimit-Limit" in res.headers
    assert "X-RateLimit-Remaining" in res.headers
    assert "X-RateLimit-Reset" in res.headers

