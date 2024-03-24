"""Tests for the client."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import aiohttp
from aioresponses import CallbackResult, aioresponses
import pytest

from airgradient import AirGradientClient, AirGradientConnectionError, AirGradientError
from tests import load_fixture
from tests.const import MOCK_HOST, MOCK_URL

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
        status=200,
        headers={"Content-Type": "plain/text"},
        body="Yes",
    )
    with pytest.raises(AirGradientError):
        assert await client.get_current_measures()


async def test_timeout(
    responses: aioresponses,
) -> None:
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_: str, **_kwargs: Any) -> CallbackResult:
        """Response handler for this test."""
        await asyncio.sleep(2)
        return CallbackResult(body="Goodmorning!")

    responses.get(
        f"{MOCK_URL}/measures/current",
        callback=response_handler,
    )
    async with AirGradientClient(host=MOCK_HOST, request_timeout=1) as airgradient:
        with pytest.raises(AirGradientConnectionError):
            assert await airgradient.get_current_measures()


async def test_status(
    responses: aioresponses,
    client: AirGradientClient,
    snapshot: SnapshotAssertion,
) -> None:
    """Test status call."""
    responses.get(
        f"{MOCK_URL}/measures/current",
        status=200,
        body=load_fixture("current_measures.json"),
    )
    assert await client.get_current_measures() == snapshot
