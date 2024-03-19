"""Asynchronous Python client for Withings."""

from typing import AsyncGenerator, Generator

import aiohttp
from aioresponses import aioresponses
import pytest

from airgradient import WithingsClient
from syrupy import SnapshotAssertion

from .syrupy import WithingsSnapshotExtension


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Withings extension."""
    return snapshot.use_extension(WithingsSnapshotExtension)


@pytest.fixture(name="withings_client")
async def client() -> AsyncGenerator[WithingsClient, None]:
    """Return a Withings client."""
    async with aiohttp.ClientSession() as session, WithingsClient(
        session=session,
    ) as withings_client:
        yield withings_client


@pytest.fixture(name="authenticated_client")
async def authenticated_client(
    withings_client: WithingsClient,
) -> WithingsClient:
    """Return an authenticated Withings client."""
    withings_client.authenticate("test")
    return withings_client


@pytest.fixture(name="responses")
def aioresponses_fixture() -> Generator[aioresponses, None, None]:
    """Return aioresponses fixture."""
    with aioresponses() as mocked_responses:
        yield mocked_responses
