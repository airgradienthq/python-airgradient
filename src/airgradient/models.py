"""Models for AirGradient."""

from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class Measures(DataClassORJSONMixin):
    """Measures model."""

    signal_strength: int = field(metadata=field_options(alias="wifi"))
    serial_number: str = field(metadata=field_options(alias="serialno"))
    boot_time: int = field(metadata=field_options(alias="boot"))
    firmware_version: str = field(metadata=field_options(alias="firmwareVersion"))
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
