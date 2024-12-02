"""Asynchronous Python client for AirGradient."""

from collections.abc import AsyncGenerator, Generator

import aiohttp
from aioresponses import aioresponses
import pytest

from airgradient import AirGradientClient
from syrupy import SnapshotAssertion

from .syrupy import AirGradientSnapshotExtension


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the AirGradient extension."""
    return snapshot.use_extension(AirGradientSnapshotExtension)


@pytest.fixture
async def client() -> AsyncGenerator[AirGradientClient, None]:
    """Return a AirGradient client."""
    async with (
        aiohttp.ClientSession() as session,
        AirGradientClient(
            "192.168.0.30",
            session=session,
        ) as airgradient_client,
    ):
        yield airgradient_client


@pytest.fixture(name="responses")
def aioresponses_fixture() -> Generator[aioresponses, None, None]:
    """Return aioresponses fixture."""
    with aioresponses() as mocked_responses:
        yield mocked_responses
