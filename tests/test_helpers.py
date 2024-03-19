"""Asynchronous Python client for Withings."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from airgradient import MeasurementGroup, SleepSummary, aggregate_measurements
from airgradient.helpers import aggregate_sleep_summary

from . import load_fixture

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion


def test_aggregate_measurements(snapshot: SnapshotAssertion) -> None:
    """Test aggregation."""
    json_file: list[dict[str, Any]] = json.loads(load_fixture("measurement_list.json"))

    measurements = [MeasurementGroup.from_api(measurement) for measurement in json_file]

    assert aggregate_measurements(measurements) == snapshot


def test_aggregate_sleep_summary(snapshot: SnapshotAssertion) -> None:
    """Test aggregation."""
    json_file: list[dict[str, Any]] = json.loads(load_fixture("sleep_summary.json"))[
        "body"
    ]["series"]

    sleep_summaries = [
        SleepSummary.from_api(sleep_summary) for sleep_summary in json_file
    ]

    assert aggregate_sleep_summary(sleep_summaries) == snapshot


def test_aggregate_single_sleep_summary(snapshot: SnapshotAssertion) -> None:
    """Test aggregation."""
    json_file: dict[str, Any] = json.loads(load_fixture("sleep_summary.json"))["body"][
        "series"
    ][0]

    sleep_summary = SleepSummary.from_api(json_file)

    assert aggregate_sleep_summary([sleep_summary]) == snapshot


def test_aggregate_no_sleep_summary(snapshot: SnapshotAssertion) -> None:
    """Test aggregation."""
    assert aggregate_sleep_summary([]) == snapshot
