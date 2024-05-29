"""Tests for the client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable

import aiohttp
from aiohttp.hdrs import METH_PUT
from aioresponses import aioresponses
import pytest

from airgradient import (
    AirGradientClient,
    AirGradientError,
    ConfigurationControl,
    LedBarMode,
    PmStandard,
    TemperatureUnit,
)
from tests import load_fixture
from tests.const import HEADERS, MOCK_HOST, MOCK_URL

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion


async def test_putting_in_own_session(
    responses: aioresponses,
) -> None:
    """Test putting in own session."""
    responses.get(
        f"{MOCK_URL}/measures/current",
        status=200,
        body=load_fixture("current_measures.json"),
    )
    async with aiohttp.ClientSession() as session:
        airgradient = AirGradientClient(session=session, host=MOCK_HOST)
        await airgradient.get_current_measures()
        assert airgradient.session is not None
        assert not airgradient.session.closed
        await airgradient.close()
        assert not airgradient.session.closed


async def test_creating_own_session(
    responses: aioresponses,
) -> None:
    """Test creating own session."""
    responses.get(
        f"{MOCK_URL}/measures/current",
        status=200,
        body=load_fixture("current_measures.json"),
    )
    airgradient = AirGradientClient(host=MOCK_HOST)
    await airgradient.get_current_measures()
    assert airgradient.session is not None
    assert not airgradient.session.closed
    await airgradient.close()
    assert airgradient.session.closed


async def test_unexpected_server_response(
    responses: aioresponses,
    client: AirGradientClient,
) -> None:
    """Test handling unexpected response."""
    responses.get(
        f"{MOCK_URL}/measures/current",
        status=404,
        headers={"Content-Type": "plain/text"},
        body="Yes",
    )
    with pytest.raises(AirGradientError):
        assert await client.get_current_measures()


@pytest.mark.parametrize(
    "fixture",
    ["current_measures.json", "measures_after_boot.json"],
)
async def test_current_fixtures(
    responses: aioresponses,
    client: AirGradientClient,
    snapshot: SnapshotAssertion,
    fixture: str,
) -> None:
    """Test status call."""
    responses.get(
        f"{MOCK_URL}/measures/current",
        status=200,
        body=load_fixture(fixture),
    )
    assert await client.get_current_measures() == snapshot


async def test_config(
    responses: aioresponses,
    client: AirGradientClient,
    snapshot: SnapshotAssertion,
) -> None:
    """Test config call."""
    responses.get(
        f"{MOCK_URL}/config",
        status=200,
        body=load_fixture("config.json"),
    )
    assert await client.get_config() == snapshot


@pytest.mark.parametrize(
    ("function", "expected_data"),
    [
        (
            lambda client: client.set_temperature_unit(TemperatureUnit.CELSIUS),
            {"temperatureUnit": "c"},
        ),
        (
            lambda client: client.set_pm_standard(PmStandard.UGM3),
            {"pmStandard": "ugm3"},
        ),
        (
            lambda client: client.set_configuration_control(ConfigurationControl.CLOUD),
            {"configurationControl": "cloud"},
        ),
        (
            lambda client: client.set_led_bar_mode(LedBarMode.CO2),
            {"ledBarMode": "co2"},
        ),
    ],
)
async def test_setting_config(
    responses: aioresponses,
    client: AirGradientClient,
    function: Callable[[AirGradientClient], Awaitable[None]],
    expected_data: dict[str, Any],
) -> None:
    """Test config call."""
    responses.put(
        f"{MOCK_URL}/config",
        status=200,
        body="Success",
        headers={"Content-Type": "plain/text"},
    )
    await function(client)
    responses.assert_called_once_with(
        f"{MOCK_URL}/config",
        METH_PUT,
        headers=HEADERS,
        json=expected_data,
    )
