"""Tests for sdk.compat module."""

import pytest
from sdk.compat import UTC


class TestUTC:
    """Tests for UTC timezone compatibility."""
    
    def test_utc_is_singleton(self):
        """UTC should be a singleton timezone instance."""
        from datetime import timezone
        
        assert UTC is timezone.utc
    
    def test_utc_offset_is_zero(self):
        """UTC offset should be zero."""
        from datetime import timedelta
        
        assert UTC.utcoffset(None) == timedelta(0)
        assert UTC.dst(None) is None
