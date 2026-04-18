"""Tests for sdk.datetime module."""

from datetime import time, timedelta

import pytest

from sdk.datetime import (
    time_in_milliseconds,
    time_in_seconds,
)


class TestTimeInMilliseconds:
    """Tests for time_in_milliseconds function."""
    
    def test_midnight_returns_zero(self):
        """Midnight should return 0 milliseconds."""
        result = time_in_milliseconds(time(0, 0, 0))
        assert result == 0
    
    def test_one_second_returns_1000(self):
        """One second should return 1000 milliseconds."""
        result = time_in_milliseconds(time(0, 0, 1))
        assert result == 1000
    
    def test_one_minute_returns_60000(self):
        """One minute should return 60000 milliseconds."""
        result = time_in_milliseconds(time(0, 1, 0))
        assert result == 60000
    
    def test_one_hour_returns_3600000(self):
        """One hour should return 3600000 milliseconds."""
        result = time_in_milliseconds(time(1, 0, 0))
        assert result == 3600000
    
    def test_complex_time(self):
        """Complex time should calculate correctly."""
        # 1:30:45.500 = 1*3600 + 30*60 + 45 + 0.5 = 5445.5 seconds
        result = time_in_milliseconds(time(1, 30, 45, 500000))
        expected = int((1 * 3600 + 30 * 60 + 45 + 0.5) * 1000)
        assert result == expected
    
    def test_max_time(self):
        """Maximum time (23:59:59.999999) should calculate correctly."""
        result = time_in_milliseconds(time(23, 59, 59, 999999))
        # 23*3600 + 59*60 + 59 + 0.999999 = 86399.999999 seconds
        expected = (23 * 3600 + 59 * 60 + 59 + 0.999999) * 1000
        assert result == pytest.approx(expected)


class TestTimeInSeconds:
    """Tests for time_in_seconds function."""
    
    def test_midnight_returns_zero(self):
        """Midnight should return 0 seconds."""
        result = time_in_seconds(time(0, 0, 0))
        assert result == 0.0
    
    def test_one_second_returns_one(self):
        """One second should return 1.0 seconds."""
        result = time_in_seconds(time(0, 0, 1))
        assert result == 1.0
    
    def test_one_minute_returns_60(self):
        """One minute should return 60.0 seconds."""
        result = time_in_seconds(time(0, 1, 0))
        assert result == 60.0
    
    def test_one_hour_returns_3600(self):
        """One hour should return 3600.0 seconds."""
        result = time_in_seconds(time(1, 0, 0))
        assert result == 3600.0
    
    def test_with_microseconds(self):
        """Time with microseconds should include fractional seconds."""
        result = time_in_seconds(time(0, 0, 1, 500000))
        assert result == 1.5
    
    def test_max_time(self):
        """Maximum time should calculate correctly."""
        result = time_in_seconds(time(23, 59, 59, 999999))
        expected = 23 * 3600 + 59 * 60 + 59 + 0.999999
        assert result == pytest.approx(expected, abs=1e-6)


class TestTimeConversionRoundTrip:
    """Tests for round-trip conversion between time formats."""
    
    def test_round_trip_seconds_to_milliseconds(self):
        """Converting to seconds then milliseconds should be consistent."""
        original = time(12, 30, 45, 123000)  # 123000 microseconds = 0.123 seconds
        seconds = time_in_seconds(original)
        milliseconds = time_in_milliseconds(original)
        
        assert milliseconds == int(seconds * 1000)
