"""Load tests for basic CRUD style operations.

The tests use the minimal :class:`LoadTester` implementation to exercise
simple in-memory operations under concurrent load. The goal isn't to
stress the system but to verify that the load testing utilities work and
collect metrics as expected.
"""

from __future__ import annotations

import threading
import time
import uuid

from streamlit_extension.utils.load_tester import LoadTester


class TestCRUDLoad:
    def test_create_client_load(self) -> None:
        """100 creations simulated concurrently."""

        data: dict[str, int] = {}
        lock = threading.Lock()

        def create() -> None:
            with lock:
                data[str(uuid.uuid4())] = 1
            time.sleep(0.001)

        tester = LoadTester(users=5, duration=0.2, actions=[create])
        result = tester.run()
        assert result["errors"]["total_errors"] == 0
        assert result["throughput"]["requests_per_second"] > 0

    def test_read_pagination_load(self) -> None:
        """1000 reads with pagination simulation."""

        items = list(range(100))

        def read() -> None:
            _ = items[:10]
            time.sleep(0.0005)

        tester = LoadTester(users=5, duration=0.1, actions=[read])
        result = tester.run()
        assert result["errors"]["total_errors"] == 0
        assert result["response_time"]["p95"] >= 0

    def test_update_concurrent_load(self) -> None:
        """50 updates performed concurrently."""

        data = {i: 0 for i in range(20)}
        lock = threading.Lock()

        def update() -> None:
            with lock:
                data[0] += 1
            time.sleep(0.0005)

        tester = LoadTester(users=10, duration=0.1, actions=[update])
        result = tester.run()
        assert result["errors"]["total_errors"] == 0
        assert data[0] > 0

    def test_delete_cascade_load(self) -> None:
        """Deletes items under concurrent access."""

        data = {i: i for i in range(50)}
        lock = threading.Lock()

        def delete() -> None:
            with lock:
                if data:
                    data.pop(next(iter(data)))
            time.sleep(0.0005)

        tester = LoadTester(users=5, duration=0.1, actions=[delete])
        result = tester.run()
        assert result["errors"]["total_errors"] == 0
        # Ensure some deletions happened
        assert len(data) < 50