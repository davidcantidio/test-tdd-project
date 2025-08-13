"""
Duration Formatter Engine for Friendly Duration Descriptions

This module provides formatting of numeric duration values into friendly,
human-readable descriptions that match the format used in real epic data.

Focus: Duration System Implementation - User-friendly duration formatting
"""

from typing import Optional, Tuple, Union, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DurationUnit(Enum):
    """Duration units for formatting"""
    DAYS = "dias"
    WEEKS = "semanas"
    MONTHS = "meses"


class DurationStyle(Enum):
    """Different formatting styles"""
    COMPACT = "compact"          # "1.5d", "2w"
    STANDARD = "standard"        # "1.5 dias", "2 semanas"
    VERBOSE = "verbose"          # "1.5 dias úteis", "2 semanas completas"


class DurationFormattingError(Exception):
    """Custom exception for duration formatting errors"""
    pass


class DurationFormatter:
    """
    Engine for formatting numeric duration values into friendly descriptions.
    
    Supports:
    - Automatic unit selection (days, weeks, months)
    - Fractional duration formatting ("1.5 dias")
    - Singular/plural forms ("1 dia" vs "2 dias")
    - Multiple formatting styles
    - Compatibility with real epic data formats
    """
    
    def __init__(self, style: DurationStyle = DurationStyle.STANDARD, 
                 auto_unit_selection: bool = True):
        """
        Initialize duration formatter.
        
        Args:
            style: Formatting style to use
            auto_unit_selection: Whether to automatically select best unit
        """
        self.style = style
        self.auto_unit_selection = auto_unit_selection
        
        # Configuration for unit thresholds
        self._unit_thresholds = {
            DurationUnit.MONTHS: 30.0,   # 30+ days → months
            DurationUnit.WEEKS: 7.0,     # 7+ days → weeks
            DurationUnit.DAYS: 0.0       # fallback to days
        }
        
        # Formatting templates for different styles
        self._templates = {
            DurationStyle.COMPACT: {
                DurationUnit.DAYS: "{value}d",
                DurationUnit.WEEKS: "{value}w", 
                DurationUnit.MONTHS: "{value}m"
            },
            DurationStyle.STANDARD: {
                DurationUnit.DAYS: "{value} {unit}",
                DurationUnit.WEEKS: "{value} {unit}",
                DurationUnit.MONTHS: "{value} {unit}"
            },
            DurationStyle.VERBOSE: {
                DurationUnit.DAYS: "{value} {unit} úteis",
                DurationUnit.WEEKS: "{value} {unit} completas",
                DurationUnit.MONTHS: "{value} {unit} completos"
            }
        }
    
    def format(self, days: float, 
               preferred_unit: Optional[DurationUnit] = None) -> str:
        """
        Format duration in days to friendly description.
        
        Args:
            days: Duration in days (can be fractional)
            preferred_unit: Preferred unit to use (overrides auto-selection)
            
        Returns:
            Formatted duration string
            
        Raises:
            DurationFormattingError: If formatting fails
        """
        try:
            if days < 0:
                raise DurationFormattingError("Duration cannot be negative")
            
            # Select unit
            if preferred_unit:
                unit = preferred_unit
                value = self._convert_days_to_unit(days, unit)
            elif self.auto_unit_selection:
                unit, value = self._select_best_unit(days)
            else:
                unit = DurationUnit.DAYS
                value = days
            
            # Format value and unit text
            formatted_value = self._format_value(value)
            unit_text = self._get_unit_text(unit, value)
            
            # Apply template
            template = self._templates[self.style][unit]
            return template.format(value=formatted_value, unit=unit_text)
            
        except Exception as e:
            raise DurationFormattingError(f"Failed to format duration: {e}")
    
    def format_range(self, min_days: float, max_days: float) -> str:
        """
        Format a duration range.
        
        Args:
            min_days: Minimum duration in days
            max_days: Maximum duration in days
            
        Returns:
            Formatted range string like "1-2 dias" or "1.5-3 semanas"
        """
        if min_days > max_days:
            raise DurationFormattingError("Min duration cannot be greater than max")
        
        if min_days == max_days:
            return self.format(min_days)
        
        # Use same unit for both values
        if self.auto_unit_selection:
            # Use unit based on the larger value
            unit, _ = self._select_best_unit(max_days)
        else:
            unit = DurationUnit.DAYS
        
        min_value = self._convert_days_to_unit(min_days, unit)
        max_value = self._convert_days_to_unit(max_days, unit)
        
        min_formatted = self._format_value(min_value)
        max_formatted = self._format_value(max_value)
        unit_text = self._get_unit_text(unit, max_value)
        
        if self.style == DurationStyle.COMPACT:
            # Use proper compact unit abbreviations
            compact_units = {
                DurationUnit.DAYS: "d",
                DurationUnit.WEEKS: "w",
                DurationUnit.MONTHS: "m"
            }
            compact_unit = compact_units[unit]
            return f"{min_formatted}-{max_formatted}{compact_unit}"
        else:
            return f"{min_formatted}-{max_formatted} {unit_text}"
    
    def parse_formatted_duration(self, formatted_str: str) -> float:
        """
        Parse a formatted duration string back to days.
        
        Args:
            formatted_str: Formatted duration string
            
        Returns:
            Duration in days
            
        Raises:
            DurationFormattingError: If parsing fails
        """
        # Import DurationCalculator for parsing logic
        from .duration_calculator import DurationCalculator
        
        calculator = DurationCalculator()
        try:
            return calculator.parse_and_convert_to_days(formatted_str)
        except Exception as e:
            raise DurationFormattingError(f"Failed to parse duration: {e}")
    
    def format_epic_duration(self, duration_str: str) -> str:
        """
        Reformat an existing epic duration string to current style.
        
        Args:
            duration_str: Original duration string (e.g., "1.5 dias")
            
        Returns:
            Reformatted duration string
        """
        days = self.parse_formatted_duration(duration_str)
        return self.format(days)
    
    def _select_best_unit(self, days: float) -> Tuple[DurationUnit, float]:
        """Select the most appropriate unit for the given duration."""
        # Try units in order of preference (largest to smallest)
        for unit, threshold in self._unit_thresholds.items():
            if days >= threshold:
                value = self._convert_days_to_unit(days, unit)
                # Prefer units that result in "nice" numbers
                if self._is_nice_number(value):
                    return unit, value
                # If we're at weeks and it's exactly divisible, use it
                elif unit == DurationUnit.WEEKS and days % 7 == 0:
                    return unit, value
                # If we're at the largest unit, use it anyway
                elif unit == DurationUnit.MONTHS:
                    return unit, value
        
        # Fallback to days
        return DurationUnit.DAYS, days
    
    def _convert_days_to_unit(self, days: float, unit: DurationUnit) -> float:
        """Convert days to the specified unit."""
        if unit == DurationUnit.DAYS:
            return days
        elif unit == DurationUnit.WEEKS:
            return days / 7.0
        elif unit == DurationUnit.MONTHS:
            return days / 30.0  # Approximate 30 days per month
        else:
            raise DurationFormattingError(f"Unknown unit: {unit}")
    
    def _format_value(self, value: float) -> str:
        """Format numeric value for display."""
        # If it's a whole number, show without decimal
        if value == int(value):
            return str(int(value))
        else:
            # Show one decimal place for fractional values
            return f"{value:.1f}"
    
    def _get_unit_text(self, unit: DurationUnit, value: float) -> str:
        """Get the appropriate unit text (singular/plural)."""
        # Determine if we need singular or plural form
        is_singular = value == 1.0
        
        if unit == DurationUnit.DAYS:
            return "dia" if is_singular else "dias"
        elif unit == DurationUnit.WEEKS:
            return "semana" if is_singular else "semanas"
        elif unit == DurationUnit.MONTHS:
            return "mês" if is_singular else "meses"
        else:
            return unit.value
    
    def _is_nice_number(self, value: float) -> bool:
        """Check if a number is 'nice' for display (whole or .5)."""
        # Nice numbers are whole numbers or .5 increments
        return value == int(value) or abs(value - int(value) - 0.5) < 0.01


