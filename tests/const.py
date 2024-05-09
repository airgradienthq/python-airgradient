"""Constants for tests."""

from importlib import metadata

MOCK_HOST = "192.168.0.30"

MOCK_URL = f"http://{MOCK_HOST}"
version = metadata.version("airgradient")

HEADERS = {
    "User-Agent": f"PythonAirGradient/{version}",
    "Accept": "application/json",
}
