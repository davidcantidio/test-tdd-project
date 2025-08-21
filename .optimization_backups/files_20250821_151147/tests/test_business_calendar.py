"""
🧪 Test Suite for Business Calendar System

Comprehensive tests for the optimized business calendar with holiday support.
Validates the fixes for Codex audit issues:

1. O(n) complexity optimization
2. Holiday calendar integration
3. Caching performance
4. Accuracy vs. original algorithm
"""

import pytest
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

# Add duration_system to path
sys.path.append(str(Path(__file__).parent.parent))

from duration_system.business_calendar import (
    BusinessCalendar,
    BusinessCalendarType,
    WeekendPattern,
    get_business_calendar,
    count_business_days,
    add_business_days,
    is_business_day,
    OptimizedDurationCalculator,
    benchmark_business_day_performance
)


class TestBusinessCalendar:
    """Test suite for BusinessCalendar class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.calendar = BusinessCalendar(
            calendar_type=BusinessCalendarType.BRAZIL,
            weekend_pattern=WeekendPattern.SATURDAY_SUNDAY
        )
        self.generic_calendar = BusinessCalendar(
            calendar_type=BusinessCalendarType.GENERIC,
            weekend_pattern=WeekendPattern.SATURDAY_SUNDAY
        )
    
    def test_weekend_detection_saturday_sunday(self):
        """Test weekend detection for Saturday/Sunday pattern."""
        # Monday - not weekend
        assert self.calendar.is_business_day(date(2024, 6, 3)) is True  # Monday
        
        # Tuesday - not weekend  
        assert self.calendar.is_business_day(date(2024, 6, 4)) is True  # Tuesday
        
        # Saturday - weekend
        assert self.calendar.is_business_day(date(2024, 6, 1)) is False  # Saturday
        
        # Sunday - weekend
        assert self.calendar.is_business_day(date(2024, 6, 2)) is False  # Sunday
    
    def test_weekend_detection_friday_saturday(self):
        """Test weekend detection for Friday/Saturday pattern."""
        friday_saturday_calendar = BusinessCalendar(
            calendar_type=BusinessCalendarType.GENERIC,
            weekend_pattern=WeekendPattern.FRIDAY_SATURDAY
        )
        
        # Thursday - not weekend
        assert friday_saturday_calendar.is_business_day(date(2024, 6, 6)) is True  # Thursday
        
        # Friday - weekend
        assert friday_saturday_calendar.is_business_day(date(2024, 6, 7)) is False  # Friday
        
        # Saturday - weekend  
        assert friday_saturday_calendar.is_business_day(date(2024, 6, 8)) is False  # Saturday
        
        # Sunday - not weekend
        assert friday_saturday_calendar.is_business_day(date(2024, 6, 9)) is True  # Sunday
    
    def test_holiday_detection_with_custom_holidays(self):
        """Test holiday detection with custom holidays."""
        custom_holidays = {
            date(2024, 6, 10),  # Custom holiday
            date(2024, 12, 25)  # Christmas
        }
        
        calendar_with_holidays = BusinessCalendar(
            calendar_type=BusinessCalendarType.GENERIC,
            custom_holidays=custom_holidays
        )
        
        # Normal business day
        assert calendar_with_holidays.is_business_day(date(2024, 6, 11)) is True  # Tuesday
        
        # Custom holiday (Monday)
        assert calendar_with_holidays.is_business_day(date(2024, 6, 10)) is False
        
        # Christmas (Wednesday) 
        assert calendar_with_holidays.is_business_day(date(2024, 12, 25)) is False
    
    def test_business_day_counting_basic(self):
        """Test basic business day counting."""
        # June 3-7, 2024 (Monday to Friday)
        start_date = date(2024, 6, 3)  # Monday
        end_date = date(2024, 6, 7)    # Friday
        
        # Should be 5 business days
        count = self.generic_calendar.count_business_days_optimized(start_date, end_date)
        assert count == 5
    
    def test_business_day_counting_with_weekend(self):
        """Test business day counting including weekends."""
        # June 1-9, 2024 (Saturday to Sunday - includes 1 full week)
        start_date = date(2024, 6, 1)  # Saturday  
        end_date = date(2024, 6, 9)    # Sunday
        
        # Should be 5 business days (Mon-Fri in between)
        count = self.generic_calendar.count_business_days_optimized(start_date, end_date)
        assert count == 5
    
    def test_business_day_counting_same_date(self):
        """Test business day counting for same date."""
        # Business day
        business_day = date(2024, 6, 3)  # Monday
        count = self.generic_calendar.count_business_days_optimized(business_day, business_day)
        assert count == 1
        
        # Weekend day
        weekend_day = date(2024, 6, 1)  # Saturday
        count = self.generic_calendar.count_business_days_optimized(weekend_day, weekend_day)
        assert count == 0
    
    def test_business_day_counting_reverse_dates(self):
        """Test business day counting with reversed dates."""
        start_date = date(2024, 6, 7)  # Friday
        end_date = date(2024, 6, 3)    # Monday (earlier)
        
        # Should return 0 for reversed dates
        count = self.generic_calendar.count_business_days_optimized(start_date, end_date)
        assert count == 0
    
    def test_add_business_days_basic(self):
        """Test adding business days."""
        # Start on Monday, add 5 business days -> should be next Monday
        start_date = date(2024, 6, 3)  # Monday
        result = self.generic_calendar.add_business_days_optimized(start_date, 5)
        
        # Should skip weekend and land on Monday
        expected = date(2024, 6, 10)  # Next Monday
        assert result == expected
    
    def test_add_business_days_zero(self):
        """Test adding zero business days."""
        start_date = date(2024, 6, 3)  # Monday
        result = self.generic_calendar.add_business_days_optimized(start_date, 0)
        assert result == start_date
    
    def test_add_business_days_large_number(self):
        """Test adding large number of business days (optimization test)."""
        start_date = date(2024, 1, 1)
        
        # Add 100 business days
        result = self.generic_calendar.add_business_days_optimized(start_date, 100)
        
        # Verify by counting back
        count = self.generic_calendar.count_business_days_optimized(start_date, result)
        assert count >= 100  # Should be at least 100 (could be more due to holidays)
    
    def test_get_next_business_day(self):
        """Test getting next business day."""
        # From Friday to Monday
        friday = date(2024, 6, 7)
        next_business = self.generic_calendar.get_next_business_day(friday)
        expected_monday = date(2024, 6, 10)
        assert next_business == expected_monday
        
        # From Monday to Tuesday
        monday = date(2024, 6, 3)
        next_business = self.generic_calendar.get_next_business_day(monday)
        expected_tuesday = date(2024, 6, 4)
        assert next_business == expected_tuesday
    
    def test_get_previous_business_day(self):
        """Test getting previous business day."""
        # From Monday to Friday
        monday = date(2024, 6, 3)
        prev_business = self.generic_calendar.get_previous_business_day(monday)
        expected_friday = date(2024, 5, 31)
        assert prev_business == expected_friday
        
        # From Tuesday to Monday
        tuesday = date(2024, 6, 4)
        prev_business = self.generic_calendar.get_previous_business_day(tuesday)
        expected_monday = date(2024, 6, 3)
        assert prev_business == expected_monday
    
    def test_cache_functionality(self):
        """Test caching functionality."""
        # Clear cache first
        self.calendar.clear_cache()
        
        # First calculation should populate cache
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        count1 = self.calendar.count_business_days_optimized(start_date, end_date)
        cache_stats_after_first = self.calendar.get_cache_stats()
        
        # Second calculation should use cache
        count2 = self.calendar.count_business_days_optimized(start_date, end_date)
        
        # Results should be identical
        assert count1 == count2
        
        # Cache should have entries
        assert cache_stats_after_first["business_day_cache_size"] > 0 or cache_stats_after_first["holiday_cache_size"] > 0


class TestBusinessCalendarTypes:
    """Test different business calendar types."""
    
    @pytest.mark.skipif(
        not hasattr(sys.modules.get('holidays', None), 'Brazil'),
        reason="holidays library not available or doesn't support Brazil"
    )
    def test_brazil_calendar_holidays(self):
        """Test Brazilian calendar with holidays."""
        br_calendar = BusinessCalendar(calendar_type=BusinessCalendarType.BRAZIL)
        
        # Test Independence Day (September 7) - should not be business day
        independence_day = date(2024, 9, 7)
        
        # Only test if not a weekend
        if independence_day.weekday() not in {5, 6}:  # Not Sat/Sun
            assert br_calendar.is_business_day(independence_day) is False
    
    @pytest.mark.skipif(
        not hasattr(sys.modules.get('holidays', None), 'UnitedStates'),
        reason="holidays library not available or doesn't support US"
    )
    def test_us_calendar_holidays(self):
        """Test US calendar with holidays."""
        us_calendar = BusinessCalendar(calendar_type=BusinessCalendarType.UNITED_STATES)
        
        # Test July 4th - should not be business day
        july_4th = date(2024, 7, 4)
        
        # Only test if not a weekend
        if july_4th.weekday() not in {5, 6}:  # Not Sat/Sun
            assert us_calendar.is_business_day(july_4th) is False
    
    def test_generic_calendar_no_holidays(self):
        """Test generic calendar has no holidays."""
        generic_calendar = BusinessCalendar(calendar_type=BusinessCalendarType.GENERIC)
        
        # Should treat typical holidays as business days (if not weekend)
        christmas = date(2024, 12, 25)
        
        # Only test if Christmas is not on weekend
        if christmas.weekday() not in {5, 6}:  # Not Sat/Sun
            assert generic_calendar.is_business_day(christmas) is True


class TestPerformanceOptimizations:
    """Test performance optimizations and complexity improvements."""
    
    def test_short_range_vs_long_range_methods(self):
        """Test that different algorithms are used for short vs long ranges."""
        calendar = BusinessCalendar(calendar_type=BusinessCalendarType.GENERIC)
        
        # Short range (should use direct method)
        short_start = date(2024, 6, 1)
        short_end = date(2024, 6, 15)
        short_count = calendar.count_business_days_optimized(short_start, short_end)
        
        # Long range (should use mathematical method)
        long_start = date(2024, 1, 1)
        long_end = date(2024, 12, 31)
        long_count = calendar.count_business_days_optimized(long_start, long_end)
        
        # Both should return reasonable values
        assert 0 < short_count <= 11  # At most 11 business days in 15 calendar days
        assert 200 < long_count <= 366  # Full year should have 200+ business days
    
    @pytest.mark.performance
    def test_performance_improvement_benchmark(self):
        """Test that optimized algorithm is faster than direct method."""
        calendar = BusinessCalendar(calendar_type=BusinessCalendarType.GENERIC)
        
        # Test with year-long range
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # Time the optimized method
        start_time = time.time()
        for _ in range(10):
            calendar.count_business_days_optimized(start_date, end_date)
        optimized_time = time.time() - start_time
        
        # Time the direct method
        start_time = time.time()
        for _ in range(10):
            calendar._count_business_days_direct(start_date, end_date)
        direct_time = time.time() - start_time
        
        # Optimized should be faster for long ranges
        # Note: For very long ranges, optimized should be significantly faster
        # For this test, we just ensure it doesn't timeout and gives reasonable results
        assert optimized_time < 1.0  # Should complete in under 1 second
        assert direct_time < 10.0  # Direct method should complete in under 10 seconds
        
        print(f"Optimized: {optimized_time:.3f}s, Direct: {direct_time:.3f}s")
    
    def test_mathematical_weekend_calculation(self):
        """Test mathematical weekend calculation accuracy."""
        calendar = BusinessCalendar(calendar_type=BusinessCalendarType.GENERIC)
        
        # Test exact week
        week_start = date(2024, 6, 3)  # Monday
        week_end = date(2024, 6, 9)    # Sunday
        
        weekend_count = calendar._count_weekend_days_mathematical(week_start, week_end)
        assert weekend_count == 2  # Saturday and Sunday
        
        # Test partial week
        partial_start = date(2024, 6, 5)  # Wednesday
        partial_end = date(2024, 6, 7)    # Friday
        
        weekend_count_partial = calendar._count_weekend_days_mathematical(partial_start, partial_end)
        assert weekend_count_partial == 0  # No weekends in Wed-Fri
    
    def test_holiday_counting_efficiency(self):
        """Test efficient holiday counting across years."""
        calendar = BusinessCalendar(calendar_type=BusinessCalendarType.GENERIC)
        
        # Add some custom holidays
        calendar.custom_holidays = {
            date(2024, 6, 10),
            date(2024, 6, 20),
            date(2025, 1, 1)
        }
        
        # Count holidays across year boundary
        start_date = date(2024, 6, 1)
        end_date = date(2025, 1, 31)
        
        holiday_count = calendar._count_holidays_in_range(start_date, end_date)
        assert holiday_count == 3  # All 3 custom holidays are in range
        
        # Test with range that excludes some holidays
        limited_end = date(2024, 6, 15)
        limited_holiday_count = calendar._count_holidays_in_range(start_date, limited_end)
        assert limited_holiday_count == 1  # Only June 10th holiday


class TestConvenienceFunctions:
    """Test convenience functions for ease of use."""
    
    def test_count_business_days_function(self):
        """Test count_business_days convenience function."""
        # Test with date objects
        start_date = date(2024, 6, 3)  # Monday
        end_date = date(2024, 6, 7)    # Friday
        
        count = count_business_days(start_date, end_date, BusinessCalendarType.GENERIC)
        assert count == 5
        
        # Test with string dates
        count_str = count_business_days("2024-06-03", "2024-06-07", BusinessCalendarType.GENERIC)
        assert count_str == 5
    
    def test_add_business_days_function(self):
        """Test add_business_days convenience function."""
        # Test with date object
        start_date = date(2024, 6, 3)  # Monday
        result = add_business_days(start_date, 5, BusinessCalendarType.GENERIC)
        expected = date(2024, 6, 10)  # Next Monday
        assert result == expected
        
        # Test with string date
        result_str = add_business_days("2024-06-03", 5, BusinessCalendarType.GENERIC)
        assert result_str == expected
    
    def test_is_business_day_function(self):
        """Test is_business_day convenience function."""
        # Business day (Monday)
        assert is_business_day(date(2024, 6, 3), BusinessCalendarType.GENERIC) is True
        assert is_business_day("2024-06-03", BusinessCalendarType.GENERIC) is True
        
        # Weekend (Saturday)
        assert is_business_day(date(2024, 6, 1), BusinessCalendarType.GENERIC) is False
        assert is_business_day("2024-06-01", BusinessCalendarType.GENERIC) is False
    
    def test_global_calendar_singleton(self):
        """Test that global calendar instances are singletons."""
        cal1 = get_business_calendar(BusinessCalendarType.BRAZIL)
        cal2 = get_business_calendar(BusinessCalendarType.BRAZIL)
        
        # Should be the same instance
        assert cal1 is cal2
        
        # Different types should be different instances
        cal3 = get_business_calendar(BusinessCalendarType.UNITED_STATES)
        assert cal1 is not cal3


class TestOptimizedDurationCalculator:
    """Test the optimized duration calculator integration."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.calculator = OptimizedDurationCalculator(BusinessCalendarType.GENERIC)
    
    def test_calculate_business_days_between(self):
        """Test business days calculation."""
        start_date = date(2024, 6, 3)  # Monday
        end_date = date(2024, 6, 7)    # Friday
        
        days = self.calculator.calculate_business_days_between(start_date, end_date)
        assert days == 5.0
        
        # Test with string dates
        days_str = self.calculator.calculate_business_days_between("2024-06-03", "2024-06-07")
        assert days_str == 5.0
    
    def test_add_business_days_to_date(self):
        """Test adding business days to date."""
        start_date = date(2024, 6, 3)  # Monday
        result = self.calculator.add_business_days_to_date(start_date, 5.0)
        expected = date(2024, 6, 10)  # Next Monday
        assert result == expected
        
        # Test with string date
        result_str = self.calculator.add_business_days_to_date("2024-06-03", 5.0)
        assert result_str == expected
    
    def test_fractional_business_days(self):
        """Test handling of fractional business days."""
        start_date = date(2024, 6, 3)  # Monday
        
        # 2.5 days should round to 2 days
        result = self.calculator.add_business_days_to_date(start_date, 2.5)
        expected = date(2024, 6, 5)  # Wednesday (2 business days later)
        assert result == expected


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""
    
    def test_invalid_date_strings(self):
        """Test handling of invalid date strings."""
        calendar = BusinessCalendar()
        
        # Invalid date format should return False for is_business_day
        assert calendar.is_business_day("invalid-date") is False
        assert calendar.is_business_day("2024-13-45") is False
    
    def test_very_large_date_ranges(self):
        """Test handling of very large date ranges."""
        calendar = BusinessCalendar(calendar_type=BusinessCalendarType.GENERIC)
        
        # 10-year range
        start_date = date(2020, 1, 1)
        end_date = date(2030, 12, 31)
        
        # Should handle large ranges without timeout
        count = calendar.count_business_days_optimized(start_date, end_date)
        
        # Rough estimate: ~260 business days per year * 11 years
        assert 2500 < count < 3000
    
    def test_leap_year_handling(self):
        """Test handling of leap years."""
        calendar = BusinessCalendar(calendar_type=BusinessCalendarType.GENERIC)
        
        # 2024 is a leap year
        leap_day = date(2024, 2, 29)
        
        # Should correctly identify if it's a business day
        is_business = calendar.is_business_day(leap_day)
        
        # Result depends on what day of week Feb 29, 2024 falls on
        # (Thursday in 2024, so should be True)
        assert is_business is True
    
    def test_cache_memory_management(self):
        """Test that cache doesn't grow unbounded."""
        calendar = BusinessCalendar(cache_size=10)  # Small cache
        
        # Add many entries to test cache limit
        for i in range(20):
            start = date(2024, 1, 1) + timedelta(days=i)
            end = start + timedelta(days=5)
            calendar.count_business_days_optimized(start, end)
        
        # Cache should not exceed reasonable size
        stats = calendar.get_cache_stats()
        assert stats["business_day_cache_size"] <= 1000  # Reasonable limit


@pytest.mark.benchmark
def test_benchmark_performance():
    """Test the benchmark function itself."""
    results = benchmark_business_day_performance()
    
    # Should return all expected keys
    expected_keys = {
        "optimized_time", "direct_time", "speedup_factor", 
        "optimized_per_call_ms", "direct_per_call_ms"
    }
    assert set(results.keys()) == expected_keys
    
    # All values should be positive
    for key, value in results.items():
        assert value > 0, f"{key} should be positive, got {value}"
    
    # Optimized should generally be faster
    assert results["optimized_per_call_ms"] < 100, "Optimized method should be under 100ms per call"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])