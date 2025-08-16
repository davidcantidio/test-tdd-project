"""Stress and spike load testing scenarios."""

from __future__ import annotations

import time

from streamlit_extension.utils.load_tester import LoadTester


class TestStressLoad:
    def test_peak_load(self) -> None:
        """Simulate a short burst of heavy load."""

        def work() -> None:
            time.sleep(0.0003)

        tester = LoadTester(users=40, duration=0.1, actions=[work])
        result = tester.run()
        assert result["throughput"]["requests_per_second"] > 0

    def test_spike_load(self) -> None:
        """Sudden spike in users."""

        def work() -> None:
            time.sleep(0.0002)

        tester = LoadTester(users=50, duration=0.05, actions=[work])
        result = tester.run()
        assert result["errors"]["total_errors"] == 0