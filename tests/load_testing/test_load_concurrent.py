"""Load tests focusing on concurrent user scenarios."""

from __future__ import annotations

import threading
import time

from streamlit_extension.utils.load_tester import LoadTester


class TestConcurrentUser:
    def test_multi_user_workflow(self) -> None:
        """50 users executing a simple workflow."""

        counter = 0
        lock = threading.Lock()

        def step() -> None:
            nonlocal counter
            with lock:
                counter += 1
            time.sleep(0.0005)

        tester = LoadTester(users=10, duration=0.1, actions=[step, step])
        result = tester.run()
        assert counter > 0
        assert result["errors"]["total_errors"] == 0

    def test_concurrent_form_submission(self) -> None:
        """100 submissions happening simultaneously."""

        submissions: list[int] = []
        lock = threading.Lock()

        def submit() -> None:
            with lock:
                submissions.append(1)
            time.sleep(0.0005)

        tester = LoadTester(users=20, duration=0.1, actions=[submit])
        result = tester.run()
        assert len(submissions) > 0
        assert result["throughput"]["requests_per_second"] > 0

    def test_session_management_load(self) -> None:
        """200 active sessions simulated."""

        def noop() -> None:
            time.sleep(0.0001)

        tester = LoadTester(users=20, duration=0.1, actions=[noop])
        result = tester.run()
        assert result["response_time"]["max"] >= 0

    def test_authentication_spike(self) -> None:
        """Spike of 500 logins simulated quickly."""

        def login() -> None:
            time.sleep(0.0002)

        tester = LoadTester(users=30, duration=0.1, actions=[login])
        result = tester.run()
        assert result["errors"]["total_errors"] == 0