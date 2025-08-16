"""Utility to monitor resource usage per user."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class UsageAssessment:
    current_usage: int
    quota: int
    percentage: float
    is_fair: bool


class FairUsageMonitor:
    """Track usage for users and compare against quotas."""

    def __init__(self) -> None:
        self.usage: Dict[str, Dict[str, int]] = {}

    def add_usage(self, user_id: str, resource: str, amount: int = 1) -> None:
        self.usage.setdefault(user_id, {})[resource] = self.usage.setdefault(user_id, {}).get(resource, 0) + amount

    def check_fair_usage(self, user_id: str, resource: str, quota: int) -> UsageAssessment:
        current = self.usage.setdefault(user_id, {}).get(resource, 0)
        percentage = (current / quota) * 100 if quota else 0.0
        return UsageAssessment(current, quota, percentage, percentage <= 100)