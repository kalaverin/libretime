"""Global pytest configuration."""

import pytest


@pytest.fixture
def mock_datetime_now(mocker):
    """Mock datetime.now() for deterministic tests."""
    from datetime import datetime, timezone
    
    fixed_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    
    mock = mocker.patch("datetime.datetime")
    mock.now.return_value = fixed_time
    mock.utcnow.return_value = fixed_time
    
    return fixed_time
