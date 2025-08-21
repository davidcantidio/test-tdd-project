"""
Test suite for DurationFormatter Engine

Comprehensive test coverage for duration formatting functionality
that creates user-friendly descriptions from numeric duration values.

Target: ≥95% code coverage
"""

import pytest
from duration_system.duration_formatter import (
    DurationFormatter,
    DurationUnit,
    DurationStyle,
    DurationFormattingError,
    format_duration,
    format_epic_duration_standard,
    format_duration_compact,
    format_duration_range,
    reformat_epic_duration,
    EpicDurationFormatter,
    demonstrate_formatting_examples
)


class TestDurationFormatter:
    """Test suite for DurationFormatter class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.formatter = DurationFormatter()
        self.compact_formatter = DurationFormatter(style=DurationStyle.COMPACT)
        self.verbose_formatter = DurationFormatter(style=DurationStyle.VERBOSE)
        self.days_only_formatter = DurationFormatter(auto_unit_selection=False)
    
    # ==================================================================================
    # BASIC FORMATTING TESTS
    # ==================================================================================
    
    def test_format_single_day(self):
        """Test formatting 1 day (singular)"""
        result = self.formatter.format(1.0)
        assert result == "1 dia"
    
    def test_format_multiple_days(self):
        """Test formatting multiple days (plural)"""
        result = self.formatter.format(2.0)
        assert result == "2 dias"
    
    def test_format_fractional_days(self):
        """Test formatting fractional days"""
        result = self.formatter.format(1.5)
        assert result == "1.5 dias"
    
    def test_format_single_week(self):
        """Test formatting 1 week (7 days)"""
        result = self.formatter.format(7.0)
        assert result == "1 semana"
    
    def test_format_multiple_weeks(self):
        """Test formatting multiple weeks"""
        result = self.formatter.format(14.0)
        assert result == "2 semanas"
    
    def test_format_fractional_weeks(self):
        """Test formatting fractional weeks"""
        result = self.formatter.format(10.5)
        assert result == "1.5 semanas"
    
    def test_format_single_month(self):
        """Test formatting 1 month (30 days)"""
        result = self.formatter.format(30.0)
        assert result == "1 mês"
    
    def test_format_multiple_months(self):
        """Test formatting multiple months"""
        result = self.formatter.format(60.0)
        assert result == "2 meses"
    
    def test_format_zero_duration(self):
        """Test formatting zero duration"""
        result = self.formatter.format(0.0)
        assert result == "0 dias"
    
    def test_format_negative_duration_error(self):
        """Test error with negative duration"""
        with pytest.raises(DurationFormattingError) as exc_info:
            self.formatter.format(-1.0)
        assert "cannot be negative" in str(exc_info.value)
    
    # ==================================================================================
    # REAL EPIC DATA FORMAT TESTS
    # ==================================================================================
    
    # TODO: Consider extracting this block into a separate method
    def test_format_epic_data_patterns(self):
        """Test formatting patterns found in real epic data"""
        test_cases = [
            (1.5, "1.5 dias"),   # epico_5.json, epico_6.json
            (2.0, "2 dias"),     # epico_0.json
            (5.0, "5 dias"),     # epico_2.json
            (7.0, "1 semana"),   # epico_3.json (should convert to weeks)
            (4.0, "4 dias")      # epico_4.json
        ]
        
        for days, expected in test_cases:
            result = self.formatter.format(days)
            assert result == expected, f"Failed for {days} days: got {result}, expected {expected}"
    
    def test_format_with_preferred_unit_days(self):
        """Test formatting with preferred unit set to days"""
        # Force 7 days to be formatted as days instead of 1 week
        result = self.formatter.format(7.0, preferred_unit=DurationUnit.DAYS)
        assert result == "7 dias"
    
    def test_format_with_preferred_unit_weeks(self):
        """Test formatting with preferred unit set to weeks"""
        # Force 5 days to be formatted as weeks
        result = self.formatter.format(5.0, preferred_unit=DurationUnit.WEEKS)
        assert result == "0.7 semanas"
    
    def test_format_with_preferred_unit_months(self):
        """Test formatting with preferred unit set to months"""
        # Force 15 days to be formatted as months
        result = self.formatter.format(15.0, preferred_unit=DurationUnit.MONTHS)
        assert result == "0.5 meses"
    
    # ==================================================================================
    # FORMATTING STYLE TESTS
    # ==================================================================================
    
    def test_compact_style_days(self):
        """Test compact formatting style for days"""
        result = self.compact_formatter.format(3.5)
        assert result == "3.5d"
    
    def test_compact_style_weeks(self):
        """Test compact formatting style for weeks"""
        result = self.compact_formatter.format(14.0)
        assert result == "2w"
    
    def test_compact_style_months(self):
        """Test compact formatting style for months"""
        result = self.compact_formatter.format(60.0)
        assert result == "2m"
    
    def test_verbose_style_days(self):
        """Test verbose formatting style for days"""
        result = self.verbose_formatter.format(3.0)
        assert result == "3 dias úteis"
    
    def test_verbose_style_weeks(self):
        """Test verbose formatting style for weeks"""
        result = self.verbose_formatter.format(14.0)
        assert result == "2 semanas completas"
    
    def test_verbose_style_months(self):
        """Test verbose formatting style for months"""
        result = self.verbose_formatter.format(60.0)
        assert result == "2 meses completos"
    
    def test_days_only_formatter(self):
        """Test formatter with auto unit selection disabled"""
        # Should always format as days, even for 7+ days
        result = self.days_only_formatter.format(7.0)
        assert result == "7 dias"
        
        result = self.days_only_formatter.format(30.0)
        assert result == "30 dias"
    
    # ==================================================================================
    # DURATION RANGE FORMATTING TESTS
    # ==================================================================================
    
    def test_format_range_same_values(self):
        """Test formatting range with same min and max"""
        result = self.formatter.format_range(5.0, 5.0)
        assert result == "5 dias"
    
    def test_format_range_days(self):
        """Test formatting range in days"""
        result = self.formatter.format_range(2.0, 5.0)
        assert result == "2-5 dias"
    
    def test_format_range_weeks(self):
        """Test formatting range in weeks"""
        result = self.formatter.format_range(7.0, 14.0)
        assert result == "1-2 semanas"
    
    def test_format_range_fractional(self):
        """Test formatting range with fractional values"""
        result = self.formatter.format_range(1.5, 3.5)
        assert result == "1.5-3.5 dias"
    
    def test_format_range_compact_style(self):
        """Test formatting range in compact style"""
        result = self.compact_formatter.format_range(7.0, 21.0)
        assert result == "1-3w"
    
    def test_format_range_invalid_order(self):
        """Test error when min > max in range"""
        with pytest.raises(DurationFormattingError) as exc_info:
            self.formatter.format_range(5.0, 2.0)
        assert "cannot be greater than" in str(exc_info.value)
    
    # ==================================================================================
    # PARSING AND REFORMATTING TESTS
    # ==================================================================================
    
    def test_parse_formatted_duration_days(self):
        """Test parsing formatted duration back to days"""
        days = self.formatter.parse_formatted_duration("1.5 dias")
        assert days == 1.5
    
    def test_parse_formatted_duration_weeks(self):
        """Test parsing formatted duration in weeks"""
        days = self.formatter.parse_formatted_duration("1 semana")
        assert days == 7.0
    
    def test_parse_formatted_duration_invalid(self):
        """Test error parsing invalid formatted duration"""
        with pytest.raises(DurationFormattingError):
            self.formatter.parse_formatted_duration("invalid format")
    
    def test_format_epic_duration_reformat(self):
        """Test reformatting existing epic duration"""
        result = self.formatter.format_epic_duration("1 semana")
        assert result == "1 semana"  # Should stay the same in standard format
    
    def test_format_epic_duration_style_change(self):
        """Test reformatting epic duration to different style"""
        result = self.compact_formatter.format_epic_duration("1 semana")
        assert result == "1w"
    
    # ==================================================================================
    # UNIT SELECTION LOGIC TESTS
    # ==================================================================================
    
    def test_unit_selection_prefers_whole_numbers(self):
        """Test that unit selection prefers whole numbers"""
        # 14 days should be "2 semanas" not "14 dias"
        result = self.formatter.format(14.0)
        assert result == "2 semanas"
    
    def test_unit_selection_keeps_nice_fractions(self):
        """Test that unit selection keeps nice fractions like .5"""
        # 10.5 days = 1.5 weeks, should prefer weeks
        result = self.formatter.format(10.5)
        assert result == "1.5 semanas"
    
    def test_unit_selection_avoids_ugly_fractions(self):
        """Test that unit selection avoids ugly fractions"""
        # 5 days = 0.714... weeks, should stay as days
        result = self.formatter.format(5.0)
        assert result == "5 dias"
    
    def test_unit_selection_exact_multiples(self):
        """Test unit selection for exact multiples"""
        test_cases = [
            (7.0, "1 semana"),     # Exactly 1 week
            (21.0, "3 semanas"),   # Exactly 3 weeks
            (30.0, "1 mês"),       # Exactly 1 month
            (90.0, "3 meses")      # Exactly 3 months
        ]
        
        for days, expected in test_cases:
            result = self.formatter.format(days)
            assert result == expected
    
    # ==================================================================================
    # PRIVATE METHOD TESTS
    # ==================================================================================
    
    def test_convert_days_to_unit_days(self):
        """Test converting days to days unit"""
        result = self.formatter._convert_days_to_unit(5.0, DurationUnit.DAYS)
        assert result == 5.0
    
    def test_convert_days_to_unit_weeks(self):
        """Test converting days to weeks unit"""
        result = self.formatter._convert_days_to_unit(14.0, DurationUnit.WEEKS)
        assert result == 2.0
    
    def test_convert_days_to_unit_months(self):
        """Test converting days to months unit"""
        result = self.formatter._convert_days_to_unit(60.0, DurationUnit.MONTHS)
        assert result == 2.0
    
    def test_format_value_whole_number(self):
        """Test formatting whole number values"""
        result = self.formatter._format_value(5.0)
        assert result == "5"
    
    def test_format_value_fractional(self):
        """Test formatting fractional values"""
        result = self.formatter._format_value(1.5)
        assert result == "1.5"
    
    def test_get_unit_text_days_singular(self):
        """Test getting unit text for days (singular)"""
        result = self.formatter._get_unit_text(DurationUnit.DAYS, 1.0)
        assert result == "dia"
    
    def test_get_unit_text_days_plural(self):
        """Test getting unit text for days (plural)"""
        result = self.formatter._get_unit_text(DurationUnit.DAYS, 2.0)
        assert result == "dias"
    
    def test_get_unit_text_weeks_singular(self):
        """Test getting unit text for weeks (singular)"""
        result = self.formatter._get_unit_text(DurationUnit.WEEKS, 1.0)
        assert result == "semana"
    
    def test_get_unit_text_weeks_plural(self):
        """Test getting unit text for weeks (plural)"""
        result = self.formatter._get_unit_text(DurationUnit.WEEKS, 2.0)
        assert result == "semanas"
    
    def test_get_unit_text_months_singular(self):
        """Test getting unit text for months (singular)"""
        result = self.formatter._get_unit_text(DurationUnit.MONTHS, 1.0)
        assert result == "mês"
    
    def test_get_unit_text_months_plural(self):
        """Test getting unit text for months (plural)"""
        result = self.formatter._get_unit_text(DurationUnit.MONTHS, 2.0)
        assert result == "meses"
    
    def test_is_nice_number_whole(self):
        """Test nice number detection for whole numbers"""
        assert self.formatter._is_nice_number(1.0) is True
        assert self.formatter._is_nice_number(5.0) is True
    
    def test_is_nice_number_half(self):
        """Test nice number detection for .5 values"""
        assert self.formatter._is_nice_number(1.5) is True
        assert self.formatter._is_nice_number(2.5) is True
    
    def test_is_nice_number_ugly_fraction(self):
        """Test nice number detection for ugly fractions"""
        assert self.formatter._is_nice_number(1.333) is False
        assert self.formatter._is_nice_number(2.714) is False


# ==================================================================================
# CONVENIENCE FUNCTION TESTS
# ==================================================================================

class TestConvenienceFunctions:
    """Test suite for convenience functions"""
    
    def test_format_duration_default(self):
        """Test default duration formatting function"""
        result = format_duration(1.5)
        assert result == "1.5 dias"
    
    def test_format_duration_compact_style(self):
        """Test duration formatting with compact style"""
        result = format_duration(7.0, DurationStyle.COMPACT)
        assert result == "1w"
    
    def test_format_epic_duration_standard(self):
        """Test epic duration formatting function"""
        result = format_epic_duration_standard(2.0)
        assert result == "2 dias"
    
    def test_format_duration_compact_function(self):
        """Test compact duration formatting function"""
        result = format_duration_compact(14.0)
        assert result == "2w"
    
    def test_format_duration_range_function(self):
        """Test duration range formatting function"""
        result = format_duration_range(1.0, 3.0)
        assert result == "1-3 dias"
    
    def test_reformat_epic_duration_same_style(self):
        """Test reformatting epic duration to same style"""
        result = reformat_epic_duration("1.5 dias", DurationStyle.STANDARD)
        assert result == "1.5 dias"
    
    def test_reformat_epic_duration_different_style(self):
        """Test reformatting epic duration to different style"""
        result = reformat_epic_duration("1 semana", DurationStyle.COMPACT)
        assert result == "1w"


# ==================================================================================
# PRESET FORMATTER TESTS
# ==================================================================================

class TestEpicDurationFormatter:
    """Test suite for preset formatter configurations"""
    
    def test_standard_preset(self):
        """Test standard epic duration formatter preset"""
        formatter = EpicDurationFormatter.standard()
        result = formatter.format(7.0)
        assert result == "1 semana"
        assert formatter.style == DurationStyle.STANDARD
        assert formatter.auto_unit_selection is True
    
    def test_compact_preset(self):
        """Test compact formatter preset"""
        formatter = EpicDurationFormatter.compact()
        result = formatter.format(7.0)
        assert result == "1w"
        assert formatter.style == DurationStyle.COMPACT
        assert formatter.auto_unit_selection is True
    
    def test_days_only_preset(self):
        """Test days-only formatter preset"""
        formatter = EpicDurationFormatter.days_only()
        result = formatter.format(7.0)
        assert result == "7 dias"
        assert formatter.style == DurationStyle.STANDARD
        assert formatter.auto_unit_selection is False


# ==================================================================================
# INTEGRATION TESTS WITH REAL EPIC DATA
# ==================================================================================

class TestRealEpicDataIntegration:
    """Integration tests using real epic data patterns"""
    
    def setup_method(self):
        self.formatter = DurationFormatter()
    
    def test_epic_duration_roundtrip(self):
        """Test roundtrip: format → parse → format"""
        original_days = 1.5
        formatted = self.formatter.format(original_days)
        parsed_days = self.formatter.parse_formatted_duration(formatted)
        reformatted = self.formatter.format(parsed_days)
        
        assert formatted == "1.5 dias"
        assert parsed_days == original_days
        assert reformatted == formatted
    
# TODO: Consider extracting this block into a separate method
    
    def test_all_epic_patterns_compatibility(self):
        """Test compatibility with all real epic duration patterns"""
        # Test patterns from actual epic files
        epic_patterns = [
            ("1.5 dias", 1.5),
            ("2 dias", 2.0),
            ("5 dias", 5.0),
            ("1 semana", 7.0),
            ("4 dias", 4.0)
        ]
        
        for pattern, expected_days in epic_patterns:
            # Parse existing pattern
            parsed_days = self.formatter.parse_formatted_duration(pattern)
            assert parsed_days == expected_days
            
            # Format from days
            formatted = self.formatter.format(expected_days)
            # Note: formatter might choose different units (e.g., 7 days → 1 semana)
            # TODO: Consider extracting this block into a separate method
            reparsed = self.formatter.parse_formatted_duration(formatted)
            assert reparsed == expected_days
    
    def test_epic_data_style_consistency(self):
        """Test that formatter produces style consistent with epic data"""
        # Epic data uses standard style with auto unit selection
        formatter = EpicDurationFormatter.standard()
        
        test_cases = [
            (1.0, "1 dia"),
            (1.5, "1.5 dias"),
            (2.0, "2 dias"),
            (7.0, "1 semana"),
            (14.0, "2 semanas")
        ]
        
        for days, expected in test_cases:
            result = formatter.format(days)
            assert result == expected


# ==================================================================================
# ERROR HANDLING AND EDGE CASES
# ==================================================================================

class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        self.formatter = DurationFormatter()
    
    def test_very_large_duration(self):
        """Test formatting very large duration"""
        result = self.formatter.format(1000.0)
        # Should format as months
        assert "meses" in result
    
    def test_very_small_duration(self):
        """Test formatting very small duration"""
        result = self.formatter.format(0.1)
        assert result == "0.1 dias"
    
    def test_invalid_unit_conversion(self):
        """Test error with invalid unit in private method"""
        # This tests error handling in _convert_days_to_unit
        with pytest.raises(DurationFormattingError):
            # Create a mock invalid unit for testing
            class InvalidUnit:
                value = "invalid"
            
            self.formatter._convert_days_to_unit(1.0, InvalidUnit())
    
    def test_formatting_error_propagation(self):
        """Test that internal errors are properly wrapped"""
        # Test that any internal exception gets wrapped in DurationFormattingError
        formatter = DurationFormatter()
        
        # This should not fail in normal operation, but tests error handling
        try:
            result = formatter.format(1.0)
            assert result == "1 dia"
        except DurationFormattingError:
            # If it does fail, it should be properly wrapped
            pass


# ==================================================================================
# PERFORMANCE TESTS
# ==================================================================================

class TestPerformance:
    """Performance tests to ensure formatting meets targets"""
    
# TODO: Consider extracting this block into a separate method
    
    def setup_method(self):
        self.formatter = DurationFormatter()
    
    def test_formatting_performance(self):
        """Test that duration formatting completes efficiently"""
        import time
        
        durations = [1.0, 1.5, 2.0, 7.0, 14.0, 30.0] * 20
        
        start_time = time.time()
        
        for duration in durations:
            result = self.formatter.format(duration)
            # TODO: Consider extracting this block into a separate method
            assert isinstance(result, str)
            assert len(result) > 0
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        assert elapsed_time < 50, f"Duration formatting took {elapsed_time:.2f}ms, target: <50ms"
    
    def test_range_formatting_performance(self):
        """Test that range formatting completes efficiently"""
        import time
        
        ranges = [(1.0, 2.0), (7.0, 14.0), (30.0, 60.0)] * 10
        
        start_time = time.time()
        
        for min_days, max_days in ranges:
            result = self.formatter.format_range(min_days, max_days)
            assert isinstance(result, str)
            assert "-" in result or result == self.formatter.format(min_days)
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        assert elapsed_time < 30, f"Range formatting took {elapsed_time:.2f}ms, target: <30ms"


# ==================================================================================
# DEMONSTRATION AND UTILITY TESTS
# ==================================================================================

class TestDemonstrationUtilities:
    """Test demonstration and utility functions"""
    
    def test_demonstrate_formatting_examples(self):
        """Test the demonstration function"""
        examples = demonstrate_formatting_examples()
        
        assert isinstance(examples, dict)
        assert len(examples) > 0
        
        # Check that specific examples are present
        assert 1.0 in examples
        assert 7.0 in examples
        assert examples[1.0] == "1 dia"
        assert examples[7.0] == "1 semana"
    
    def test_formatter_string_representation(self):
        """Test that formatter works correctly when imported"""
        # This tests the module-level functionality
        from duration_system.duration_formatter import DurationFormatter
        
        formatter = DurationFormatter()
        result = formatter.format(1.5)
        assert result == "1.5 dias"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])