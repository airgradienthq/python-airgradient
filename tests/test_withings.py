"""Asynchronous Python client for Withings."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from typing import TYPE_CHECKING, Any

import aiohttp
from aiohttp.hdrs import METH_POST
from aioresponses import CallbackResult, aioresponses
import pytest

from airgradient import (
    ActivityDataFields,
    MeasurementType,
    NotificationCategory,
    SleepDataFields,
    SleepSummaryDataFields,
    WebhookCall,
    WithingsAuthenticationFailedError,
    WithingsBadStateError,
    WithingsClient,
    WithingsConnectionError,
    WithingsError,
    WithingsErrorOccurredError,
    WithingsInvalidParamsError,
    WithingsTooManyRequestsError,
    WithingsUnauthorizedError,
    WithingsUnknownStatusError,
    WorkoutDataFields,
    get_measurement_type_from_notification_category,
)

from . import load_fixture
from .const import HEADERS, WITHINGS_URL

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion


async def test_putting_in_own_session(
    responses: aioresponses,
) -> None:
    """Test putting in own session."""
    responses.post(
        f"{WITHINGS_URL}/v2/user",
        status=200,
        body=load_fixture("device.json"),
    )
    async with aiohttp.ClientSession() as session:
        withings = WithingsClient(session=session)
        withings.authenticate("test")
        await withings.get_devices()
        assert withings.session is not None
        assert not withings.session.closed
        await withings.close()
        assert not withings.session.closed


async def test_creating_own_session(
    responses: aioresponses,
) -> None:
    """Test creating own session."""
    responses.post(
        f"{WITHINGS_URL}/v2/user",
        status=200,
        body=load_fixture("device.json"),
    )
    withings = WithingsClient()
    withings.authenticate("test")
    await withings.get_devices()
    assert withings.session is not None
    assert not withings.session.closed
    await withings.close()
    assert withings.session.closed


async def test_refresh_token() -> None:
    """Test refreshing token."""

    async def _get_token() -> str:
        return "token"

    async with WithingsClient() as withings:
        assert withings._token is None  # pylint: disable=protected-access
        await withings.refresh_token()
        assert withings._token is None  # pylint: disable=protected-access

        withings.refresh_token_function = _get_token
        await withings.refresh_token()

        assert withings._token == "token"  # pylint: disable=protected-access


async def test_unexpected_server_response(
    responses: aioresponses,
    authenticated_client: WithingsClient,
) -> None:
    """Test handling unexpected response."""
    responses.post(
        f"{WITHINGS_URL}/v2/user",
        status=200,
        headers={"Content-Type": "plain/text"},
        body="Yes",
    )
    with pytest.raises(WithingsError):
        assert await authenticated_client.get_devices()


async def test_timeout(
    responses: aioresponses,
) -> None:
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_: str, **_kwargs: Any) -> CallbackResult:
        """Response handler for this test."""
        await asyncio.sleep(2)
        return CallbackResult(body="Goodmorning!")

    responses.post(
        f"{WITHINGS_URL}/v2/user",
        callback=response_handler,
    )
    async with WithingsClient(request_timeout=1) as withings:
        with pytest.raises(WithingsConnectionError):
            assert await withings.get_devices()


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (100, WithingsAuthenticationFailedError),
        (201, WithingsInvalidParamsError),
        (214, WithingsUnauthorizedError),
        (215, WithingsErrorOccurredError),
        (522, WithingsConnectionError),
        (524, WithingsBadStateError),
        (601, WithingsTooManyRequestsError),
        (-1, WithingsUnknownStatusError),
        (None, WithingsUnknownStatusError),
    ],
)
async def test_error_codes(
    responses: aioresponses,
    authenticated_client: WithingsClient,
    status: int | None,
    error: type[Exception],
) -> None:
    """Test error codes from withings."""
    response_data = json.loads(load_fixture("device.json"))
    response_data["status"] = status

    responses.post(
        f"{WITHINGS_URL}/v2/user",
        status=200,
        body=json.dumps(response_data),
    )
    with pytest.raises(error):
        assert await authenticated_client.get_devices()


async def test_get_activities_since(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving activities."""
    responses.post(
        f"{WITHINGS_URL}/v2/measure",
        status=200,
        body=load_fixture("activity.json"),
    )
    response = await authenticated_client.get_activities_since(
        datetime.fromtimestamp(1609559200, tz=timezone.utc),
        activity_data_fields=[ActivityDataFields.DISTANCE],
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/measure",
        METH_POST,
        headers=HEADERS,
        data={
            "lastupdate": 1609559200,
            "action": "getactivity",
            "data_fields": "distance",
        },
    )


