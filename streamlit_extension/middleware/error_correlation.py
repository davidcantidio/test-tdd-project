"""Error correlation and pattern analysis helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List


@dataclass
class ErrorEvent:
    timestamp: datetime
    message: str


@dataclass
class ErrorPattern:
    pattern_type: str
    frequency: int
    time_span: timedelta
    root_cause: str
    impact_scope: int


class ErrorPatternAnalyzer:
    """Analyze error patterns based on correlation IDs."""

    def __init__(self) -> None:
        self.error_store: Dict[str, List[ErrorEvent]] = {}

    def record_error(self, correlation_id: str, event: ErrorEvent) -> None:
        self.error_store.setdefault(correlation_id, []).append(event)

    def get_correlated_errors(self, correlation_id: str) -> List[ErrorEvent]:
        return self.error_store.get(correlation_id, [])

    def detect_pattern_type(self, related_errors: List[ErrorEvent]) -> str:
        return "repeated" if len(related_errors) > 1 else "single"

    def calculate_time_span(self, related_errors: List[ErrorEvent]) -> timedelta:
        if len(related_errors) < 2:
            return timedelta(0)
        return related_errors[-1].timestamp - related_errors[0].timestamp

    def identify_root_cause(self, related_errors: List[ErrorEvent]) -> str:
        return related_errors[0].message if related_errors else ""

    def calculate_impact(self, related_errors: List[ErrorEvent]) -> int:
        return len(related_errors)

    def analyze_error_patterns(self, correlation_id: str) -> ErrorPattern:
        related_errors = self.get_correlated_errors(correlation_id)
        return ErrorPattern(
            pattern_type=self.detect_pattern_type(related_errors),
            frequency=len(related_errors),
            time_span=self.calculate_time_span(related_errors),
            root_cause=self.identify_root_cause(related_errors),
            impact_scope=self.calculate_impact(related_errors),
        )


class CrossSystemCorrelator:
    """Correlate errors across different systems using correlation IDs."""

    def __init__(self, analyzer: ErrorPatternAnalyzer | None = None) -> None:
        self.analyzer = analyzer or ErrorPatternAnalyzer()

    def correlate_distributed_errors(self, correlation_id: str) -> List[ErrorEvent]:
        return self.analyzer.get_correlated_errors(correlation_id)

    def collect_all_events(self, correlation_id: str) -> List[ErrorEvent]:
        return self.analyzer.get_correlated_errors(correlation_id)

    def build_error_timeline(self, correlation_id: str) -> List[ErrorEvent]:
        events = self.collect_all_events(correlation_id)
        return sorted(events, key=lambda x: x.timestamp)