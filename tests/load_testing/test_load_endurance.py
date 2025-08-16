"""Endurance (soak) testing scenarios."""

from __future__ import annotations

import time

from streamlit_extension.utils.load_tester import LoadTester


class TestEnduranceLoad:
    def test_endurance_run(self) -> None:
        """Run a slightly longer test to ensure stability over time."""

        def work() -> None:
            time.sleep(0.0005)

        tester = LoadTester(users=5, duration=0.2, actions=[work])
        result = tester.run()
        assert result["errors"]["total_errors"] == 0
        assert result["throughput"]["requests_per_second"] > 0