# Convenience functions for common formatting operations
def format_duration(days: float, style: DurationStyle = DurationStyle.STANDARD) -> str:
    """Quick function to format duration with default settings."""
    formatter = DurationFormatter(style=style)
    return formatter.format(days)


def format_epic_duration_standard(days: float) -> str:
    """Format duration in the standard epic format used in real data."""
    formatter = DurationFormatter(style=DurationStyle.STANDARD)
    return formatter.format(days)


def format_duration_compact(days: float) -> str:
    """Format duration in compact style for UI display."""
    formatter = DurationFormatter(style=DurationStyle.COMPACT)
    return formatter.format(days)


def format_duration_range(min_days: float, max_days: float) -> str:
    """Format a duration range with automatic unit selection."""
    formatter = DurationFormatter()
    return formatter.format_range(min_days, max_days)


def reformat_epic_duration(original_duration: str, 
                          target_style: DurationStyle = DurationStyle.STANDARD) -> str:
    """Reformat an existing epic duration to a different style."""
    formatter = DurationFormatter(style=target_style)
    return formatter.format_epic_duration(original_duration)


# Presets for common use cases
class EpicDurationFormatter:
    """Preset formatter configurations for epic data compatibility."""
    
    @staticmethod
    def standard() -> DurationFormatter:
        """Standard epic duration formatter (matches real epic data)."""
        return DurationFormatter(
            style=DurationStyle.STANDARD,
            auto_unit_selection=True
        )
    
    @staticmethod
    def compact() -> DurationFormatter:
        """Compact formatter for UI display."""
        return DurationFormatter(
            style=DurationStyle.COMPACT,
            auto_unit_selection=True
        )
    
    @staticmethod
    def days_only() -> DurationFormatter:
        """Formatter that always uses days (for precise tracking)."""
        return DurationFormatter(
            style=DurationStyle.STANDARD,
            auto_unit_selection=False
        )


# Testing utilities
def demonstrate_formatting_examples():
    """Demonstrate various formatting examples for testing/documentation."""
    formatter = DurationFormatter()
    
    test_cases = [
        1.0,    # "1 dia"
        1.5,    # "1.5 dias" 
        2.0,    # "2 dias"
        7.0,    # "1 semana"
        10.5,   # "1.5 semanas"
        14.0,   # "2 semanas"
        30.0,   # "1 mês"
        45.0    # "1.5 meses"
    ]
    
    examples = {}
    for days in test_cases:
        examples[days] = formatter.format(days)
    
    return examples


if __name__ == "__main__":
    # Quick demonstration
    examples = demonstrate_formatting_examples()
    for days, formatted in examples.items():
        print(f"{days} days → {formatted}")