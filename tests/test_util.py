"""Asynchronous Python client for Withings."""

from airgradient.util import get_measurement, get_measurement_from_dict


def test_measurement() -> None:
    """Test measurement."""
    assert get_measurement(20, -1) == 2


def test_measurement_from_dict() -> None:
    """Test measurement."""
    assert get_measurement_from_dict({"value": 20, "unit": -1}) == 2
