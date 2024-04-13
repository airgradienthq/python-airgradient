"""Models for AirGradient."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class Measures(DataClassORJSONMixin):
    """Measures model."""

    signal_strength: int = field(metadata=field_options(alias="wifi"))
    serial_number: str = field(metadata=field_options(alias="serialno"))
    boot_time: int = field(metadata=field_options(alias="boot"))
    firmware_version: str = field(metadata=field_options(alias="firmwareVersion"))
    model: str = field(metadata=field_options(alias="fwMode"))
    rco2: int | None = None
    pm01: int | None = None
    pm02: int | None = None
    pm10: int | None = None
    total_volatile_organic_component_index: int | None = field(
        default=None, metadata=field_options(alias="tvocIndex")
    )
    raw_total_volatile_organic_component: int | None = field(
        default=None, metadata=field_options(alias="tvoc_raw")
    )
    pm003_count: int | None = field(
        default=None, metadata=field_options(alias="pm003Count")
    )
    nitrogen_index: int | None = field(
        default=None, metadata=field_options(alias="noxIndex")
    )
    raw_nitrogen: int | None = field(
        default=None, metadata=field_options(alias="nox_raw")
    )
    ambient_temperature: float | None = field(
        default=None, metadata=field_options(alias="atmp")
    )
    relative_humidity: float | None = field(
        default=None, metadata=field_options(alias="rhum")
    )


class PmStandard(StrEnum):
    """PM standard model."""

    UGM3 = "ugm3"
    USAQI = "usaqi"


class TemperatureUnit(StrEnum):
    """Temperature unit model."""

    CELSIUS = "c"
    FAHRENHEIT = "f"


class ConfigurationControl(StrEnum):
    """Configuration control model."""

    CLOUD = "cloud"
    LOCAL = "local"
    BOTH = "both"


class LedBarMode(StrEnum):
    """LED bar mode."""

    OFF = "off"
    CO2 = "co2"
    PM = "pm"


@dataclass
class Config(DataClassORJSONMixin):
    """Config model."""

    country: str
    pm_standard: PmStandard = field(metadata=field_options(alias="pmStandard"))
    led_bar_mode: LedBarMode = field(metadata=field_options(alias="ledBarMode"))
    co2_automatic_baseline_calibration_days: int = field(
        metadata=field_options(alias="abcDays")
    )
    temperature_unit: TemperatureUnit = field(
        metadata=field_options(alias="temperatureUnit")
    )
    configuration_control: ConfigurationControl = field(
        metadata=field_options(alias="configurationControl")
    )
    post_data_to_airgradient: bool = field(
        metadata=field_options(alias="postDataToAirGradient")
    )