async def test_get_activities_period(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving activities."""
    responses.post(
        f"{WITHINGS_URL}/v2/measure",
        status=200,
        body=load_fixture("activity.json"),
    )
    response = await authenticated_client.get_activities_in_period(
        start_date=datetime.fromtimestamp(1609459200, tz=timezone.utc),
        end_date=datetime.fromtimestamp(1609559200, tz=timezone.utc),
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/measure",
        METH_POST,
        headers=HEADERS,
        data={
            "action": "getactivity",
            "startdateymd": "2021-01-01 00:00:00+00:00",
            "enddateymd": "2021-01-02 03:46:40+00:00",
        },
    )


async def test_get_devices(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving devices."""
    responses.post(
        f"{WITHINGS_URL}/v2/user",
        status=200,
        body=load_fixture("device.json"),
    )
    response = await authenticated_client.get_devices()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/user",
        METH_POST,
        headers=HEADERS,
        data={"action": "getdevice"},
    )


async def test_get_new_device(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test retrieving devices that aren't known yet."""
    responses.post(
        f"{WITHINGS_URL}/v2/user",
        status=200,
        body=load_fixture("new_device.json"),
    )
    response = await authenticated_client.get_devices()
    assert response == snapshot
    assert (
        "Futuristic device is an unsupported value for <enum 'DeviceType'>,"
        " please report this at https://github.com/joostlek/python-withings/issues"
        in caplog.text
    )
    assert (
        "696969 is an unsupported value for <enum 'DeviceModel'>, please report"
        " this at https://github.com/joostlek/python-withings/issues" in caplog.text
    )


@pytest.mark.parametrize(
    "fixture",
    [
        "goals",
        "goals_1",
        "goals_2",
        "no_goals",
    ],
)
async def test_get_goals(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
    fixture: str,
) -> None:
    """Test retrieving goals."""
    responses.post(
        f"{WITHINGS_URL}/v2/user",
        status=200,
        body=load_fixture(f"{fixture}.json"),
    )
    response = await authenticated_client.get_goals()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/user",
        METH_POST,
        headers=HEADERS,
        data={"action": "getgoals"},
    )


async def test_get_measurement_since(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving measurements."""
    responses.post(
        f"{WITHINGS_URL}/measure",
        status=200,
        body=load_fixture("measurement.json"),
    )
    response = await authenticated_client.get_measurement_since(
        datetime.fromtimestamp(1609459200, tz=timezone.utc),
        measurement_types=[MeasurementType.WEIGHT],
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/measure",
        METH_POST,
        headers=HEADERS,
        data={"action": "getmeas", "lastupdate": 1609459200, "meastypes": "1"},
    )


async def test_get_measurement_period(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving measurements."""
    responses.post(
        f"{WITHINGS_URL}/measure",
        status=200,
        body=load_fixture("measurement.json"),
    )
    response = await authenticated_client.get_measurement_in_period(
        start_date=datetime.fromtimestamp(1609459200, tz=timezone.utc),
        end_date=datetime.fromtimestamp(1609559200, tz=timezone.utc),
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/measure",
        METH_POST,
        headers=HEADERS,
        data={"action": "getmeas", "startdate": 1609459200, "enddate": 1609559200},
    )


async def test_subscribing(
    responses: aioresponses,
    authenticated_client: WithingsClient,
) -> None:
    """Test subscribing to webhook updates."""
    responses.post(
        f"{WITHINGS_URL}/notify",
        status=200,
        body=load_fixture("notify_subscribe.json"),
    )
    await authenticated_client.subscribe_notification(
        "https://test.com/callback",
        NotificationCategory.PRESSURE,
    )
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/notify",
        METH_POST,
        headers=HEADERS,
        data={
            "action": "subscribe",
            "callbackurl": "https://test.com/callback",
            "appli": 4,
        },
    )


