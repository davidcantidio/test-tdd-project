"""
Test suite for DurationCalculator Engine

Comprehensive test coverage for duration calculation, parsing, and validation
functionality used in the Duration System implementation.

Target: ≥95% code coverage
"""

import pytest
from datetime import date, datetime, timedelta
from duration_system.duration_calculator import (
    DurationCalculator,
    DurationUnit,
    DateCalculationMode,
    DurationCalculationError,
    calculate_epic_duration,
    parse_epic_duration,
    validate_epic_dates
)


class TestDurationCalculator:
    """Test suite for DurationCalculator class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.calculator = DurationCalculator()
        self.business_calculator = DurationCalculator(DateCalculationMode.BUSINESS_DAYS)
    
    # ==================================================================================
    # DURATION CALCULATION TESTS
    # ==================================================================================
    
    def test_calculate_duration_days_basic(self):
        """Test basic duration calculation between dates"""
        start = date(2025, 1, 1)
        end = date(2025, 1, 3)
        
        duration = self.calculator.calculate_duration_days(start, end)
        assert duration == 2.0
    
    def test_calculate_duration_days_same_date(self):
        """Test duration calculation for same date"""
        start = date(2025, 1, 1)
        end = date(2025, 1, 1)
        
        duration = self.calculator.calculate_duration_days(start, end)
        assert duration == 0.0
    
    def test_calculate_duration_days_string_input(self):
        """Test duration calculation with string date inputs"""
        duration = self.calculator.calculate_duration_days("2025-01-01", "2025-01-08")
        assert duration == 7.0
    
    def test_calculate_duration_days_datetime_input(self):
        """Test duration calculation with datetime inputs"""
        start = datetime(2025, 1, 1, 10, 30)
        end = datetime(2025, 1, 3, 15, 45)
        
        duration = self.calculator.calculate_duration_days(start, end)
        assert duration == 2.0  # Only full days counted
    
    def test_calculate_duration_days_invalid_order(self):
        """Test error when start date is after end date"""
        start = date(2025, 1, 3)
        end = date(2025, 1, 1)
        
        with pytest.raises(DurationCalculationError) as exc_info:
            self.calculator.calculate_duration_days(start, end)
        assert "cannot be after" in str(exc_info.value)
    
    def test_calculate_duration_days_invalid_date_format(self):
        """Test error with invalid date format"""
        with pytest.raises(DurationCalculationError) as exc_info:
            self.calculator.calculate_duration_days("invalid-date", "2025-01-01")
        assert "Invalid date format" in str(exc_info.value)
    
    def test_calculate_duration_business_days(self):
        """Test business days calculation (excluding weekends)"""
        # Monday to Friday (5 business days)
        start = date(2025, 1, 6)  # Monday
        end = date(2025, 1, 10)   # Friday
        
        duration = self.business_calculator.calculate_duration_days(start, end)
        assert duration == 4.0  # Mon, Tue, Wed, Thu (Fri not included in range)
    
    def test_calculate_duration_business_days_with_weekend(self):
        """Test business days calculation spanning weekend"""
        # Friday to Tuesday (2 business days, skipping weekend)
        start = date(2025, 1, 3)  # Friday
        end = date(2025, 1, 7)    # Tuesday
        
        duration = self.business_calculator.calculate_duration_days(start, end)
        assert duration == 2.0  # Monday, Tuesday
    
    # ==================================================================================
    # END DATE CALCULATION TESTS
    # ==================================================================================
    
    def test_calculate_end_date_basic(self):
        """Test calculating end date from start date and duration"""
        start = date(2025, 1, 1)
        duration = 5.0
        
        end_date = self.calculator.calculate_end_date(start, duration)
        assert end_date == date(2025, 1, 6)
    
    def test_calculate_end_date_fractional_duration(self):
        """Test calculating end date with fractional duration"""
        start = date(2025, 1, 1)
        duration = 2.5  # Fractional part ignored for date calculation
        
        end_date = self.calculator.calculate_end_date(start, duration)
        assert end_date == date(2025, 1, 3)  # 2 full days
    
    def test_calculate_end_date_zero_duration(self):
        """Test calculating end date with zero duration"""
        start = date(2025, 1, 1)
        duration = 0.0
        
        end_date = self.calculator.calculate_end_date(start, duration)
        assert end_date == start
    
    def test_calculate_end_date_negative_duration(self):
        """Test error with negative duration"""
        start = date(2025, 1, 1)
        duration = -1.0
        
        with pytest.raises(DurationCalculationError) as exc_info:
            self.calculator.calculate_end_date(start, duration)
        assert "cannot be negative" in str(exc_info.value)
    
    def test_calculate_end_date_business_days(self):
        """Test calculating end date with business days"""
        start = date(2025, 1, 6)  # Monday
        duration = 3.0  # 3 business days
        
        end_date = self.business_calculator.calculate_end_date(start, duration)
        assert end_date == date(2025, 1, 9)  # Thursday
    
    def test_calculate_end_date_string_input(self):
        """Test calculating end date with string date input"""
        end_date = self.calculator.calculate_end_date("2025-01-01", 7.0)
        assert end_date == date(2025, 1, 8)
    
    # ==================================================================================
    # DURATION STRING PARSING TESTS
    # ==================================================================================
    
    def test_parse_duration_string_days_singular(self):
        """Test parsing '1 dia'"""
        value, unit = self.calculator.parse_duration_string("1 dia")
        assert value == 1.0
        assert unit == DurationUnit.DAYS
    
    def test_parse_duration_string_days_plural(self):
        """Test parsing '2 dias'"""
        value, unit = self.calculator.parse_duration_string("2 dias")
        assert value == 2.0
        assert unit == DurationUnit.DAYS
    
    def test_parse_duration_string_fractional_days(self):
        """Test parsing '1.5 dias' (real epic data format)"""
        value, unit = self.calculator.parse_duration_string("1.5 dias")
        assert value == 1.5
        assert unit == DurationUnit.DAYS
    
    def test_parse_duration_string_weeks_singular(self):
        """Test parsing '1 semana'"""
        value, unit = self.calculator.parse_duration_string("1 semana")
        assert value == 1.0
        assert unit == DurationUnit.WEEKS
    
    def test_parse_duration_string_weeks_plural(self):
        """Test parsing '2 semanas'"""
        value, unit = self.calculator.parse_duration_string("2 semanas")
        assert value == 2.0
        assert unit == DurationUnit.WEEKS
    
    def test_parse_duration_string_case_insensitive(self):
        """Test parsing with different cases"""
        value, unit = self.calculator.parse_duration_string("5 DIAS")
        assert value == 5.0
        assert unit == DurationUnit.DAYS
    
    def test_parse_duration_string_extra_whitespace(self):
        """Test parsing with extra whitespace"""
        value, unit = self.calculator.parse_duration_string("  3.5   dias  ")
        assert value == 3.5
        assert unit == DurationUnit.DAYS
    
    def test_parse_duration_string_invalid_format(self):
        """Test error with invalid duration format"""
        with pytest.raises(DurationCalculationError) as exc_info:
            self.calculator.parse_duration_string("invalid format")
        assert "Invalid duration format" in str(exc_info.value)
    
    def test_parse_duration_string_unsupported_unit(self):
        """Test error with unsupported unit"""
        # This should not happen with current regex, but test for robustness
        with pytest.raises(DurationCalculationError):
            # Patch the regex to allow invalid unit for testing
            self.calculator._duration_pattern = __import__('re').compile(r'^(\d+(?:\.\d+)?)\s*(invalid)$')
            self.calculator.parse_duration_string("1 invalid")
    
    # ==================================================================================
    # DURATION CONVERSION TESTS
    # ==================================================================================
    
    def test_duration_to_days_days_unit(self):
        """Test converting days unit to days"""
        days = self.calculator.duration_to_days(3.5, DurationUnit.DAYS)
        assert days == 3.5
    
    def test_duration_to_days_weeks_unit(self):
        """Test converting weeks unit to days"""
        days = self.calculator.duration_to_days(2.0, DurationUnit.WEEKS)
        assert days == 14.0
    
    def test_duration_to_days_months_unit(self):
        """Test converting months unit to days"""
        days = self.calculator.duration_to_days(1.0, DurationUnit.MONTHS)
        assert days == 30.0
    
    def test_parse_and_convert_to_days_real_epic_formats(self):
        """Test parsing and converting real epic duration formats"""
        # Test formats from real epic data
        test_cases = [
            ("1.5 dias", 1.5),
            ("2 dias", 2.0),
            ("5 dias", 5.0),
            ("1 semana", 7.0),
            ("4 dias", 4.0)
        ]
        
        for duration_str, expected_days in test_cases:
            days = self.calculator.parse_and_convert_to_days(duration_str)
            assert days == expected_days
    
    # ==================================================================================
    # DATE CONSISTENCY VALIDATION TESTS
    # ==================================================================================
    
    def test_validate_date_consistency_valid_planned_dates(self):
        """Test validation with valid planned dates"""
        result = self.calculator.validate_date_consistency(
            planned_start="2025-01-01",
            planned_end="2025-01-08",
            duration_days=7.0
        )
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert result["calculated_durations"]["planned"] == 7.0
    
    def test_validate_date_consistency_invalid_planned_order(self):
        """Test validation with invalid planned date order"""
        result = self.calculator.validate_date_consistency(
            planned_start="2025-01-08",
            planned_end="2025-01-01"
        )
        
        assert result["is_valid"] is False
        assert any("cannot be after" in error for error in result["errors"])
    
    def test_validate_date_consistency_duration_mismatch(self):
        """Test validation with duration mismatch"""
        result = self.calculator.validate_date_consistency(
            planned_start="2025-01-01",
            planned_end="2025-01-08",
            duration_days=5.0  # Expected 5, actual 7
        )
        
        assert result["is_valid"] is True  # Still valid, just warning
        assert any("differs from expected" in warning for warning in result["warnings"])
    
    def test_validate_date_consistency_actual_dates(self):
        """Test validation with actual dates"""
        result = self.calculator.validate_date_consistency(
            actual_start="2025-01-02",
            actual_end="2025-01-10"
        )
        
        assert result["is_valid"] is True
        assert result["calculated_durations"]["actual"] == 8.0
    
    def test_validate_date_consistency_invalid_actual_order(self):
        """Test validation with invalid actual date order"""
        result = self.calculator.validate_date_consistency(
            actual_start="2025-01-10",
            actual_end="2025-01-02"
        )
        
        assert result["is_valid"] is False
        assert any("cannot be after" in error for error in result["errors"])
    
    def test_validate_date_consistency_early_start(self):
        """Test validation when actual start is before planned"""
        result = self.calculator.validate_date_consistency(
            planned_start="2025-01-05",
            actual_start="2025-01-01"
        )
        
        assert result["is_valid"] is True  # Valid but with warning
        assert any("before planned start" in warning for warning in result["warnings"])
    
    def test_validate_date_consistency_overrun(self):
        """Test validation when actual end is after planned (overrun)"""
        result = self.calculator.validate_date_consistency(
            planned_end="2025-01-05",
            actual_end="2025-01-10"
        )
        
        assert result["is_valid"] is True  # Valid but with warning
        assert any("overrun" in warning for warning in result["warnings"])
    
    def test_validate_date_consistency_invalid_date_format(self):
        """Test validation with invalid date format"""
        result = self.calculator.validate_date_consistency(
            planned_start="invalid-date"
        )
        
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
    
    # ==================================================================================
    # PRIVATE METHOD TESTS
    # ==================================================================================
    
    def test_normalize_date_date_object(self):
        """Test date normalization with date object"""
        input_date = date(2025, 1, 1)
        normalized = self.calculator._normalize_date(input_date)
        assert normalized == input_date
    
    def test_normalize_date_datetime_object(self):
        """Test date normalization with datetime object"""
        input_datetime = datetime(2025, 1, 1, 15, 30)
        normalized = self.calculator._normalize_date(input_datetime)
        assert normalized == date(2025, 1, 1)
    
    def test_normalize_date_string_formats(self):
        """Test date normalization with various string formats"""
        test_cases = [
            ("2025-01-01", date(2025, 1, 1)),
            ("01/01/2025", date(2025, 1, 1)),
            ("01/01/2025", date(2025, 1, 1))
        ]
        
        for date_str, expected in test_cases:
            normalized = self.calculator._normalize_date(date_str)
            assert normalized == expected
    
    def test_normalize_date_invalid_string(self):
        """Test date normalization with invalid string"""
        with pytest.raises(ValueError):
            self.calculator._normalize_date("invalid-date-format")
    
    def test_normalize_date_invalid_type(self):
        """Test date normalization with invalid type"""
        with pytest.raises(TypeError):
            self.calculator._normalize_date(123)
    
    def test_calculate_business_days_weekend_span(self):
        """Test business days calculation spanning weekend"""
        # Friday to Monday
        start = date(2025, 1, 3)  # Friday
        end = date(2025, 1, 6)    # Monday
        
        business_days = self.calculator._calculate_business_days(start, end)
        assert business_days == 1.0  # Only Monday
    
    def test_add_business_days_skip_weekend(self):
        """Test adding business days that skip weekend"""
        # Friday + 1 business day = Monday
        start = date(2025, 1, 3)  # Friday
        result = self.calculator._add_business_days(start, 1.0)
        assert result == date(2025, 1, 6)  # Monday


# ==================================================================================
# CONVENIENCE FUNCTION TESTS
# ==================================================================================

class TestConvenienceFunctions:
    """Test suite for convenience functions"""
    
    def test_calculate_epic_duration(self):
        """Test convenience function for epic duration calculation"""
        duration = calculate_epic_duration("2025-01-01", "2025-01-08")
        assert duration == 7.0
    
    def test_parse_epic_duration(self):
        """Test convenience function for epic duration parsing"""
        days = parse_epic_duration("1.5 dias")
        assert days == 1.5
    
    def test_validate_epic_dates(self):
        """Test convenience function for epic date validation"""
        result = validate_epic_dates(
            planned_start="2025-01-01",
            planned_end="2025-01-08",
            duration_str="1 semana"
        )
        
        assert result["is_valid"] is True
        assert result["calculated_durations"]["planned"] == 7.0


# ==================================================================================
# INTEGRATION TESTS WITH REAL EPIC DATA
# ==================================================================================

class TestRealEpicDataIntegration:
    """Integration tests using real epic data patterns"""
    
    def setup_method(self):
        self.calculator = DurationCalculator()
    
    def test_epic_5_duration_pattern(self):
        """Test duration pattern from epico_5.json: '1.5 dias'"""
        duration_str = "1.5 dias"
        days = self.calculator.parse_and_convert_to_days(duration_str)
        assert days == 1.5
        
        # Test end date calculation
        start_date = date(2025, 1, 1)
        end_date = self.calculator.calculate_end_date(start_date, days)
        assert end_date == date(2025, 1, 2)  # 1 full day (1.5 truncated)
    
    def test_epic_3_duration_pattern(self):
        """Test duration pattern from epico_3.json: '1 semana'"""
        duration_str = "1 semana"
        days = self.calculator.parse_and_convert_to_days(duration_str)
        assert days == 7.0
        
        # Test timeline calculation
        start_date = date(2025, 1, 1)
        end_date = self.calculator.calculate_end_date(start_date, days)
        assert end_date == date(2025, 1, 8)
    
    def test_epic_duration_patterns_comprehensive(self):
        """Test all duration patterns found in real epic data"""
        test_patterns = [
            ("1.5 dias", 1.5),   # epico_5.json, epico_6.json
            ("2 dias", 2.0),     # epico_0.json
            ("5 dias", 5.0),     # epico_2.json
            ("1 semana", 7.0),   # epico_3.json
            ("4 dias", 4.0)      # epico_4.json
        ]
        
        for duration_str, expected_days in test_patterns:
            calculated_days = self.calculator.parse_and_convert_to_days(duration_str)
            assert calculated_days == expected_days, f"Failed for pattern: {duration_str}"
    
    def test_epic_timeline_simulation(self):
        """Simulate complete epic timeline with real data"""
        # Simulate Epic 5: Cache Management (1.5 dias)
        duration_str = "1.5 dias"
        planned_start = date(2025, 8, 13)
        
        # Parse duration and calculate end date
        duration_days = self.calculator.parse_and_convert_to_days(duration_str)
        planned_end = self.calculator.calculate_end_date(planned_start, duration_days)
        
        # Calculate actual duration between dates (will be 1.0 due to truncation)
        actual_calculated_duration = self.calculator.calculate_duration_days(planned_start, planned_end)
        
        # Validate consistency - should have warning about duration mismatch
        validation = self.calculator.validate_date_consistency(
            planned_start=planned_start,
            planned_end=planned_end,
            duration_days=duration_days
        )
        
        assert validation["is_valid"] is True
        assert validation["calculated_durations"]["planned"] == actual_calculated_duration
        assert planned_end == date(2025, 8, 14)  # 1 day later (1.5 truncated)
        # Should have warning about duration mismatch due to truncation
        assert any("differs from expected" in warning for warning in validation["warnings"])


# ==================================================================================
# ERROR HANDLING AND EDGE CASES
# ==================================================================================

class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        self.calculator = DurationCalculator()
    
    def test_empty_duration_string(self):
        """Test error with empty duration string"""
        with pytest.raises(DurationCalculationError):
            self.calculator.parse_duration_string("")
    
    def test_none_date_input(self):
        """Test error with None date input"""
        with pytest.raises(DurationCalculationError):
            self.calculator.calculate_duration_days(None, date.today())
    
    def test_very_large_duration(self):
        """Test handling of very large duration values"""
        large_duration = 10000.0
        start_date = date(2025, 1, 1)
        
        # Should not raise error
        end_date = self.calculator.calculate_end_date(start_date, large_duration)
        assert isinstance(end_date, date)
    
    def test_zero_value_duration_string(self):
        """Test parsing zero duration"""
        value, unit = self.calculator.parse_duration_string("0 dias")
        assert value == 0.0
        assert unit == DurationUnit.DAYS
    
    def test_validation_with_all_none_values(self):
        """Test validation when all date values are None"""
        result = self.calculator.validate_date_consistency()
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["calculated_durations"]) == 0


# ==================================================================================
# PERFORMANCE TESTS
# ==================================================================================

class TestPerformance:
    """Performance tests to ensure duration calculations meet targets"""
    
    def setup_method(self):
        self.calculator = DurationCalculator()
    
    def test_duration_calculation_performance(self):
        """Test that duration calculation completes within 10ms target"""
        import time
        
        start_time = time.time()
        
        # Perform multiple calculations using timedelta to avoid invalid dates
        base_start = date(2025, 1, 1)
        for i in range(100):
            start_date = base_start
            end_date = base_start + timedelta(days=i)
            duration = self.calculator.calculate_duration_days(start_date, end_date)
            assert duration == i
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        assert elapsed_time < 100, f"Duration calculation took {elapsed_time:.2f}ms, target: <100ms"
    
    def test_duration_parsing_performance(self):
        """Test that duration parsing completes efficiently"""
        import time
        
        duration_strings = ["1.5 dias", "2 dias", "1 semana", "5 dias", "4 dias"] * 20
        
        start_time = time.time()
        
        for duration_str in duration_strings:
            days = self.calculator.parse_and_convert_to_days(duration_str)
            assert days > 0
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        assert elapsed_time < 50, f"Duration parsing took {elapsed_time:.2f}ms, target: <50ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])