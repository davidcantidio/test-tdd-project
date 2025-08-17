"""Storage backends for rate limiting state."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional
from collections import deque
import sqlite3

try:  # pragma: no cover - optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class MemoryRateLimitStorage:
    """In-memory storage suitable for tests and single process usage."""

    def __init__(self) -> None:
        # key -> {"tokens": float, "last_refill": float, "timestamps": deque, "window_start": int|None, "counter": int}
        self.data: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()

    def get_bucket_state(self, key: str) -> Dict[str, Any]:
        with self.lock:
            return self.data.get(key, {"tokens": 0.0, "last_refill": time.time()})

    def update_bucket_state(self, key: str, *, tokens: float, last_refill: float) -> None:
        with self.lock:
            state = self.data.setdefault(key, {})
            state["tokens"] = tokens
            state["last_refill"] = last_refill

    def increment(self, key: str, timestamp: float) -> int:
        """Increment sliding window counter and return current count."""
        with self.lock:
            window = self.data.setdefault(key, {"timestamps": deque()})["timestamps"]
            window.append(timestamp)
            return len(window)

    def prune(self, key: str, cutoff: float) -> None:
        with self.lock:
            window = self.data.setdefault(key, {"timestamps": deque()})["timestamps"]
            while window and window[0] <= cutoff:
                window.popleft()

    def get_window_count(self, key: str, cutoff: float) -> int:
        """Count items in window after pruning without incrementing."""
        with self.lock:
            window = self.data.setdefault(key, {"timestamps": deque()})["timestamps"]
            while window and window[0] <= cutoff:
                window.popleft()
            return len(window)

    def get_counter_state(self, key: str) -> Dict[str, Any]:
        """Return {'window_start': int|None, 'counter': int} for fixed window."""
        with self.lock:
            st = self.data.setdefault(key, {})
            if "window_start" not in st:
                st["window_start"] = None
            if "counter" not in st:
                st["counter"] = 0
            return {"window_start": st["window_start"], "counter": st["counter"]}

    def update_counter_state(self, key: str, *, window_start: Optional[int], counter: int) -> None:
        with self.lock:
            st = self.data.setdefault(key, {})
            st["window_start"] = window_start
            st["counter"] = counter


class RedisRateLimitStorage:
    """Redis-backed storage for rate limiting."""

    def __init__(self, client: "redis.Redis") -> None:  # type: ignore[name-defined]
        if redis is None:
            raise RuntimeError("redis-py não está instalado. `pip install redis`")
        self.r = client

    def get_bucket_state(self, key: str) -> Dict[str, Any]:
        h = self.r.hgetall(f"rl:bucket:{key}")
        if not h:
            return {"tokens": 0.0, "last_refill": time.time()}
        tokens = float(h.get(b"tokens", b"0") or 0)
        last_refill = float(h.get(b"last_refill", b"0") or 0) or time.time()
        return {"tokens": tokens, "last_refill": last_refill}

    def update_bucket_state(self, key: str, *, tokens: float, last_refill: float) -> None:
        self.r.hset(f"rl:bucket:{key}", mapping={"tokens": tokens, "last_refill": last_refill})

    def increment(self, key: str, timestamp: float) -> int:
        zkey = f"rl:win:{key}"
        self.r.zadd(zkey, {timestamp: timestamp})
        return int(self.r.zcard(zkey))

    def prune(self, key: str, cutoff: float) -> None:
        zkey = f"rl:win:{key}"
        self.r.zremrangebyscore(zkey, "-inf", cutoff)

    def get_window_count(self, key: str, cutoff: float) -> int:
        zkey = f"rl:win:{key}"
        self.prune(key, cutoff)
        return int(self.r.zcard(zkey))

    def get_counter_state(self, key: str) -> Dict[str, Any]:
        h = self.r.hgetall(f"rl:fixed:{key}")
        if not h:
            return {"window_start": None, "counter": 0}
        ws = h.get(b"window_start")
        window_start = int(ws) if ws is not None else None
        counter = int(h.get(b"counter", b"0") or 0)
        return {"window_start": window_start, "counter": counter}

    def update_counter_state(self, key: str, *, window_start: Optional[int], counter: int) -> None:
        self.r.hset(
            f"rl:fixed:{key}",
            mapping={"window_start": window_start if window_start is not None else -1, "counter": counter},
        )


class SQLiteRateLimitStorage:
    """SQLite-backed storage for rate limiting."""

    def __init__(self, path: str = "rate_limit.db") -> None:
        self.path = path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rl_buckets(
                    key TEXT PRIMARY KEY,
                    tokens REAL NOT NULL,
                    last_refill REAL NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rl_windows(
                    key TEXT NOT NULL,
                    ts REAL NOT NULL
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_rl_windows_key_ts ON rl_windows(key, ts)"
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rl_fixed(
                    key TEXT PRIMARY KEY,
                    window_start INTEGER,
                    counter INTEGER NOT NULL
                )
                """
            )

    def get_bucket_state(self, key: str) -> Dict[str, Any]:
        with self._lock, self._conn:
            cur = self._conn.execute("SELECT tokens, last_refill FROM rl_buckets WHERE key=?", (key,))
            row = cur.fetchone()
            if not row:
                return {"tokens": 0.0, "last_refill": time.time()}
            return {"tokens": float(row[0]), "last_refill": float(row[1])}

    def update_bucket_state(self, key: str, *, tokens: float, last_refill: float) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO rl_buckets(key, tokens, last_refill) VALUES(?,?,?)
                ON CONFLICT(key) DO UPDATE SET tokens=excluded.tokens, last_refill=excluded.last_refill
                """,
                (key, tokens, last_refill),
            )

    def increment(self, key: str, timestamp: float) -> int:
        with self._lock, self._conn:
            self._conn.execute("INSERT INTO rl_windows(key, ts) VALUES(?,?)", (key, float(timestamp)))
            cur = self._conn.execute("SELECT COUNT(*) FROM rl_windows WHERE key=?", (key,))
            return int(cur.fetchone()[0])

    def prune(self, key: str, cutoff: float) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM rl_windows WHERE key=? AND ts<=?", (key, float(cutoff)))

    def get_window_count(self, key: str, cutoff: float) -> int:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM rl_windows WHERE key=? AND ts<=?", (key, float(cutoff)))
            cur = self._conn.execute("SELECT COUNT(*) FROM rl_windows WHERE key=?", (key,))
            return int(cur.fetchone()[0])

    def get_counter_state(self, key: str) -> Dict[str, Any]:
        with self._lock, self._conn:
            cur = self._conn.execute("SELECT window_start, counter FROM rl_fixed WHERE key=?", (key,))
            row = cur.fetchone()
            if not row:
                return {"window_start": None, "counter": 0}
            ws = int(row[0]) if row[0] is not None else None
            return {"window_start": ws, "counter": int(row[1] or 0)}

    def update_counter_state(self, key: str, *, window_start: Optional[int], counter: int) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO rl_fixed(key, window_start, counter) VALUES(?,?,?)
                ON CONFLICT(key) DO UPDATE SET window_start=excluded.window_start, counter=excluded.counter
                """,
                (key, window_start, counter),
            )