async def test_revoking(
    responses: aioresponses,
    authenticated_client: WithingsClient,
) -> None:
    """Test subscribing to webhook updates."""
    responses.post(
        f"{WITHINGS_URL}/notify",
        status=200,
        body=load_fixture("notify_revoke.json"),
    )
    await authenticated_client.revoke_notification_configurations(
        "https://test.com/callback",
        NotificationCategory.PRESSURE,
    )
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/notify",
        METH_POST,
        headers=HEADERS,
        data={
            "action": "revoke",
            "callbackurl": "https://test.com/callback",
            "appli": 4,
        },
    )


async def test_list_subscriptions(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving subscriptions."""
    responses.post(
        f"{WITHINGS_URL}/notify",
        status=200,
        body=load_fixture("notify_list.json"),
    )
    response = await authenticated_client.list_notification_configurations(
        NotificationCategory.WEIGHT,
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/notify",
        METH_POST,
        headers=HEADERS,
        data={"action": "list", "appli": 1},
    )


async def test_list_all_subscriptions(
    responses: aioresponses,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving all subscriptions."""
    responses.post(
        f"{WITHINGS_URL}/notify",
        status=200,
        body=load_fixture("notify_list.json"),
    )
    response = await authenticated_client.list_notification_configurations()
    assert response
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/notify",
        METH_POST,
        headers=HEADERS,
        data={"action": "list"},
    )


@pytest.mark.parametrize(
    "notification_category",
    list(NotificationCategory),
    ids=[nc.name for nc in NotificationCategory],
)
async def test_measurement_points_to_get(
    notification_category: NotificationCategory,
    snapshot: SnapshotAssertion,
) -> None:
    """Test if we receive the right updated measurement points."""
    assert (
        get_measurement_type_from_notification_category(notification_category)
        == snapshot
    )


async def test_webhook_object(snapshot: SnapshotAssertion) -> None:
    """Test if the webhook call transforms in a good object."""
    data = {
        "userid": 12345,
        "appli": 1,
        "startdate": 1530576000,
        "enddate": 1530698753,
    }
    assert WebhookCall.from_api(data) == snapshot


