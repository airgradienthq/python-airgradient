"""Asynchronous Python client for AirGradient."""


class AirGradientError(Exception):
    """Generic exception."""


class AirGradientConnectionError(AirGradientError):
    """AirGradient connection exception."""
