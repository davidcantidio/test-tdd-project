"""Duration calculator for epic timeline management.

The module offers utilities to parse human readable duration strings and
convert them into concrete date offsets.  Both calendar and business day
calculations are supported with simple algorithms that skip weekends when
necessary.  These helpers power the duration features used across the test
TDD project.

Example:
    >>> calc = DurationCalculator()
    >>> calc.calculate_duration_days("2024-01-01", "2024-01-03")
    2.0

Todo:
    * Add holiday calendar integration for business day calculations.
"""

from datetime import datetime, date, timedelta
from typing import Optional, Tuple, Union, Dict, Any
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)

# Average number of days per month in Gregorian calendar
AVERAGE_DAYS_PER_MONTH = 365.25 / 12  # ≈30.4375 days


class DurationUnit(Enum):
    """Supported duration units from real epic data"""
    DAYS = "dias"
    WEEKS = "semanas"
    MONTHS = "meses"


class DateCalculationMode(Enum):
    """Date calculation modes"""
    CALENDAR_DAYS = "calendar"
    BUSINESS_DAYS = "business"


class DurationCalculationError(Exception):
    """Custom exception for duration calculation errors"""
    pass


class DurationCalculator:
    """
    Core engine for automatic duration calculation between dates.
    
    Supports:
    - Calendar days vs business days calculation
    - Multiple duration units (days, weeks, months)
    - Date consistency validation
    - Duration parsing from epic data formats
    """
    
    def __init__(self, calculation_mode: DateCalculationMode = DateCalculationMode.CALENDAR_DAYS):
        """
        Initialize duration calculator.
        
        Args:
            calculation_mode: Whether to use calendar or business days
        """
        self.calculation_mode = calculation_mode
        self._duration_pattern = re.compile(
            r'^(\d+(?:\.\d+)?)\s*(dias?|semanas?|meses?)$',
            re.IGNORECASE
        )
    
    def calculate_duration_days(
        self, 
        start_date: Union[date, datetime, str], 
        end_date: Union[date, datetime, str]
    ) -> float:
        """
        Calculate duration in days between two dates.
        
        Args:
            start_date: Start date (various formats supported)
            end_date: End date (various formats supported)
            
        Returns:
            Duration in days (float for fractional days)
            
        Raises:
            DurationCalculationError: If dates are invalid or inconsistent
        """
        try:
            start = self._normalize_date(start_date)
            end = self._normalize_date(end_date)
            
            if start > end:
                raise DurationCalculationError(
                    f"Start date ({start}) cannot be after end date ({end})"
                )
            
            if self.calculation_mode == DateCalculationMode.BUSINESS_DAYS:
                return self._calculate_business_days(start, end)
            else:
                return (end - start).days
                
        except (ValueError, TypeError) as e:
            raise DurationCalculationError(f"Invalid date format: {e}")
    
    def calculate_end_date(
        self, 
        start_date: Union[date, datetime, str], 
        duration_days: float
    ) -> date:
        """
        Calculate end date given start date and duration.
        
        Args:
            start_date: Start date
            duration_days: Duration in days (can be fractional)
            
        Returns:
            Calculated end date
            
        Raises:
            DurationCalculationError: If calculation fails
        """
        try:
            start = self._normalize_date(start_date)
            
            if duration_days < 0:
                raise DurationCalculationError("Duration cannot be negative")
            
            if self.calculation_mode == DateCalculationMode.BUSINESS_DAYS:
                return self._add_business_days(start, duration_days)
            else:
                days_to_add = int(duration_days)
                # Handle fractional days by ignoring them for date calculation
                return start + timedelta(days=days_to_add)
                
        except (ValueError, TypeError) as e:
            raise DurationCalculationError(f"Invalid input: {e}")
    
    def parse_duration_string(self, duration_str: str) -> Tuple[float, DurationUnit]:
        """
        Parse duration string from epic data format.
        
        Supported formats from real epic data:
        - "1 dia", "2 dias"
        - "1.5 dias" 
        - "1 semana", "2 semanas"
        
        Args:
            duration_str: Duration string to parse
            
        Returns:
            Tuple of (numeric_value, unit)
            
        Raises:
            DurationCalculationError: If format is not recognized
        """
        duration_str = duration_str.strip()
        match = self._duration_pattern.match(duration_str)
        
        if not match:
            raise DurationCalculationError(
                f"Invalid duration format: '{duration_str}'. "
                f"Expected formats: '1.5 dias', '1 semana', etc."
            )
        
        value_str, unit_str = match.groups()
        value = float(value_str)
        
        # Normalize unit to enum
        unit_normalized = unit_str.lower()
        if unit_normalized in ['dia', 'dias']:
            unit = DurationUnit.DAYS
        elif unit_normalized in ['semana', 'semanas']:
            unit = DurationUnit.WEEKS
        elif unit_normalized in ['mes', 'meses', 'mês']:
            unit = DurationUnit.MONTHS
        else:
            raise DurationCalculationError(f"Unsupported unit: {unit_str}")
        
        return value, unit
    
    def duration_to_days(self, value: float, unit: DurationUnit) -> float:
        """
        Convert duration value to days based on unit.
        
        Args:
            value: Numeric value 
            unit: Duration unit
            
        Returns:
            Duration converted to days
        """
        if unit == DurationUnit.DAYS:
            return value
        elif unit == DurationUnit.WEEKS:
            return value * 7.0
        elif unit == DurationUnit.MONTHS:
            # Use average Gregorian month length for better accuracy
            return value * AVERAGE_DAYS_PER_MONTH
        else:
            raise DurationCalculationError(f"Unknown unit: {unit}")
    
    def parse_and_convert_to_days(self, duration_str: str) -> float:
        """
        Parse duration string and convert to days in one step.
        
        Args:
            duration_str: Duration string from epic data
            
        Returns:
            Duration in days (float)
        """
        value, unit = self.parse_duration_string(duration_str)
        return self.duration_to_days(value, unit)
    
    def validate_date_consistency(
        self, 
        planned_start: Optional[Union[date, str]] = None,
        planned_end: Optional[Union[date, str]] = None,
        actual_start: Optional[Union[date, str]] = None,
        actual_end: Optional[Union[date, str]] = None,
        duration_days: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Validate consistency between date fields and duration.
        
        Args:
            planned_start: Planned start date
            planned_end: Planned end date  
            actual_start: Actual start date
            actual_end: Actual end date
            duration_days: Expected duration in days
            
        Returns:
            Validation result with status and details
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "calculated_durations": {}
        }
        
        try:
            # Normalize dates
            dates = {}
            for name, date_val in [
                ("planned_start", planned_start),
                ("planned_end", planned_end),
                ("actual_start", actual_start),
                ("actual_end", actual_end)
            ]:
                if date_val is not None:
                    dates[name] = self._normalize_date(date_val)
            
            # Validate planned dates
            if "planned_start" in dates and "planned_end" in dates:
                if dates["planned_start"] > dates["planned_end"]:
                    result["errors"].append(
                        "Planned start date cannot be after planned end date"
                    )
                    result["is_valid"] = False
                else:
                    planned_duration = self.calculate_duration_days(
                        dates["planned_start"], dates["planned_end"]
                    )
                    result["calculated_durations"]["planned"] = planned_duration
                    
                    # Check against expected duration
                    if duration_days is not None:
                        diff = abs(planned_duration - duration_days)
                        if diff >= 0.5:  # Allow less than 0.5 day tolerance
                            result["warnings"].append(
                                f"Planned duration ({planned_duration:.1f} days) "
                                f"differs from expected ({duration_days:.1f} days)"
                            )
            
            # Validate actual dates
            if "actual_start" in dates and "actual_end" in dates:
                if dates["actual_start"] > dates["actual_end"]:
                    result["errors"].append(
                        "Actual start date cannot be after actual end date"
                    )
                    result["is_valid"] = False
                else:
                    actual_duration = self.calculate_duration_days(
                        dates["actual_start"], dates["actual_end"]
                    )
                    result["calculated_durations"]["actual"] = actual_duration
            
            # Cross-validate planned vs actual
            if "planned_start" in dates and "actual_start" in dates:
                if dates["actual_start"] < dates["planned_start"]:
                    result["warnings"].append(
                        "Actual start is before planned start"
                    )
            
            if "planned_end" in dates and "actual_end" in dates:
                if dates["actual_end"] > dates["planned_end"]:
                    result["warnings"].append(
                        "Actual end is after planned end (overrun)"
                    )
        
        except (DurationCalculationError, ValueError, TypeError) as e:
            result["errors"].append(str(e))
            result["is_valid"] = False
        
        return result
    
    def _normalize_date(self, date_input: Union[date, datetime, str]) -> date:
        """Convert various date formats to date object."""
        if isinstance(date_input, date) and not isinstance(date_input, datetime):
            return date_input
        elif isinstance(date_input, datetime):
            return date_input.date()
        elif isinstance(date_input, str):
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_input, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date string: {date_input}")
        else:
            raise TypeError(f"Unsupported date type: {type(date_input)}")
    
    def _calculate_business_days(self, start_date: date, end_date: date) -> float:
        """Calculate business days between two dates (excluding weekends)."""
        if start_date == end_date:
            return 0.0
        
        # Simple business day calculation (Monday=0, Sunday=6)
        business_days = 0
        current_date = start_date
        
        while current_date < end_date:
            if current_date.weekday() < 5:  # Monday-Friday
                business_days += 1
            current_date += timedelta(days=1)
        
        return float(business_days)
    
    def _add_business_days(self, start_date: date, business_days: float) -> date:
        """Add business days to a date."""
        days_to_add = int(business_days)
        current_date = start_date
        added_days = 0
        
        while added_days < days_to_add:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5:  # Monday-Friday
                added_days += 1
        
        return current_date


# Convenience functions for common operations
def calculate_epic_duration(start_date: Union[date, str], end_date: Union[date, str]) -> float:
    """Quick function to calculate epic duration in days."""
    calculator = DurationCalculator()
    return calculator.calculate_duration_days(start_date, end_date)


def parse_epic_duration(duration_str: str) -> float:
    """Quick function to parse epic duration string to days."""
    calculator = DurationCalculator()
    return calculator.parse_and_convert_to_days(duration_str)


def validate_epic_dates(
    planned_start: Optional[str] = None,
    planned_end: Optional[str] = None,
    duration_str: Optional[str] = None
) -> Dict[str, Any]:
    """Quick function to validate epic date consistency."""
    calculator = DurationCalculator()
    duration_days = None
    
    if duration_str:
        duration_days = calculator.parse_and_convert_to_days(duration_str)
    
    return calculator.validate_date_consistency(
        planned_start=planned_start,
        planned_end=planned_end,
        duration_days=duration_days
    )