async def test_get_sleep(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving sleep."""
    responses.post(
        f"{WITHINGS_URL}/v2/sleep",
        status=200,
        body=load_fixture("sleep.json"),
    )
    response = await authenticated_client.get_sleep(
        datetime.fromtimestamp(0, tz=timezone.utc),
        datetime.fromtimestamp(1609559200, tz=timezone.utc),
        [
            SleepDataFields.HEART_RATE,
            SleepDataFields.RESPIRATION_RATE,
            SleepDataFields.SNORING,
            SleepDataFields.HEART_RATE_VARIABILITY,
            SleepDataFields.HEART_RATE_VARIABILITY_2,
            SleepDataFields.MOVEMENT_SCORE,
        ],
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/sleep",
        METH_POST,
        headers=HEADERS,
        data={
            "action": "get",
            "startdate": 0,
            "enddate": 1609559200,
            "data_fields": "hr,rr,snoring,sdnn_1,rmssd,mvt_score",
        },
    )


async def test_get_sleep_without_data_fields(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving sleep without datafields."""
    responses.post(
        f"{WITHINGS_URL}/v2/sleep",
        status=200,
        body=load_fixture("sleep_no_datafields.json"),
    )
    response = await authenticated_client.get_sleep(
        datetime.fromtimestamp(0, tz=timezone.utc),
        datetime.fromtimestamp(1609559200, tz=timezone.utc),
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/sleep",
        METH_POST,
        headers=HEADERS,
        data={"action": "get", "startdate": 0, "enddate": 1609559200},
    )


async def test_get_sleep_summary_in_period(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving sleep."""
    responses.post(
        f"{WITHINGS_URL}/v2/sleep",
        status=200,
        body=load_fixture("sleep_summary.json"),
    )
    response = await authenticated_client.get_sleep_summary_in_period(
        start_date=datetime.fromtimestamp(0, tz=timezone.utc).date(),
        end_date=datetime.fromtimestamp(1609559200, tz=timezone.utc).date(),
        sleep_summary_data_fields=[
            SleepSummaryDataFields.REM_SLEEP_PHASE_COUNT,
            SleepSummaryDataFields.SLEEP_EFFICIENCY,
            SleepSummaryDataFields.SLEEP_LATENCY,
            SleepSummaryDataFields.TOTAL_SLEEP_TIME,
            SleepSummaryDataFields.TOTAL_TIME_IN_BED,
            SleepSummaryDataFields.WAKE_UP_LATENCY,
            SleepSummaryDataFields.TIME_AWAKE_DURING_SLEEP,
            SleepSummaryDataFields.APNEA_HYPOPNEA_INDEX,
            SleepSummaryDataFields.BREATHING_DISTURBANCES_INTENSITY,
            SleepSummaryDataFields.EXTERNAL_TOTAL_SLEEP_TIME,
            SleepSummaryDataFields.DEEP_SLEEP_DURATION,
            SleepSummaryDataFields.AVERAGE_HEART_RATE,
            SleepSummaryDataFields.MIN_HEART_RATE,
            SleepSummaryDataFields.MAX_HEART_RATE,
            SleepSummaryDataFields.LIGHT_SLEEP_DURATION,
            SleepSummaryDataFields.ACTIVE_MOVEMENT_DURATION,
            SleepSummaryDataFields.AVERAGE_MOVEMENT_SCORE,
            SleepSummaryDataFields.NIGHT_EVENTS,
            SleepSummaryDataFields.OUT_OF_BED_COUNT,
            SleepSummaryDataFields.REM_SLEEP_DURATION,
            SleepSummaryDataFields.AVERAGE_RESPIRATION_RATE,
            SleepSummaryDataFields.MIN_RESPIRATION_RATE,
            SleepSummaryDataFields.MAX_RESPIRATION_RATE,
            SleepSummaryDataFields.SLEEP_SCORE,
            SleepSummaryDataFields.SNORING,
            SleepSummaryDataFields.SNORING_COUNT,
            SleepSummaryDataFields.WAKE_UP_COUNT,
            SleepSummaryDataFields.TOTAL_TIME_AWAKE,
            SleepSummaryDataFields.WITHINGS_INDEX,
        ],
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/sleep",
        METH_POST,
        headers=HEADERS,
        data={
            "action": "getsummary",
            "startdateymd": "1970-01-01",
            "enddateymd": "2021-01-02",
            "data_fields": "nb_rem_episodes,sleep_efficiency,sleep_latency,"
            "total_sleep_time,total_timeinbed,wakeup_latency,waso,"
            "apnea_hypopnea_index,breathing_disturbances_intensity,asleepduration,"
            "deepsleepduration,hr_average,hr_min,hr_max,lightsleepduration,"
            "mvt_active_duration,mvt_score_avg,night_events,out_of_bed_count,"
            "remsleepduration,rr_average,rr_min,rr_max,sleep_score,snoring,"
            "snoringepisodecount,wakeupcount,wakeupduration,withings_index",
        },
    )


async def test_get_sleep_summary_in_period_without_data_fields(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving sleep without datafields."""
    responses.post(
        f"{WITHINGS_URL}/v2/sleep",
        status=200,
        body=load_fixture("sleep_summary_no_datafields.json"),
    )
    response = await authenticated_client.get_sleep_summary_in_period(
        start_date=datetime.fromtimestamp(0, tz=timezone.utc).date(),
        end_date=datetime.fromtimestamp(1609559200, tz=timezone.utc).date(),
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/sleep",
        METH_POST,
        headers=HEADERS,
        data={
            "action": "getsummary",
            "startdateymd": "1970-01-01",
            "enddateymd": "2021-01-02",
        },
    )


async def test_get_sleep_summary_since(
    responses: aioresponses,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving sleep."""
    responses.post(
        f"{WITHINGS_URL}/v2/sleep",
        status=200,
        body=load_fixture("sleep_summary.json"),
    )
    response = await authenticated_client.get_sleep_summary_since(
        sleep_summary_since=datetime.fromtimestamp(0, tz=timezone.utc),
        sleep_summary_data_fields=[
            SleepSummaryDataFields.REM_SLEEP_PHASE_COUNT,
            SleepSummaryDataFields.SLEEP_EFFICIENCY,
            SleepSummaryDataFields.SLEEP_LATENCY,
            SleepSummaryDataFields.TOTAL_SLEEP_TIME,
            SleepSummaryDataFields.TOTAL_TIME_IN_BED,
            SleepSummaryDataFields.WAKE_UP_LATENCY,
            SleepSummaryDataFields.TIME_AWAKE_DURING_SLEEP,
            SleepSummaryDataFields.APNEA_HYPOPNEA_INDEX,
            SleepSummaryDataFields.BREATHING_DISTURBANCES_INTENSITY,
            SleepSummaryDataFields.EXTERNAL_TOTAL_SLEEP_TIME,
            SleepSummaryDataFields.DEEP_SLEEP_DURATION,
            SleepSummaryDataFields.AVERAGE_HEART_RATE,
            SleepSummaryDataFields.MIN_HEART_RATE,
            SleepSummaryDataFields.MAX_HEART_RATE,
            SleepSummaryDataFields.LIGHT_SLEEP_DURATION,
            SleepSummaryDataFields.ACTIVE_MOVEMENT_DURATION,
            SleepSummaryDataFields.AVERAGE_MOVEMENT_SCORE,
            SleepSummaryDataFields.NIGHT_EVENTS,
            SleepSummaryDataFields.OUT_OF_BED_COUNT,
            SleepSummaryDataFields.REM_SLEEP_DURATION,
            SleepSummaryDataFields.AVERAGE_RESPIRATION_RATE,
            SleepSummaryDataFields.MIN_RESPIRATION_RATE,
            SleepSummaryDataFields.MAX_RESPIRATION_RATE,
            SleepSummaryDataFields.SLEEP_SCORE,
            SleepSummaryDataFields.SNORING,
            SleepSummaryDataFields.SNORING_COUNT,
            SleepSummaryDataFields.WAKE_UP_COUNT,
            SleepSummaryDataFields.TOTAL_TIME_AWAKE,
            SleepSummaryDataFields.WITHINGS_INDEX,
        ],
    )
    assert len(response) == 300
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/sleep",
        METH_POST,
        headers=HEADERS,
        data={
            "action": "getsummary",
            "lastupdate": 0,
            "data_fields": "nb_rem_episodes,sleep_efficiency,sleep_latency,"
            "total_sleep_time,total_timeinbed,wakeup_latency,waso,"
            "apnea_hypopnea_index,breathing_disturbances_intensity,asleepduration,"
            "deepsleepduration,hr_average,hr_min,hr_max,lightsleepduration,"
            "mvt_active_duration,mvt_score_avg,night_events,out_of_bed_count,"
            "remsleepduration,rr_average,rr_min,rr_max,sleep_score,snoring,"
            "snoringepisodecount,wakeupcount,wakeupduration,withings_index",
        },
    )


async def test_get_sleep_summary_since_without_data_fields(
    responses: aioresponses,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving sleep without datafields."""
    responses.post(
        f"{WITHINGS_URL}/v2/sleep",
        status=200,
        body=load_fixture("sleep_summary_no_datafields.json"),
    )
    response = await authenticated_client.get_sleep_summary_since(
        datetime.fromtimestamp(0, tz=timezone.utc),
    )
    assert len(response) == 300
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/sleep",
        METH_POST,
        headers=HEADERS,
        data={
            "action": "getsummary",
            "lastupdate": 0,
        },
    )


async def test_get_workouts_since(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving workouts."""
    responses.post(
        f"{WITHINGS_URL}/v2/measure",
        status=200,
        body=load_fixture("workouts.json"),
    )
    response = await authenticated_client.get_workouts_since(
        datetime.fromtimestamp(0, tz=timezone.utc),
        workout_data_fields=[WorkoutDataFields.CALORIES],
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/measure",
        METH_POST,
        headers=HEADERS,
        data={"action": "getworkouts", "lastupdate": 0, "data_fields": "calories"},
    )


async def test_get_workouts_period(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: WithingsClient,
) -> None:
    """Test retrieving workouts."""
    responses.post(
        f"{WITHINGS_URL}/v2/measure",
        status=200,
        body=load_fixture("workouts.json"),
    )
    response = await authenticated_client.get_workouts_in_period(
        start_date=datetime.fromtimestamp(0, tz=timezone.utc),
        end_date=datetime.fromtimestamp(1609559200, tz=timezone.utc),
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{WITHINGS_URL}/v2/measure",
        METH_POST,
        headers=HEADERS,
        data={
            "action": "getworkouts",
            "startdateymd": "1970-01-01 00:00:00+00:00",
            "enddateymd": "2021-01-02 03:46:40+00:00",
        },
    )
