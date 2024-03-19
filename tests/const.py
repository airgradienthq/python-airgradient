"""Constants for tests."""

from importlib import metadata

WITHINGS_URL = "https://wbsapi.withings.net:443"

version = metadata.version("airgradient")

HEADERS = {
    "User-Agent": f"AioWithings/{version}",
    "Accept": "application/json, text/plain, */*",
    "Authorization": "Bearer test",
}
