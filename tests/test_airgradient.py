"""Tests for the client."""

from __future__ import annotations

import aiohttp
from aioresponses import aioresponses

from airgradient import AirGradientClient
from tests import load_fixture
from tests.const import MOCK_HOST, MOCK_URL


async def test_putting_in_own_session(
    responses: aioresponses,
) -> None:
    """Test putting in own session."""
    responses.get(
        f"{MOCK_URL}/status",
        status=200,
        body=load_fixture("status.json"),
    )
    async with aiohttp.ClientSession() as session:
        airgradient = AirGradientClient(session=session, host=MOCK_HOST)
        await airgradient.get_status()
        assert airgradient.session is not None
        assert not airgradient.session.closed
        await airgradient.close()
        assert not airgradient.session.closed
