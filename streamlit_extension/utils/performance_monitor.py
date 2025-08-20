"""Lightweight system resource monitoring utilities.

The real project might collect a wide range of metrics. For the purposes
of the tests in this kata we only sample overall CPU and memory usage
using `psutil`. These values are useful to ensure the load tests execute
without exhausting local resources.
"""

from __future__ import annotations

import psutil
from typing import Dict
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


class PerformanceMonitor:
    """Capture simple system resource statistics."""

    def sample(self) -> Dict[str, float]:
        """Return a snapshot of current CPU and memory usage.

        The values are returned as percentages in the range 0-100.
        """

        # interval=None usa o intervalo desde a última chamada sem bloquear.
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        return {"cpu_usage": float(cpu), "memory_usage": float(mem)}