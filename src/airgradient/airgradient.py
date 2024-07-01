"""Asynchronous Python client for AirGradient."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from importlib import metadata
import socket
from typing import TYPE_CHECKING, Any

from aiohttp import ClientError, ClientResponseError, ClientSession
from aiohttp.hdrs import METH_GET, METH_PUT
from yarl import URL

from .exceptions import AirGradientConnectionError
from .models import (
    Config,
    ConfigurationControl,
    LedBarMode,
    Measures,
    PmStandard,
    TemperatureUnit,
)

if TYPE_CHECKING:
    from typing_extensions import Self


VERSION = metadata.version(__package__)


@dataclass
class AirGradientClient:
    """Main class for handling connections with AirGradient."""

    host: str
    session: ClientSession | None = None
    request_timeout: int = 10
    _close_session: bool = False

    async def _request(
        self,
        uri: str,
        *,
        method: str = METH_GET,
        data: dict[str, Any] | None = None,
    ) -> str:
        """Handle a request to AirGradient."""
        url = URL.build(scheme="http", host=self.host).joinpath(uri)

        headers = {
            "User-Agent": f"PythonAirGradient/{VERSION}",
            "Accept": "application/json",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(
                    method,
                    url,
                    headers=headers,
                    json=data,
                )
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to the device"
            raise AirGradientConnectionError(msg) from exception
        except (
            ClientError,
            ClientResponseError,
            socket.gaierror,
        ) as exception:
            msg = "Error occurred while communicating with the device"
            raise AirGradientConnectionError(msg) from exception

        if response.status != 200:
            content_type = response.headers.get("Content-Type", "")
            text = await response.text()
            msg = "Unexpected response from AirGradient"
            raise AirGradientConnectionError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        return await response.text()

    async def get_current_measures(self) -> Measures:
        """Get current measures from AirGradient."""
        response = await self._request("measures/current")
        return Measures.from_json(response)

    async def get_config(self) -> Config:
        """Get config from AirGradient device."""
        response = await self._request("config")
        return Config.from_json(response)

    async def _set_config(self, field: str, value: Any) -> None:
        """Set config on AirGradient device."""
        await self._request("config", method=METH_PUT, data={field: value})

    async def set_pm_standard(self, pm_standard: PmStandard) -> None:
        """Set PM standard on AirGradient device."""
        await self._set_config("pmStandard", pm_standard)

    async def set_temperature_unit(self, temperature_unit: TemperatureUnit) -> None:
        """Set temperature unit on AirGradient device."""
        await self._set_config("temperatureUnit", temperature_unit)

    async def set_configuration_control(
        self, configuration_control: ConfigurationControl
    ) -> None:
        """Set configuration control on AirGradient device."""
        await self._set_config("configurationControl", configuration_control)

    async def set_led_bar_mode(self, led_bar_mode: LedBarMode) -> None:
        """Set LED bar mode on AirGradient device."""
        await self._set_config("ledBarMode", led_bar_mode)

    async def request_co2_calibration(self) -> None:
        """Request CO2 calibration on AirGradient device."""
        await self._set_config("co2CalibrationRequested", value=True)

    async def request_led_bar_test(self) -> None:
        """Request LED bar test on AirGradient device."""
        await self._set_config("ledBarTestRequested", value=True)

    async def set_display_brightness(self, brightness: int) -> None:
        """Set display brightness on AirGradient device."""
        await self._set_config("displayBrightness", brightness)

    async def set_led_bar_brightness(self, brightness: int) -> None:
        """Set LED bar brightness on AirGradient device."""
        await self._set_config("ledBarBrightness", brightness)

    async def enable_sharing_data(self, *, enable: bool) -> None:
        """Enable or disable sharing data on AirGradient device."""
        await self._set_config("postDataToAirGradient", value=enable)

    async def set_co2_automatic_baseline_calibration(self, days: int) -> None:
        """Set CO2 automatic baseline calibration on AirGradient device."""
        await self._set_config("abcDays", days)

    async def set_nox_learning_offset(self, offset: int) -> None:
        """Set NOx learning offset on AirGradient device."""
        await self._set_config("noxLearningOffset", offset)

    async def set_tvoc_learning_offset(self, offset: int) -> None:
        """Set TVOC learning offset on AirGradient device."""
        await self._set_config("tvocLearningOffset", offset)

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The AirGradientClient object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()
